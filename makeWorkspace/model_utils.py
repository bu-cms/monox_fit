import ROOT  # type:ignore
from typing import Any
from counting_experiment import Category, Channel
from utils.generic.logger import initialize_colorized_logger
from utils.workspace.uncertainties import get_veto_unc, get_jes_variations_names, get_id_variations_names

logger = initialize_colorized_logger(log_level="INFO")


def define_model(
    category_id: str,
    category_name: str,
    input_file: ROOT.TFile,
    output_file: ROOT.TFile,
    output_workspace: ROOT.RooWorkspace,
    diagonalizer: Any,
    year: str,
    variable: str,
    convention: str,
    model_name: str,
    target_name: str,
    samples_map: dict[str, str],
    channel_names: dict[str, str],
    veto_channel_list: list[str],
    trigger_channel_list: dict[str],
    jes_jer_channel_list: list[str],
    region_names: dict[str, str],
    do_monojet_theory: bool = False,
):
    """
    Defines a statistical model for a given category using transfer factors.

    This function constructs a model by:
    - Fetching input histograms for the target and control samples.
    - Computing transfer factors (ratios of target to control samples).
    - Creating `Channel` objects for each transfer factor.
    - Applying systematic uncertainties such as veto nuisances, JES/JER variations, and theory uncertainties.
    - Adding bin-by-bin statistical uncertainties.
    - Storing results in an output ROOT file and workspace.
    - Returning a `Category` object encapsulating the model details.

    Args:
        category_id (str): Unique identifier for the category.
        category_name (str): Name of the category.
        input_file (ROOT.TFile): Input ROOT file containing histograms.
        output_file (ROOT.TFile): Output ROOT file to store results.
        output_workspace (ROOT.RooWorkspace): Output workspace for the statistical model.
        diagonalizer (Any): Object for diagonalizing correlations.
        year (str): Data-taking year.
        convention (str): Naming convention for systematic uncertainties.
        model_name (str): Name of the model.
        target_name (str): Name of the target MC sample in the input ROOT file.
        samples_map (dict[str, str]): Mapping of control MC sample names to their ROOT file entries.
        channel_names (dict[str, str]): Mapping of transfer factor labels to channel names.
        veto_channel_list (list[str]): Channels where veto uncertainties are applied.
        trigger_channel_list (dict[str]): Channels where trigger uncertainties are applied and corresponding trigger name.
        veto_dict (dict[str, float]): Dictionary of veto nuisance values.
        jes_jer_channel_list (list[str]): Channels where JES/JER uncertainties are applied.
        region_names (dict[str, str]): Mapping of transfer factor labels to region names.

    Returns:
        Category: A `Category` object encapsulating the defined model.
    """

    # Some setup
    input_tdir = input_file.Get(f"category_{category_id}")
    input_wspace = input_tdir.Get(f"wspace_{category_id}")
    common_syst_folder = f"inputs/sys/{variable}/{category_id}"

    # Defining the nominal transfer factors
    # Nominal MC process to model
    target = input_tdir.Get(target_name)
    # Control MC samples
    control_samples = fetch_control_samples(input_tdir=input_tdir, samples_map=samples_map)

    # Compute and save a copy of the transfer factors (target divided by control)
    transfer_factors = define_transfer_factors(
        control_samples=control_samples,
        category_id=category_id,
        target_sample=target,
        output_file=output_file,
    )

    # Create a `Channel` object for each transfer factor
    CRs = define_channels(
        transfer_factors=transfer_factors,
        category_id=category_id,
        input_wspace=input_wspace,
        output_workspace=output_workspace,
        convention=convention,
        channel_names=channel_names,
        model_name=model_name,
    )

    add_veto_nuisances(
        transfer_factors=transfer_factors,
        channel_objects=CRs,
        channel_list=veto_channel_list,
        model_name=model_name,
        category_id=category_id,
        output_file=output_file,
        syst_folder=common_syst_folder,
        year=year,
    )
    add_trigger_nuisances(
        transfer_factors=transfer_factors,
        channel_objects=CRs,
        channel_list=trigger_channel_list,
        category_id=category_id,
        output_file=output_file,
        syst_folder=common_syst_folder,
        year=year,
    )

    add_id_nuisances(
        transfer_factors=transfer_factors,
        channel_objects=CRs,
        channel_list=samples_map.keys(),
        year=year,
        category_id=category_id,
        output_file=output_file,
        syst_folder=common_syst_folder,
        model_name=model_name,
    )

    add_jes_jer_uncertainties(
        transfer_factors=transfer_factors,
        channel_objects=CRs,
        channel_list=jes_jer_channel_list,
        year=year,
        category_id=category_id,
        output_file=output_file,
        model_name=model_name,
        syst_folder=common_syst_folder,
    )

    if do_monojet_theory:
        add_monojet_theory_uncertainties(
            transfer_factors=transfer_factors,
            channel_objects=CRs,
            category_id=category_id,
            output_file=output_file,
            syst_folder=common_syst_folder,
            model_name=model_name,
        )

    # Add Bin by bin nuisances to cover statistical uncertainties
    do_stat_unc(transfer_factors=transfer_factors, channel_objects=CRs, region_names=region_names, category_id=category_id, output_file=output_file)

    # Extract the bin edges of the distribution
    bin_edges = [target.GetBinLowEdge(b + 1) for b in range(target.GetNbinsX() + 1)]

    # Create and return `Category` object
    return Category(
        corrname=model_name,
        catid=category_id,
        cname=category_name,
        _fin=input_tdir,
        _fout=output_file,
        _wspace=input_wspace,
        _wspace_out=output_workspace,
        _bins=bin_edges,
        _varname=variable,
        _target_datasetname=target.GetName(),
        _control_regions=list(CRs.values()),
        diag=diagonalizer,
        convention=convention,
    )


def fetch_control_samples(
    input_tdir: ROOT.TDirectoryFile,
    samples_map: dict[str, str],
) -> dict[str : ROOT.TH1]:
    """
    Fetch all needed control MC samples used by the model.

    Args:
        input_tdir (ROOT.TDirectoryFile): Directory where samples are stored
        samples_map (dict[str, str]): Dictionnary mapping the name of the region / transfer factor to the name of the MC sample in the directory.
    """

    return {region_name: input_tdir.Get(sample_name) for region_name, sample_name in samples_map.items()}


def define_transfer_factors(
    control_samples: dict[str : ROOT.TH1],
    category_id: str,
    target_sample: ROOT.TH1,
    output_file: ROOT.TFile,
) -> dict[str : ROOT.TH1]:
    """
    Compute the transfer factors for each MC sample.

    Args:
        control_samples (dict[str, ROOT.TH1]): Dictionary mapping transfer factors labels to their control MC sample.
        category_id (str): Unique identifier for the category.
        target_sample (Any): Histogram of the target process.
        output_file (ROOT.TFile): Output ROOT file for a copy of the transfer factors.
    """
    transfer_factors = {}
    for label, sample in control_samples.items():
        factor = target_sample.Clone(f"{label}_weights_{category_id}")
        factor.Divide(sample)
        # transfer_factors[label] = factor
        transfer_factors.update({label: factor})
        output_file.WriteTObject(factor)
    return transfer_factors


def define_channels(
    transfer_factors: dict[str, ROOT.TH1],
    category_id: str,
    model_name: str,
    input_wspace: ROOT.RooWorkspace,
    output_workspace: ROOT.RooWorkspace,
    convention: str,
    channel_names: dict[str, str],
) -> dict[str, Channel]:
    """
    Stores transfer factors in Channel objects.

    Args:
        transfer_factors (dict[str, ROOT.TH1]): Dictionary mapping transfer factors labels to their distributions.
        category_id (str): Unique identifier for the category.
        model_name (str): Unique identifier for the model.
        input_wspace (ROOT.RooWorkspace): The input ROOT workspace containing the model parameters.
        output_workspace (ROOT.RooWorkspace): The output ROOT workspace used for importing variables and functions.
        convention (str): A string defining the naming convention used for systematic uncertainties ("IC" or "BU").
        channel_names (dict[str, str]): Dictionary mapping transfer factors labels to the name of their channels.
    """
    return {
        sample: Channel(
            cname=channel_names[sample],
            wspace=input_wspace,
            wspace_out=output_workspace,
            catid=category_id + "_" + model_name,
            scalefactors=transfer_factor,
            convention=convention,
        )
        for sample, transfer_factor in transfer_factors.items()
    }


def add_veto_nuisances(
    transfer_factors: dict[str, Any],
    channel_objects: dict[str, Channel],
    channel_list: list[str],
    model_name: str,
    category_id: str,
    output_file: ROOT.TFile,
    syst_folder: str,
    year: str,
) -> None:
    """Adds veto systematic uncertainties to the specified control regions.

    Args:
        channel_objects (dict[str, Channel]): Dictionary mapping control region names to `Channel` objects.
        channel_list (list[str]): List of control regions to apply veto uncertainties.
        veto_dict (dict[str, float]): Dictionnary mapping the name of the nuissance to add and its value.
    """
    lep_map = {"e": "electron", "m": "muon", "t": "tau"}
    analysis = category_id.replace(f"_{year}", "")
    for key, veto_value in get_veto_unc(model=model_name, analysis=analysis).items():
        lep = lep_map[key]
        veto_name = f"CMS_veto_{key}_{year}"
        is_shape = veto_value == "shape"
        if is_shape:
            unc_file_name = f"{syst_folder}/systematics_{lep}_veto.root"
        for channel in channel_list:
            if is_shape:
                hist_basename = f"{model_name}_over_{channel}_{lep}_veto"
                add_shape_nuisances(
                    transfer_factors=transfer_factors,
                    channel_objects=channel_objects,
                    category_id=category_id,
                    output_file=output_file,
                    sample=channel,
                    param_name=veto_name,
                    unc_file_name=unc_file_name,
                    hist_basename=hist_basename,
                )
            else:
                channel_objects[channel].add_nuisance(veto_name, veto_value)


def get_weight_name(sample: str, category_id: str, param_name: str, direction: str) -> str:
    return f"{sample}_weights_{category_id}_{param_name}_{direction}"


def add_shape_nuisances(
    transfer_factors: dict[str, Any],
    channel_objects: dict[str, Channel],
    category_id: str,
    output_file: ROOT.TFile,
    sample: str,
    param_name: str,
    unc_file_name: str,
    hist_basename: str,
    functype: str = "quadratic",
) -> None:
    """Adds shape systematic uncertainties to the specified control regions.

    Args:
        transfer_factors (dict[str, ROOT.TH1]): Dictionary mapping transfer factors labels to their distributions.
        channel_objects (dict[str, Channel]): Dictionary of `Channel` objects.
        category_id (str): Unique identifier for the category.
        output_file (ROOT.TFile): Output ROOT file for storing variations.
        sample: (str): Name of sample to which the systematic should be applied to.
        param_name: (str): Name of the nuisance parameter to add to the model.
        unc_file_name: (str): Name of the root file where the systematic uncertainties are stored.
        hist_basename: (str): Name of the histogram to load that contains the relative systematic uncertainty.
    """
    unc_file = ROOT.TFile(unc_file_name)
    for direction in ["Up", "Down"]:
        # Scale transfer factor by relative variation and write to output file
        unc_name = f"{hist_basename}{direction}"
        new_name = get_weight_name(sample=sample, category_id=category_id, param_name=param_name, direction=direction)
        add_variation(nominal=transfer_factors[sample], unc_file=unc_file, unc_name=unc_name, new_name=new_name, outfile=output_file)
    # Add function (quadratic) to model the nuisance
    channel_objects[sample].add_nuisance_shape(name=param_name, file=output_file, functype=functype)
    unc_file.Close()


def add_trigger_nuisances(
    transfer_factors: dict[str, Any],
    channel_objects: dict[str, Channel],
    channel_list: list[str],
    category_id: str,
    output_file: ROOT.TFile,
    syst_folder: str,
    year: str,
) -> None:
    """Adds trigger systematic uncertainties to the specified control regions."""
    hist_basename = "met_trigger_sys"
    param_name = f"{hist_basename}_{year}"
    unc_file_name = f"{syst_folder}/systematics_trigger_met_muondep.root"
    for sample in channel_list:
        add_shape_nuisances(
            transfer_factors=transfer_factors,
            channel_objects=channel_objects,
            category_id=category_id,
            output_file=output_file,
            sample=sample,
            param_name=param_name,
            unc_file_name=unc_file_name,
            hist_basename=hist_basename,
        )


def add_id_nuisances(
    transfer_factors: dict[str, Any],
    channel_objects: dict[str, Channel],
    channel_list: list[str],
    year: str,
    category_id: str,
    output_file: ROOT.TFile,
    syst_folder: str,
    model_name: str,
) -> None:
    """Adds lepton id systematic uncertainties to the specified control regions."""
    id_variations = get_id_variations_names(year=year)
    unc_file_name = f"{syst_folder}/systematics_id_shapes.root"
    for var in id_variations:
        param_name = var
        for sample in channel_list:
            hist_basename = f"{model_name}_over_{sample}_{param_name}"
            add_shape_nuisances(
                transfer_factors=transfer_factors,
                channel_objects=channel_objects,
                category_id=category_id,
                output_file=output_file,
                sample=sample,
                param_name=param_name,
                unc_file_name=unc_file_name,
                hist_basename=hist_basename,
            )


def add_jes_jer_uncertainties(
    transfer_factors: dict[str, Any],
    channel_objects: dict[str, Channel],
    channel_list: list[str],
    year: str,
    category_id: str,
    output_file: ROOT.TFile,
    model_name: str,
    syst_folder: str,
) -> None:
    """Adds JES and JER uncertainties to transfer factors."""
    jet_variations = get_jes_variations_names(year=year)
    for sample in channel_list:
        for var in jet_variations:
            param_name = var
            unc_file_name = f"{syst_folder}/systematics_{param_name}.root"
            hist_basename = f"{model_name}_over_{sample}_{param_name}"
            add_shape_nuisances(
                transfer_factors=transfer_factors,
                channel_objects=channel_objects,
                category_id=category_id,
                output_file=output_file,
                sample=sample,
                param_name=param_name,
                unc_file_name=unc_file_name,
                hist_basename=hist_basename,
            )


def add_monojet_theory_uncertainties(
    transfer_factors: dict[str, ROOT.TH1],
    channel_objects: dict[str, Channel],
    category_id: str,
    output_file: ROOT.TFile,
    syst_folder: str,
    model_name: str,
) -> None:
    """Adds theoretical uncertainties to transfer factors for monojet/monov Z model."""

    channel = "monojet" if "monojet" in category_id else "monov"

    if "zjets" in model_name:
        unc_file_name = f"{syst_folder}/systematics_vjets_theory.root"
        # TODO: change the naming convention
        photon_variations = [
            ("d1k", "theory_qcd"),
            ("d2k", "theory_qcdshape"),
            ("d3k", "theory_qcdprocess"),
            ("d1kappa", "theory_ewk"),
            ("d2kappa_g", "theory_nnlomissG"),
            ("d2kappa_z", "theory_nnlomissZ"),
            ("d3kappa_g", "theory_sudakovG"),
            ("d3kappa_z", "theory_sudakovZ"),
            ("mix", "theory_cross"),
        ]
        w_variations = [
            ("d1k", "theory_wqcd"),
            ("d2k", "theory_wqcdshape"),
            ("d3k", "theory_wqcdprocess"),
            ("d1kappa", "theory_wewk"),
            ("d2kappa_w", "theory_nnlomissW"),
            ("d2kappa_z", "theory_nnlomissZ"),
            ("d3kappa_w", "theory_sudakovW"),
            ("d3kappa_z", "theory_sudakovZ"),
            ("mix", "theory_wcross"),
        ]
        theory_config = [
            ("qcd_photon", "z_over_g", photon_variations),
            ("qcd_w", "z_over_w", w_variations),
        ]
        for sample, ratio_label, variations in theory_config:
            for var in variations:
                param_name = var[1]
                hist_basename = f"{channel}_{ratio_label}_{var[0]}"
                add_shape_nuisances(
                    transfer_factors=transfer_factors,
                    channel_objects=channel_objects,
                    category_id=category_id,
                    output_file=output_file,
                    sample=sample,
                    param_name=param_name,
                    unc_file_name=unc_file_name,
                    hist_basename=hist_basename,
                )

    pdf_file_name = f"{syst_folder}/systematics_pdf_ratios.root"

    pdf_config = {
        "qcd_zjets": [
            ("qcd_photon", "z_over_g_pdf"),
            ("qcd_zmm", "z_over_z_pdf"),
            ("qcd_zee", "z_over_z_pdf"),
            ("qcd_w", "z_over_w_pdf"),
        ],
        "qcd_wjets": [
            ("qcd_wen", "w_over_w_pdf"),
            ("qcd_wmn", "w_over_w_pdf"),
        ],
    }[model_name]

    for sample, hist_basename in pdf_config:
        add_shape_nuisances(
            transfer_factors=transfer_factors,
            channel_objects=channel_objects,
            category_id=category_id,
            output_file=output_file,
            sample=sample,
            param_name=hist_basename,
            unc_file_name=pdf_file_name,
            hist_basename=hist_basename,
        )


def do_stat_unc(
    transfer_factors: dict[str, ROOT.TH1],
    channel_objects: dict[str, Channel],
    region_names: dict[str, str],
    category_id: str,
    output_file: ROOT.TFile,
) -> None:
    """Add stat. unc. variations to the workspace"""

    for sample, histogram in transfer_factors.items():
        # Add one variation per bin
        region = region_names[sample]
        for b in range(1, histogram.GetNbinsX() + 1):
            err = histogram.GetBinError(b)
            content = histogram.GetBinContent(b)
            # Safety
            # if (content <= 0) or (err / content < 0.001):
            if content <= 0:
                logger.critical(f"Undefined behaviour for {histogram.GetName()} in bin {b}: content = {content}, error = {err}.", exception_cls=ValueError)

            # Careful: The bin count "b" in this loop starts at 1. In the combine model, we want it to start from 0!
            param_name = f"{category_id}_stat_error_{region}_bin{b-1}"
            up = histogram.Clone(get_weight_name(sample=sample, category_id=category_id, param_name=param_name, direction="Up"))
            down = histogram.Clone(get_weight_name(sample=sample, category_id=category_id, param_name=param_name, direction="Down"))
            up.SetBinContent(b, content + err)
            down.SetBinContent(b, content - err)
            output_file.WriteTObject(up)
            output_file.WriteTObject(down)

            logger.debug(f"Adding statistical variation with absolute error = {err:.4f}, relative error = {err / content:.4f}: {up.GetName()}")
            channel_objects[sample].add_nuisance_shape(name=param_name, file=output_file, functype="lognorm")


def add_variation(nominal: ROOT.TH1, unc_file: ROOT.TFile, unc_name: str, new_name: str, outfile: ROOT.TFile) -> None:
    factor = unc_file.Get(unc_name)
    variation = nominal.Clone(new_name)
    if factor.GetNbinsX() == 1:
        factor_value = factor.GetBinContent(1)
        variation.Scale(factor_value)
    else:
        assert variation.Multiply(factor)
        variation.Multiply(factor)
    outfile.WriteTObject(variation)
