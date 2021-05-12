#!/usr/bin/env python

import os
import ROOT as r
from HiggsAnalysis.CombinedLimit.ModelTools import *
r.gSystem.Load("libHiggsAnalysisCombinedLimit")

pjoin = os.path.join

def main():
    dummy = []
    # File containing the HF estimate shapes for 2017 and 2018
    inputfile = 'sys/vbf_hf_estimate.root'
    f = r.TFile(inputfile, 'READ')
    f.cd()

    for year in [2017, 2018]:
        h = f.Get('qcd_estimate_mjj_{}'.format(year))
        
        outpath = pjoin('output/vbf_hf_estimate_ws_{}.root'.format(year))
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
        
        # Write the histogram and the workspace to the output file
        h.SetDirectory(0)
        subd.cd()
        subd.WriteTObject(h)
        ws.Write()
        outf.Close()

        dummy.append(ws)

    return dummy

if __name__ == '__main__':
    a = main()