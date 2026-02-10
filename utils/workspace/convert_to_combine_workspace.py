import ROOT  # type: ignore
from typing import Any
from utils.generic.logger import initialize_colorized_logger
from utils.workspace.generic import safe_import

ROOT.gSystem.Load("libHiggsAnalysisCombinedLimit")
logger = initialize_colorized_logger("INFO")


def convert_to_combine_workspace(
    wsin_combine: ROOT.RooWorkspace,
    f_simple_hists: ROOT.TFile,
    category: str,
    cmb_categories: list[Any],
    controlregions_def: list[str],
    variable: str,
    rename_variable: str = "",
) -> None:
    """Converts histograms into RooDataHists and RooParametricHist models and adds them to the RooWorkspace.

    Args:
        wsin_combine (ROOT.RooWorkspace): Target workspace to import objects into.
        f_simple_hists (ROOT.TFile): File containing category histograms and workspaces.
        categories (list[str]): List of analysis categories (e.g., ['vbf_2017']).
        cmb_categories (list[Any]): Combined categories with control region info.
        controlregions_def (list[str]): List of CR Python modules to import.
        rename_variable (str): Optional renaming of the observable variable.
    """
    wsin_combine.loadSnapshot("PRE_EXT_FIT_Clean")

    cat = category
    fdir = f_simple_hists.Get(f"category_{cat}")
    wlocal = fdir.Get(f"wspace_{cat}")

    # Identify observable variable and template histogram
    # Initialize samplehist with the first histogram we find in the directory, then break out of the loop
    # samplehist is only passed to initialized the shape of the RooParametricHist
    samplehist = None
    for key in fdir.GetListOfKeys():
        obj = key.ReadObj()
        if isinstance(obj, (ROOT.TH1D, ROOT.TH1F)):
            samplehist = obj
            break

    if not samplehist:
        logger.critical(f"No valid histogram found for category {cat}.", exception_cls=RuntimeError)

    nbins = samplehist.GetNbinsX()

    # Fetch the variable, rename it to vbf_{year}_{variable}
    logger.debug(f"x-axis label:{variable}. Hist name: {samplehist.GetName()}")
    varl = wlocal.var(variable)
    rename_variable = rename_variable or f"{variable}_{cat}"
    varl.SetName(rename_variable)
    logger.info(f"Renaming: {varl.GetName()} -> {rename_variable}")

    # Loop other all the histograms in the directory for the year convert them to RooDataHist and save them to the workspace
    for key in fdir.GetListOfKeys():
        obj = key.ReadObj()
        logger.debug(f"{obj.GetName()}, {obj.GetTitle()}, {type(obj)}")
        if not isinstance(obj, (ROOT.TH1D, ROOT.TH1F)):
            continue
        if obj.Integral() <= 0:
            obj.SetBinContent(1, 1e-4)
        name = obj.GetName()
        logger.debug(f"Importing histogram {name} for category {cat}")
        dhist = ROOT.RooDataHist(f"{cat}_{name}", f"DataSet - {cat}, {name}", ROOT.RooArgList(varl), obj)
        safe_import(workspace=wsin_combine, obj=dhist)

    # Add in the V-jets backgrounds MODELS
    # Loop over all models (`Category` objects) and all their "control regions" (`Channel` objects)
    # to fetch the expected number of events (parametrized by QCD Znunu in SR and nuisances) for all process
    # and store them as RooParametricHist in the workspace
    for crn in controlregions_def:
        cr_def = __import__(crn)

        if "qcd_zjets" == cr_def.model:
            # Parametric model expectations
            # This part is to extract the process that is used to parametrize all the others, that is QCD Znunu in SR
            # First, we fetch the expected number of events in every bin, then convert them to a RooParametricHist and save it to the workspace
            expectations = ROOT.RooArgList()
            for b in range(nbins):
                var = wsin_combine.var(f"model_mu_cat_{cat}_{cr_def.model}_bin_{b}")
                expectations.add(var)

            phist = ROOT.RooParametricHist(
                f"{cat}_signal_{cr_def.model}_model", f"Model Shape for {cr_def.model} in Category {cat}", varl, expectations, samplehist
            )
            norm = ROOT.RooAddition(f"{phist.GetName()}_norm", f"Total number of expected events in {phist.GetName()}", expectations)
            safe_import(workspace=wsin_combine, obj=phist)
            safe_import(workspace=wsin_combine, obj=norm)

        # Add control region models
        # This part is to extract all other processes parametrized by QCD Znunu in SR,
        # convert and save them to RooParametricHist in the workspace
        for cn in cmb_categories:
            logger.debug(f"CHECK {cn.catid} {cn.cname}")
            # TODO: we are already looping through every model,
            # is this loop really needed? We are continuing
            # if we don't match the imported model anyway
            if cn.catid != f"{cat}_{cr_def.model}" or cn.cname != crn:
                continue

            # Loop over all process in the category
            for cr in cn.ret_control_regions():
                cr_expectations = ROOT.RooArgList()
                # Fetch the expected number of events for the process for every bin, paramertized by QCD Znunu in SR and nuisances
                for b in range(nbins):
                    binstr = f"bin{b + 1}" if "MTR" in rename_variable else f"bin_{b}"
                    func = wsin_combine.function(f"pmu_cat_{cat}_{cr_def.model}_ch_{cr.chid}_{binstr}")
                    cr_expectations.add(func)

                model_name = f"{cat}_{cr.crname}_{cr_def.model}_model"
                logger.info(f"Building CR model: {model_name}")
                # cr_expectations.Print()
                # Convert the distribution to RooParametricHist, save to the workspace
                cr_phist = ROOT.RooParametricHist(
                    model_name,
                    f"Expected Shape for {cr.crname} in control region in Category {cat}",
                    varl,
                    cr_expectations,
                    samplehist,
                )
                cr_norm = ROOT.RooAddition(f"{cr_phist.GetName()}_norm", "Total number of expected events in {cr_phist.GetName()}", cr_expectations)
                safe_import(workspace=wsin_combine, obj=cr_phist)
                safe_import(workspace=wsin_combine, obj=cr_norm)

    # Log external nuisance parameters
    # This is the part that prints what parameters should added at the end of the datacard
    # (e.g. the statistical uncertainty for each bin of each process)
    allparams = ROOT.RooArgList(wsin_combine.allVars())
    for i in range(allparams.getSize()):
        par = allparams.at(i)
        if not par.getAttribute("NuisanceParameter_EXTERNAL"):
            continue
        if par.getAttribute("BACKGROUND_NUISANCE"):
            continue  # these aren't in fact used for combine
        logger.debug(f"External nuisance parameter: {par.GetName()} param {par.getVal():.1f} 1.0")
