#!/usr/bin/env python3

import os
import re
import argparse
import ROOT  # type: ignore
from HiggsAnalysis.CombinedLimit.ModelTools import SafeWorkspaceImporter  # type: ignore

from utils.generic.logger import initialize_colorized_logger
from utils.workspace.model import get_year_from_category, get_control_region_models
from utils.workspace.generic import safe_import
from utils.workspace.convert_to_combine_workspace import convert_to_combine_workspace

logger = initialize_colorized_logger(log_level="INFO")

# Setup ROOT and external C++ dependencies
ROOT.gSystem.AddIncludePath("-I$CMSSW_BASE/src/")
ROOT.gSystem.AddIncludePath("-I$ROOFITSYS/include")
ROOT.gSystem.Load("libRooFit.so")
ROOT.gSystem.Load("libRooFitCore.so")
ROOT.gROOT.SetBatch(True)
# ROOT.gSystem.SetBuildDir("/tmp/ROOT_build", True)
ROOT.gROOT.ProcessLine(".L makeWorkspace/diagonalizer.cc+")
from ROOT import diagonalizer  # type: ignore


def parse_args() -> argparse.Namespace:
    """Parse and validate command-line arguments."""
    parser = argparse.ArgumentParser(description="Construct fit model from RooWorkspace.")
    parser.add_argument("--input_filename", type=str, required=True, help="Input file containing histograms and workspace.")
    parser.add_argument("--output_filename", type=str, default="combined_model.root", help="Path to the output ROOT file.")
    parser.add_argument("--category", type=str, required=True, help="Analysis category, e.g., 'vbf_2017'.")
    parser.add_argument("--variable", type=str, required=True, help="Variable name")
    parser.add_argument("--rename", type=str, default="", help="Optional new name for the observable variable.")

    args = parser.parse_args()

    args.input_filename = os.path.abspath(args.input_filename)
    args.output_filename = os.path.abspath(args.output_filename)

    if not os.path.isfile(args.input_filename):
        logger.critical(f"Input file not found: {args.input_filename}", exception_cls=IOError)
    if not args.input_filename.endswith(".root"):
        logger.critical(f"Input file must be a ROOT file: {args.input_filename}", exception_cls=IOError)

    return args


def generate_combine_model(
    input_filename: str,
    output_filename: str,
    category: str,
    variable: str,
    rename: str = "",
) -> None:
    """Generate a Combine RooWorkspace with control region models."""
    model_list = get_control_region_models(category=category)

    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    input_file = ROOT.TFile.Open(input_filename)
    output_file = ROOT.TFile(output_filename, "RECREATE")

    workspace = ROOT.RooWorkspace("combinedws")
    workspace._safe_import = SafeWorkspaceImporter(workspace)

    logger.info("Creating global observables")
    sample_type = ROOT.RooCategory("bin_number", "Bin Number")
    observed = ROOT.RooRealVar("observed", "Observed Events bin", 1)
    safe_import(workspace=workspace, obj=sample_type)  # Global variables for dataset
    safe_import(workspace=workspace, obj=observed)

    # Loop over control region definitions, and load their model definitions
    diag = diagonalizer(workspace)
    cmb_categories = []
    year = get_year_from_category(category=category)
    for model_name in model_list:
        module = __import__(model_name)
        cr_dir = output_file.mkdir(f"{model_name}_category_{category}")
        # The `cmodel` function is where models are created. This function does two things:
        # 1) Compute transfer factors
        #   Processes are express different processes as a ratio with of QCD Znunu in SR
        #   For the qcd_zjets model, this is directly the ratio of the two processes
        #   For other models, processes are first taken as a ratio with either EWK Znunu, QCD Wjets and EWK Wjets,
        #   but these are later expressed as transfer factors to make QCD Znunu appear at the `init_channels` step
        # 2) Add nuisances and add them to the workspace
        #   for veto, JES/JER, theory and statistical uncertainties
        #   for each transfer factor in the model
        convention = "IC" if "MTR" in rename else "BU"
        logger.info(f"Creating model for {model_name}")
        model = module.cmodel(
            category_id=category,
            category_name=model_name,
            input_file=input_file,
            output_file=cr_dir,
            output_workspace=workspace,
            diagonalizer=diag,
            year=year,
            variable=variable,
            convention=convention,
        )
        cmb_categories.append(model)
        logger.info(f"Initializing model channels for model: {model.cname}, cat: {model.catid}")
        # This is where the actual model distributions as a function of QCD Znunu in SR are made for all processes.
        # Processes modelled with `qcd_zjets` are expressed as:
        #   (process yield) * [transfer factor = (QCD Znunu in SR) / (process yield)] * Product of all nuisances
        # Processes using the other models will first fetch the above model, before multiplying the transfer factor and nuisances
        # For instance, EWK Zll in the diMuon region, modelled with `ewk_zjets` will fetch
        #   (EWK Znunu in SR) * [transfer factor = (QCD Znunu in SR) / (EWK Znunu in SR)] * Product of all nuisances (for EWK Znunu in SR)
        # and multiply by
        #   [transfer factor = (EWK Znunu in SR) / (EWK Zll in diMuon)] * Product of all nuisances (for EWK Zll in diMuon)
        # These models are made for each bin of the given variable distribution and saved to the workspace
        model.init_channels()

    # Save pre-fit snapshot
    workspace.saveSnapshot("PRE_EXT_FIT_Clean", workspace.allVars())

    # Convert workspace to Combine workspace format
    # This actually builds the histograms used in the fit
    # It fetches the modelled distribution for every bin of every process computed at the above `init_channels` step
    # and stores them as the `RooParametricHist` that will be used in the datacard
    convert_to_combine_workspace(
        wsin_combine=workspace,
        f_simple_hists=input_file,
        category=category,
        cmb_categories=cmb_categories,
        controlregions_def=model_list,
        variable=variable,
        rename_variable=rename,
    )

    output_file.WriteTObject(workspace)
    logger.info(f"--> Produced constraints model in Combine workspace: {output_file.GetName()}")


def main() -> None:
    """Main entry point for the script."""
    args = parse_args()
    generate_combine_model(
        input_filename=args.input_filename,
        output_filename=args.output_filename,
        category=args.category,
        variable=args.variable,
        rename=args.rename,
    )


if __name__ == "__main__":
    main()
