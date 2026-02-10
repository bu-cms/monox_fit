#!/bin/env python
import os
import sys

sys.path.append(os.path.abspath("../../../plotter"))
from plot_PreFitPostFit import plotPreFitPostFit
from plot_datavalidation import dataValidation
from plot_ratio import plot_ratio
from plot_diffnuis import plot_nuis

lumi = {
    2017: 41.5,
    2018: 59.7,
}
regions = ["singlemuon", "dimuon", "gjets", "singleelectron", "dielectron"]
procs = ["zmm", "zee", "w_weights", "photon", "wen", "wmn"]


def monov_plot_channels_separately():
    ### Years fit separately
    for year in [2017, 2018]:
        for wp in "loose", "tight":
            model_file = f"root/combined_model_monov_nominal_{wp}.root"
            ws_file = f"root/ws_monov_nominal_{wp}.root"
            category = f"monov{wp}_{year}"
            fitdiag_file = f"diagnostics/fitDiagnostics_nominal_{category}.root"
            diffnuis_file = f"diagnostics/diffnuisances_nominal_{category}.root"

            outdir = f"./plots/{wp}_{year}/"
            for region in regions:
                plotPreFitPostFit(region, category, ws_file, fitdiag_file, outdir, lumi[year], year)
            for proc in procs:
                plot_ratio(proc, category, model_file, outdir, lumi[year], year)

            # Flavor integrated
            dataValidation("combined", "gjets", category, ws_file, fitdiag_file, outdir, lumi[year], year)
            dataValidation("combinedW", "gjets", category, ws_file, fitdiag_file, outdir, lumi[year], year)
            dataValidation("combined", "combinedW", category, ws_file, fitdiag_file, outdir, lumi[year], year)
            # Split by flavor
            dataValidation("dimuon", "singlemuon", category, ws_file, fitdiag_file, outdir, lumi[year], year)
            dataValidation("dielectron", "singleelectron", category, ws_file, fitdiag_file, outdir, lumi[year], year)
            dataValidation("singleelectron", "gjets", category, ws_file, fitdiag_file, outdir, lumi[year], year)
            dataValidation("singlemuon", "gjets", category, ws_file, fitdiag_file, outdir, lumi[year], year)
            dataValidation("dielectron", "gjets", category, ws_file, fitdiag_file, outdir, lumi[year], year)
            dataValidation("dimuon", "gjets", category, ws_file, fitdiag_file, outdir, lumi[year], year)
            # plot_nuis(diffnuis_file, outdir)


def monov_plot_agreement_channels_combined_years_combined():
    ### Channels combined, years combined
    fitdiag_file = "diagnostics/fitDiagnostics_nominal_monov_combined.root"
    for wp in "loose", "tight":
        ### Years fit together
        ws_file = f"root/ws_monov_nominal_{wp}.root"
        model_file = f"root/combined_model_monov_nominal_{wp}.root"

        for year in [2017, 2018]:
            outdir = f"./plots/combined_combined_{year}/"
            category = f"monov{wp}_{year}"
            for region in regions:
                plotPreFitPostFit(region, category, ws_file, fitdiag_file, outdir, lumi[year], year)
            for proc in procs:
                plot_ratio(proc, category, model_file, outdir, lumi[year], year)
        outdir = "./plots/combined/"


def monov_plot_nuisance_channels_combined():
    #### Channels combined
    # Nuisances
    for year in [2017, 2018, "combined"]:
        outdir = f"./plots/combined_{year}/"
        diffnuis_file = f"diagnostics/diffnuisances_nominal_monov_{year}.root"
        plot_nuis(diffnuis_file, outdir)


def monov_plot_agreement_channels_combined_years_separately():
    # Years separately: prefit / postfit
    for year in 2017, 2018:
        fitdiag_file = f"diagnostics/fitDiagnostics_nominal_monov_{year}.root"
        outdir = f"./plots/combined_{year}/"
        for wp in "loose", "tight":
            model_file = f"root/combined_model_monov_nominal_{wp}.root"
            ws_file = f"root/ws_monov_nominal_{wp}.root"
            category = f"monov{wp}_{year}"
            filler = {"wp": "WP", "year": year, "category": category}

            for region in regions:
                plotPreFitPostFit(region, category, ws_file, fitdiag_file, outdir, lumi[year], year)
            for proc in procs:
                plot_ratio(proc, category, model_file, outdir, lumi[year], year)


monov_plot_nuisance_channels_combined()
monov_plot_channels_separately()
monov_plot_agreement_channels_combined_years_separately()
monov_plot_agreement_channels_combined_years_combined()
