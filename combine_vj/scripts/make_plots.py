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
procs = ['zmm','zee','w_weights','photon','wen','wmn']

for year in [2017,2018]:
    ws_file = "root/ws_monojet.root"
    fitdiag_file = 'diagnostics_bkp/fitDiagnostics_monojet_monov_{year}.root'.format(year=year)
    diffnuis_file = 'diagnostics_bkp/diffnuisances_monojet_monov_combined_{year}.root'.format(year=year)
    category='monojet_{year}'.format(year=year)
    outdir = './plots/{year}/'.format(year=year)
    for region in regions:
        plotPreFitPostFit(region,     category,ws_file, fitdiag_file, outdir, lumi[year], year)


    for proc in procs:
        plot_ratio(proc, category, 'root/combined_model_monojet.root'.format(year=year), outdir, lumi[year],year)

    # Flavor integrated
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

    plot_nuis(diffnuis_file, outdir)

    outdir = './plots/{year}_unblind/'.format(year=year)
    for region in regions:
        fitdiag_file = 'diagnostics_bkp/fitDiagnostics_unblind_monojet_monov_{year}.root'.format(year=year)
        plotPreFitPostFit(region,     category,ws_file, fitdiag_file, outdir, lumi[year], year)

    diffnuis_file = 'diagnostics_bkp/diffnuisances_unblind__monojet_monov_combined_{year}.root'.format(year=year)
    plot_nuis(diffnuis_file, outdir)


    for wp in ['tight','loose']:
        ws_file="root/ws_monov_nominal_{WP}.root".format(WP=wp)
        model_file = "root/combined_model_monov_nominal_{WP}.root".format(WP=wp)
        category='monov{WP}_{YEAR}'.format(WP=wp,YEAR=year)
        outdir = './plots/{year}/'.format(year=year)

        filler = {
            "year" : year,
            "category" : category,
            "WP" : wp,
        }
        fitdiag_file = 'diagnostics_bkp/fitDiagnostics_monojet_monov_{year}.root'.format(**filler)

        for region in regions:
            plotPreFitPostFit(region,     category,ws_file, fitdiag_file, outdir, lumi[year], year)
        for proc in procs:
            plot_ratio(proc, category, 'root/combined_model_monov_nominal_{WP}.root'.format(year=year,WP=wp), outdir, lumi[year],year)


        # Flavor integrated
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

        outdir = './plots/{year}_unblind/'.format(year=year)
        fitdiag_file = 'diagnostics_bkp/fitDiagnostics_unblind_monojet_monov_{year}.root'.format(**filler)
        for region in regions:
            plotPreFitPostFit(region,     category,ws_file, fitdiag_file, outdir, lumi[year], year)

### Years fit together
outdir="plots/combined"
diffnuis_file = 'diagnostics_bkp/diffnuisances_monojet_monov_combined_combined.root'
plot_nuis(diffnuis_file, outdir)

ws_file = "root/ws_monojet.root"
for year in [2017,2018]:
    fitdiag_file = 'diagnostics_bkp/fitDiagnostics_monojet_monov_combined.root'
    category='monojet_{year}'.format(year=year)
    outdir = './plots/combined_{year}/'.format(year=year)
    for region in regions:
        plotPreFitPostFit(region,     category,ws_file, fitdiag_file, outdir, lumi[year], year)

    fitdiag_file = 'diagnostics_bkp/fitDiagnostics_unblind_monojet_monov_combined.root'.format(year=year)
    outdir = './plots/combined_{year}_unblind/'.format(year=year)
    for region in regions:
        plotPreFitPostFit(region,     category,ws_file, fitdiag_file, outdir, lumi[year], year)

for wp in ['tight','loose']:
    ws_file="root/ws_monov_nominal_{WP}.root".format(WP=wp)
    model_file = "root/combined_model_monov_nominal_{WP}.root".format(WP=wp)
    for year in [2017,2018]:
        category='monov{WP}_{YEAR}'.format(WP=wp,YEAR=year)
        filler = {
            "year" : year,
            "category" : category
        }

        fitdiag_file = 'diagnostics_bkp/fitDiagnostics_monojet_monov_combined.root'
        outdir = './plots/{year}/'.format(**filler)
        for region in regions:
            plotPreFitPostFit(region,     category,ws_file, fitdiag_file, outdir, lumi[year], year)

        outdir = './plots/{year}_unblind/'.format(**filler)
        fitdiag_file = 'diagnostics_bkp/fitDiagnostics_unblind_monojet_monov_combined.root'.format(**filler)
        for region in regions:
            plotPreFitPostFit(region,     category,ws_file, fitdiag_file, outdir, lumi[year], year)
