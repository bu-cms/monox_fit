import ROOT
ROOT.gSystem.Load("libHiggsAnalysisCombinedLimit")
from HiggsAnalysis.CombinedLimit.ModelTools import *

cat  = "vbf"
fin = ROOT.TFile("vbf_limit_2017.root","READ")
#'/afs/cern.ch/work/a/aalbert/public/share/2019-10-16_legacylimit/legacy_limit_2017.root','READ')
fdir = fin.Get("category_"+cat)

fout = ROOT.TFile('mono-x.root','RECREATE')
foutdir = fout.mkdir("category_"+cat)

wsin_combine = ROOT.RooWorkspace("wspace_"+cat,"wspace_"+cat)
wsin_combine._import = SafeWorkspaceImporter(wsin_combine)#getattr(wsin_combine,"import")
 
samplehistos = fdir.GetListOfKeys()
for s in samplehistos: 
  obj = s.ReadObj()
  samplehist = obj
  break
nbins = samplehist.GetNbinsX()

varl = ROOT.RooRealVar('mjj','mjj',0,100000);

# Keys in the fdir 
keys_local = fdir.GetListOfKeys() 
for key in keys_local: 
  obj = key.ReadObj()
  print obj.GetName(), obj.GetTitle(), type(obj)
  if type(obj)!=type(ROOT.TH1D()): continue
  title = obj.GetTitle()
  name = obj.GetName()
  if not obj.Integral() > 0 : obj.SetBinContent(1,0.0001) # otherwise Combine will complain!
  print "Creating Data Hist for ", name 
  dhist = ROOT.RooDataHist("%s"%(name),"DataSet - %s, %s"%(cat,name),ROOT.RooArgList(varl),obj)
  wsin_combine._import(dhist)
  
  obj.SetDirectory(0)
  foutdir.cd()
  foutdir.WriteTObject(obj)

foutdir.cd()
foutdir.WriteTObject(wsin_combine)
foutdir.Write()
fout.Write()
#wsin_combine.writeToFile("mono-x.root")

