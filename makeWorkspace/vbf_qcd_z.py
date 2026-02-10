import ROOT  # type:ignore
from counting_experiment import Category
from model_utils import *

model = "qcd_zjets"


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
    Constructs a category model for QCD Z+jets processes using control regions and transfer factors.

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
        "target_name": "signal_qcdzjets",  # Name of the target sample in the input ROOT file.
        "samples_map": {  # Mapping of control sample names to their ROOT file entries.
            "qcd_zmm": "Zmm_qcdzll",
            "qcd_zee": "Zee_qcdzll",
            "qcd_w": "signal_qcdwjets",
            "ewkqcd": "signal_ewkzjets",  # TODO
            "qcd_photon": "gjets_qcdgjets",
        },
        "channel_names": {  # Mapping of transfer factor labels to channel names.
            "qcd_zmm": "qcd_dimuon",
            "qcd_zee": "qcd_dielectron",
            "qcd_w": "qcd_wjetssignal",
            "ewkqcd": "ewkqcd_signal",
            "qcd_photon": "qcd_photon",
        },
        "veto_channel_list": ["qcd_w"],  # Channels where veto uncertainties are applied.
        "trigger_channel_list": ["qcd_zmm"],  # Channels where trigger uncertainties are applied.
        "jes_jer_channel_list": ["qcd_zmm", "qcd_zee", "qcd_w", "qcd_photon"],  # Channels where JES/JER uncertainties are applied.
        "region_names": {  # Mapping of transfer factor labels to region names.
            "qcd_zmm": "qcd_dimuonCR",
            "qcd_zee": "qcd_dielectronCR",
            "qcd_w": "qcd_wzCR",
            "qcd_photon": "qcd_photonCR",
            "ewkqcd": "ewkqcdzCR",
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

    return cat
