import ROOT  # type:ignore
from counting_experiment import Category
from model_utils import *

model = "ewk_wjets"


def cmodel(
    category_id: str,
    category_name: str,
    input_file: ROOT.TFile,
    output_file: ROOT.TFile,
    output_workspace: ROOT.RooWorkspace,
    diagonalizer,
    year: str,
    variable: str,
    convention: str = "BU",
) -> Category:
    """
    Constructs a category model for EWK W+jets processes using control regions and transfer factors.

    This function:
    - Reads histograms from the input ROOT file.
    - Computes transfer factors by dividing the target signal by control regions.
    - Applies systematic uncertainties (JES/JER, theory, and veto nuisances).
    - Adds bin-by-bin statistical uncertainties.
    - Creates and returns a `Category` object.

    Args:
        category_id (str): Unique identifier for the category.
        category_name (str): Human-readable name for the category.
        input_file (ROOT.TFile): Input ROOT file containing relevant histograms.
        output_file (ROOT.TFile): Output ROOT file for storing processed histograms.
        output_workspace (ROOT.RooWorkspace): Output workspace for RooFit objects.
        diagonalizer: Diagonalizer to pass to `Category`
        year (str): Data-taking year.
        convention (str, optional): Naming convention for transfer factors. Defaults to "BU".

    Returns:
        Category: A `Category` object encapsulating the modeled process.
    """

    model_args = {
        "model_name": model,
        "target_name": "signal_ewkwjets",  # Name of the target sample in the input ROOT file.
        "samples_map": {  # Mapping of control sample names to their ROOT file entries.
            "ewk_wmn": "Wmn_ewkwjets",
            "ewk_wen": "Wen_ewkwjets",
        },
        "channel_names": {  # Mapping of transfer factor labels to channel names.
            "ewk_wmn": "ewk_singlemuon",
            "ewk_wen": "ewk_singleelectron",
        },
        "veto_channel_list": ["ewk_wmn", "ewk_wen"],  # Channels where veto uncertainties are applied.
        "trigger_channel_list": ["ewk_wmn"],  # Channels where trigger uncertainties are applied.
        "jes_jer_channel_list": ["ewk_wmn", "ewk_wen"],  # Channels where JES/JER uncertainties are applied.
        "region_names": {  # Mapping of transfer factor labels to region names.
            "ewk_wmn": "ewk_singlemuon",
            "ewk_wen": "ewk_singleelectron",
        },
    }

    cat = define_model(
        # arguments of `cmodel`
        category_id=category_id,
        category_name=category_name,
        input_file=input_file,
        output_file=output_file,
        output_workspace=output_workspace,
        diagonalizer=diagonalizer,
        year=year,
        variable=variable,
        convention=convention,
        # model-specific arguments
        **model_args,
    )

    # Specify this is dependant on EWK (Z->nunu / W->lnu) in SR from corresponding channel in vbf_ewk_z
    cat.setDependant("ewk_zjets", "ewk_wjetssignal")
    return cat
