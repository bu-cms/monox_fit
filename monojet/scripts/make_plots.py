#!/bin/env python3
import os
import sys
sys.path.append(os.path.abspath("../../../plotter"))
from plot_PreFitPostFit import plotPreFitPostFit
from plot_datavalidation import dataValidation
from plot_ratio import plot_ratio
from plot_diffnuis import plot_nuis
lumi ={
    2017 : 8,
    2018: 59.7
}
regions = ['singlemuon','dimuon','gjets','singleelectron','dielectron','signal']
procs = ['zmm','zee','w_weights','photon','wen','wmn']

### Years fit separately
for year in [2017]:
    ws_file = "root/ws_monojet.root".format(year=year)
    #for tag in ["","_unblind"]:
    for tag in [""]:
        fitdiag_file = 'diagnostics/fitDiagnostics_monojet{tag}_{year}.root'.format(year=year,tag=tag)
        diffnuis_file = 'diagnostics/diffnuisances_monojet{tag}_{year}.root'.format(year=year,tag=tag)
        category='monojet_{year}'.format(year=year)
        outdir = './plots/{year}{tag}/'.format(year=year,tag=tag)
        for region in regions:
            plotPreFitPostFit(region,     category,ws_file, fitdiag_file, outdir, lumi[year], year)
        for proc in procs:
             plot_ratio(proc, category, 'root/combined_model_monojet.root'.format(year=year), outdir, lumi[year],year)

        # Flavor integrated
        dataValidation("combined",  "gjets",    category, ws_file, fitdiag_file, outdir,lumi[year],year)
        dataValidation("combinedW", "gjets",    category, ws_file, fitdiag_file, outdir,lumi[year],year)
        dataValidation("combined",  "combinedW",category, ws_file, fitdiag_file, outdir,lumi[year],year)
        # # Split by flavor
        dataValidation("dimuon",        "singlemuon",    category, ws_file, fitdiag_file, outdir,lumi[year],year)
        dataValidation("dielectron",    "singleelectron",category, ws_file, fitdiag_file, outdir,lumi[year],year)
        dataValidation("singleelectron","gjets",         category, ws_file, fitdiag_file, outdir,lumi[year],year)
        dataValidation("singlemuon",    "gjets",         category, ws_file, fitdiag_file, outdir,lumi[year],year)
        dataValidation("dielectron",    "gjets",         category, ws_file, fitdiag_file, outdir,lumi[year],year)
        dataValidation("dimuon",        "gjets",         category, ws_file, fitdiag_file, outdir,lumi[year],year)


        # plot_nuis(diffnuis_file, outdir)


### Years fit together
#for tag in ["","_unblind"]:
for tag in [""]:
    outdir="plots/combined{tag}".format(tag=tag)
    diffnuis_file = 'diagnostics/diffnuisances_monojet{tag}_combined.root'.format(tag=tag)
    plot_nuis(diffnuis_file, outdir)

    for year in [2017]:
        ws_file = "root/ws_monojet.root".format(year=year)
        fitdiag_file = 'diagnostics/fitDiagnostics_monojet{tag}_combined.root'.format(year=year,tag=tag)
        category='monojet_{year}'.format(year=year)
        outdir = './plots/combined_{year}{tag}/'.format(year=year,tag=tag)
        for region in regions:
            plotPreFitPostFit(region,     category,ws_file, fitdiag_file, outdir, lumi[year], year)
