#!/usr/bin/env python
# from counting_experiment import SafeWorkspaceImporter
from convert import *
import argparse
import os
from HiggsAnalysis.CombinedLimit.ModelTools import *

import ROOT as r

# Silent mode for ROOFit
r.RooMsgService.instance().setStreamStatus(1,False)
r.RooMsgService.instance().setSilentMode(True)

ROOT.gSystem.AddIncludePath("-I$CMSSW_BASE/src/ ");
ROOT.gSystem.AddIncludePath("-I$ROOFITSYS/include");

ROOT.gSystem.Load("libRooFit.so")
ROOT.gSystem.Load("libRooFitCore.so")

r.gROOT.SetBatch(1)
r.gROOT.ProcessLine(".L diagonalizer.cc+")
from ROOT import diagonalizer

pjoin = os.path.join

def cli_args():
    parser = argparse.ArgumentParser(prog='Construct fit model from RooWorkspace.')
    parser.add_argument('file', type=str, help='Input file to use.')
    parser.add_argument('--out', type=str, help='Path to save output under.', default='combined_model.root')
    parser.add_argument('--categories', type=str, default=None, help='Analysis categories')
    parser.add_argument('--rename', type=str, default="", help='New name for analysis variable to pass to convertToCombineWorkspace')
    args = parser.parse_args()

    args.file = os.path.abspath(args.file)
    args.out = os.path.abspath(args.out)
    if not os.path.exists(args.file):
      raise IOError("Input file not found: " + args.file)
    if not args.file.endswith('.root'):
      raise IOError("Input file is not a ROOT file: " + args.file)
    if not args.categories:
      raise IOError("Please specify the --category option.")

    args.categories = args.categories.split(',')
    return args

def main():
    # Commandline arguments
    args = cli_args()

    # Automatically determine CR settings from categories
    if any(re.match('mono(jet|v).*',x) for x in args.categories):
        controlregions_def = ["Z_constraints","W_constraints"]
    elif any(['vbf' in x for x in args.categories]):
         controlregions_def = ["Z_constraints_qcd_withphoton","W_constraints_qcd","Z_constraints_ewk_withphoton","W_constraints_ewk"]

    # Determine year from name
    bname = os.path.basename(args.file)

    # Create output path
    outdir = os.path.dirname(args.out)
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    _fOut   = r.TFile(args.out,"RECREATE")
    _f      = r.TFile.Open(args.file)
    out_ws  = r.RooWorkspace("combinedws")

    #out_ws._import = getattr(out_ws,"import")
    out_ws._import = SafeWorkspaceImporter(out_ws)

    sampleType  = r.RooCategory("bin_number","Bin Number");
    obs         = r.RooRealVar("observed","Observed Events bin",1)
    out_ws._import(sampleType)  # Global variables for dataset
    out_ws._import(obs)
    diag_combined = diagonalizer(out_ws)
    obsargset   = r.RooArgSet(out_ws.var("observed"),out_ws.cat("bin_number"))


    # Loop over control region definitions, and load their model definitions
    cmb_categories = []
    for crd,crn in enumerate(controlregions_def):
        x = __import__(crn)
        for cid,cn in enumerate(args.categories):

            # Derive year name
            m = re.match(".*201(7|8).*",cn)
            if not m or (m and len(m.groups())> 1):
                raise RuntimeError("Cannot derive year from category name: " + cn)
            year = int("201" + m.groups()[0])

            _fDir = _fOut.mkdir("%s_category_%s"%(crn,cn))

            if "MTR" in args.rename:
                cmb_categories.append(x.cmodel(cn,crn,_f,_fDir,out_ws,diag_combined, year, convention="IC"))
            else:
                cmb_categories.append(x.cmodel(cn,crn,_f,_fDir,out_ws,diag_combined, year))

    for cid,cn in enumerate(cmb_categories):
        print "Run Model: cid, cn", cid,cn
        cn.init_channels()
        channels = cn.ret_channels()

    # Save a Pre-fit snapshot
    out_ws.saveSnapshot("PRE_EXT_FIT_Clean",out_ws.allVars())
    # Now convert workspace to combine friendly workspace
    convertToCombineWorkspace(out_ws,_f,args.categories,cmb_categories,controlregions_def, args.rename)
    _fOut.WriteTObject(out_ws)

    print "Produced constraints model in --> ", _fOut.GetName()

if __name__ == "__main__":
    main()