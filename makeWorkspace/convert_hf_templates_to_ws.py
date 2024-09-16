#!/usr/bin/env python

import os
import re
import ROOT as r
from HiggsAnalysis.CombinedLimit.ModelTools import *
r.gSystem.Load("libHiggsAnalysisCombinedLimit")

pjoin = os.path.join

def convert_hftemplate_to_ws(inputfile, inputhistname, outpath, year):
    f = r.TFile(inputfile, 'READ')
    f.cd()

    h = f.Get(inputhistname)
    # Create the output ROOT file
    outf = r.TFile(outpath, 'RECREATE')
    subd = outf.mkdir('category_vbf_{}'.format(year))

    ws = r.RooWorkspace('wspace_vbf_{}'.format(year))
    ws._import = SafeWorkspaceImporter(ws)

    variable_name = 'mjj_vbf_{}'.format(year)

    varl = r.RooRealVar(variable_name, variable_name, 0,100000)
    
    name = 'qcd_estimate_mjj_{}'.format(year)
    dhist = r.RooDataHist(
        name,
        "DataSet - vbf_%s, %s" % (year,name),
        r.RooArgList(varl),
        h
    )

    ws._import(dhist)
    
    h.SetDirectory(0)
    subd.cd()
    subd.WriteTObject(h)
    ws.Write()
    outf.Close()

    return ws

def main():
    dummy = []
    # File containing the HF estimate shapes for 2017 and 2018
    inputfile = 'sys/vbf_hf_estimate.root'

    for year in [2017, 2018]:
        outpath = pjoin('output/vbf_hf_estimate_ws_{}.root'.format(year))

        ws = convert_hftemplate_to_ws(
            inputfile,
            inputhistname='qcd_estimate_mjj_{}'.format(year),
            outpath=outpath,
            year=year
        )
        dummy.append(ws)

    return dummy

if __name__ == '__main__':
    a = main()