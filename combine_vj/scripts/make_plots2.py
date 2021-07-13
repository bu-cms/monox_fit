#!/bin/env python
import os
import sys
sys.path.append(os.path.abspath("../../../plotter"))
from plot_PreFitPostFit import plotPreFitPostFit
from plot_datavalidation import dataValidation
from plot_ratio import plot_ratio
from plot_diffnuis import plot_nuis
lumi ={
    2017 : 41.5,
    2018: 59.7
}
regions = ['singlemuon','dimuon','gjets','singleelectron','dielectron','signal']
# regions = ['signal']
procs = ['zmm','zee','w_weights','photon','wen','wmn']


def nuisance_plots():
    outdir="plots/combined"
    # diffnuis_file = 'diagnostics/diffnuisances_monojet_monov_combined_combined.root'
    diffnuis_file = 'diagnostics_bkp/diffnuisances_monojet_monov_combined_combined.root'
    plot_nuis(diffnuis_file, outdir)

    outdir="plots/combined_unblind"
    diffnuis_file = 'diagnostics_condor_3/diffnuisances_monojet_monov_combined_combined_unblind.root'
    plot_nuis(diffnuis_file, outdir)

def data_validation_plots():
    for year in [2017,2018]:
        category     = 'monojet_{year}'.format(year=year)

        fitdiag_file = 'diagnostics_bkp/fitDiagnostics_monojet_monov_combined.root'
        outdir       = './plots/{year}/'.format(year=year)

        # Monojet
        ws_file      = "root/ws_monojet.root"
        category = "monojet_{YEAR}".format(YEAR=year)
        dataValidation("combined",  "gjets",    category, ws_file, fitdiag_file, outdir,lumi[year],year)
        dataValidation("combinedW", "gjets",    category, ws_file, fitdiag_file, outdir,lumi[year],year)
        dataValidation("combined",  "combinedW",category, ws_file, fitdiag_file, outdir,lumi[year],year)
        
        # Split by flavor
        dataValidation("dimuon",        "singlemuon",    category, ws_file, fitdiag_file, outdir,lumi[year],year)
        dataValidation("dielectron",    "singleelectron",category, ws_file, fitdiag_file, outdir,lumi[year],year)
        dataValidation("singleelectron","gjets",         category, ws_file, fitdiag_file, outdir,lumi[year],year)
        dataValidation("singlemuon",    "gjets",         category, ws_file, fitdiag_file, outdir,lumi[year],year)
        dataValidation("dielectron",    "gjets",         category, ws_file, fitdiag_file, outdir,lumi[year],year)
        dataValidation("dimuon",        "gjets",         category, ws_file, fitdiag_file, outdir,lumi[year],year)

        # Mono-V
        for wp in ['tight','loose']:
            ws_file  = "root/ws_monov_nominal_{WP}.root".format(WP=wp)
            category = 'monov{WP}_{YEAR}'.format(WP=wp,YEAR=year)
            dataValidation("combined",  "gjets",    category, ws_file, fitdiag_file, outdir,lumi[year],year)
            dataValidation("combinedW", "gjets",    category, ws_file, fitdiag_file, outdir,lumi[year],year)
            dataValidation("combined",  "combinedW",category, ws_file, fitdiag_file, outdir,lumi[year],year)


def postfit_plots():
    for year in [2017,2018]:
        # CR-only
        fitdiag_file = 'diagnostics_bkp/fitDiagnostics_monojet_monov_combined.root'
        outdir       = './plots/combined_{year}/'.format(year=year)

        # Monojet
        ws_file      = "root/ws_monojet.root"
        category = "monojet_{YEAR}".format(YEAR=year)
        for region in regions:
            plotPreFitPostFit(region,     category,ws_file, fitdiag_file, outdir, lumi[year], year)

        # Mono-V
        for wp in ['tight','loose']:
            ws_file  = "root/ws_monov_nominal_{WP}.root".format(WP=wp)
            category = 'monov{WP}_{YEAR}'.format(WP=wp,YEAR=year)
            for region in regions:
                plotPreFitPostFit(region,category,ws_file, fitdiag_file, outdir, lumi[year], year)

        # CR+SR
        fitdiag_file = 'diagnostics_condor_3/fitDiagnostics_monojet_monov_combined_unblind.root'
        outdir       = './plots/combined_unblind_{year}/'.format(year=year)

        # Monojet
        ws_file  = "root/ws_monojet.root"
        category = "monojet_{YEAR}".format(YEAR=year)
        for region in regions:
            for fit in "fit_b", "fit_s":
                plotPreFitPostFit(region,     category,ws_file, fitdiag_file, outdir, lumi[year], year, sb=(fit=='fit_s'), fit=fit)

        # Mono-V
        for wp in ['tight','loose']:
            ws_file  = "root/ws_monov_nominal_{WP}.root".format(WP=wp)
            category = 'monov{WP}_{YEAR}'.format(WP=wp,YEAR=year)
            for region in regions:
                for fit in "fit_b", "fit_s":
                    plotPreFitPostFit(region,category,ws_file, fitdiag_file, outdir, lumi[year], year, sb=(fit=='fit_s'), fit=fit)


# nuisance_plots()
# postfit_plots()
data_validation_plots()