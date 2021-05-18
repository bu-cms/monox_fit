#!/usr/bin/env python

import os
import re
import ROOT as r
from HiggsAnalysis.CombinedLimit.ModelTools import *
r.gSystem.Load("libHiggsAnalysisCombinedLimit")

pjoin = os.path.join

def convert_to_ws(inputfile, inputhistname, outpath, year):
    f = r.TFile(inputfile, 'READ')
    f.cd()

    h = f.Get(inputhistname)
    # Create the output ROOT file
    outf = r.TFile(outpath, 'RECREATE')
    subd = outf.mkdir('category_vbf_{}'.format(year))

    ws = r.RooWorkspace('ws_vbf_{}'.format(year))
    ws._import = SafeWorkspaceImporter(ws)

    variable_name = 'mjj_vbf_{}'.format(year)

    varl = r.RooRealVar(variable_name, variable_name, 0,100000)
    
    name = 'qcd_temp_sr'
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

    inputfiles = [
        'sys/out_MTR_2017.root_qcdDD.root',
        'sys/out_MTR_2018.root_qcdDD.root',
    ]

    for inputfile in inputfiles:
        year = re.findall('201\d', inputfile)[0]
        outpath = pjoin('output/vbf_qcd_nckw_ws_{}.root'.format(year))

        ws = convert_to_ws(
            inputfile,
            inputhistname='rebin_QCD_hist_counts',
            outpath=outpath,
            year=year
        )
        dummy.append(ws)

    return dummy

if __name__ == '__main__':
    a = main()