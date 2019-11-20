#########################################################################################
# Setup the basics ----> USER DEFINED SECTION HERE ------------------------------------//
fOutName = "combined_model.root"  # --> Output file
fName    = "mono-x.root"  # --> input file (i.e output from previous)
categories=["vbf"]
controlregions_def = ["Z_constraints_qcd","W_constraints_qcd","Z_constraints_ewk","W_constraints_ewk"] # --> configuration configs for control region fits. 
#categories = ["monojet","monov"] # --> Should be labeled as in original config 
#controlregions_def = ["Z_constraints","W_constraints"] # --> configuration configs for control region fits. 
# Note if one conrol region def depends on another (i,e if setDependant() is called) it must come AFTER its 
# the one it depends on in this list!
#--------------------------------------------------------------------------------------//
#########################################################################################

# Leave the following alone!
# Headers 
#from combineControlRegions import *
from counting_experiment import *
from convert import * 

from HiggsAnalysis.CombinedLimit.ModelTools import *

import ROOT as r 


ROOT.gSystem.AddIncludePath("-I$CMSSW_BASE/src/ ");
ROOT.gSystem.AddIncludePath("-I$ROOFITSYS/include");
#ROOT.gSystem.AddIncludePath("-I$ROOSYS/include");

ROOT.gSystem.Load("libRooFit.so")
ROOT.gSystem.Load("libRooFitCore.so")

r.gROOT.SetBatch(1)
r.gROOT.ProcessLine(".L diagonalizer.cc+")
from ROOT import diagonalizer

_fOut 	   = r.TFile(fOutName,"RECREATE") 
_f 	   = r.TFile.Open(fName) 
out_ws 	   = r.RooWorkspace("combinedws") 

#out_ws._import = getattr(out_ws,"import")
out_ws._import = SafeWorkspaceImporter(out_ws)

sampleType  = r.RooCategory("bin_number","Bin Number");
obs         = r.RooRealVar("observed","Observed Events bin",1)
out_ws._import(sampleType)  # Global variables for dataset
out_ws._import(obs)
diag_combined = diagonalizer(out_ws)
obsargset   = r.RooArgSet(out_ws.var("observed"),out_ws.cat("bin_number"))

cmb_categories = []

for crd,crn in enumerate(controlregions_def):
	x = __import__(crn)
        for cid,cn in enumerate(categories): 
		_fDir = _fOut.mkdir("%s_category_%s"%(crn,cn))
		cmb_categories.append(x.cmodel(cn,crn,_f,_fDir,out_ws,diag_combined))

for cid,cn in enumerate(cmb_categories):
        print "Run Model: cid, cn", cid,cn
	cn.init_channels()
        channels = cn.ret_channels()

# Save a Pre-fit snapshot
out_ws.saveSnapshot("PRE_EXT_FIT_Clean",out_ws.allVars()) 
# Now convert workspace to combine friendly workspace
#convertToCombineWorkspace(out_ws,_f,categories,cmb_categories,controlregions_def)
convertToCombineWorkspace(out_ws,_f,categories,cmb_categories,controlregions_def,"met_monov")
_fOut.WriteTObject(out_ws)

print "Produced constraints model in --> ", _fOut.GetName()
