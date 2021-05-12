from ROOT import *
from collections import defaultdict
from array import array
from tdrStyle import *
import math
import os
setTDRStyle()

blind = False

new_dic = defaultdict(dict)

def plotPreFitPostFit(region,category,ws_file, fitdiag_file,outdir,lumi,year,sb=False, fit="fit_b"):

  datalab = {"singlemuon":"Wmn", "dimuon":"Zmm", "gjets":"gjets", "signal":"signal", "singleelectron":"Wen", "dielectron":"Zee"}

  f_mlfit = TFile(fitdiag_file,'READ')

  f_data = TFile(ws_file,"READ")

  f_data.cd("category_"+category)
  # if region=="signal":
  #   h_data = f_mlfit.Get("shapes_" + fit + "/"+category+"_signal/total_background")
  #   for i in range(1,h_data.GetNbinsX()+1):
  #     h_data.SetBinContent(i,h_data.GetBinContent(i)*h_data.GetBinWidth(i))
  # else:
  h_data = gDirectory.Get(datalab[region]+"_data")
  filler = {
    "CATEGORY" : category,
    "FIT" : fit
  }
  channel = {"singlemuon":category+"_singlemu", "dimuon":category+"_dimuon", "gjets":category+"_photon", "signal":category+"_signal", "singleelectron":category+"_singleel", "dielectron":category+"_dielec"}

  if "mono" in category:
    mainbkgs = {
                "singlemuon":["wjets"],
                "dimuon": ["zll"],
                "gjets": ["gjets"],
                "signal":["zjets"],
                "singleelectron":["wjets"],
                "dielectron":["zll"]
                }
    processes = [
        'qcd',
        'zll',
        'gjets',
        'top',
        # 'diboson',
        'ewk',
        'ww',
        'wz',
        'zz',
        'wjets',
        'zjets',
        'wgamma',
        'zgamma',
    ]
  else:
    mainbkgs = {
            "singlemuon":["ewk_wjets","qcd_wjets"],
            "dimuon": ["ewk_zll","qcd_zll"],
            "gjets": ["ewk_gjets","qcd_gjets"],
            "signal":["qcd_zjets","ewk_zjets"],
            "singleelectron":["ewk_wjets","qcd_wjets"],
            "dielectron":["ewk_zll","qcd_zll"]
            }
    processes = [
        'qcd',
        'qcd_zll',
        'qcdzll',
        'ewkzll',
        'ewk_zll',
        'ewk_gjets',
        'qcd_gjets',
        'top',
        'diboson',
        'ewk',
        'ewk_wjets',
        'qcd_wjets',
        'qcd_zjets',
        'ewk_zjets'
    ]
  colors = {
    'diboson':"#4897D8",
    'ww':"#4897D8",
    'wz':"#4897D8",
    'zz':"#4897D8",
    'wgamma':"#4897D8",
    'zgamma':"#4897D8",
    'gjets'  :"#9A9EAB",
    'qcd_gjets'  :"#9A9EAB",
    'ewk_gjets'  :"#9A9EAB",
    'qcd'    : "#dedede",
    'top'    :"#CF3721",
    'ewk'    :"#000000",
    'zll'    :"#9A9EAB",
    'qcd_zll'    :"#9A9EAB",
    'qcdzll'    :"#9A9EAB",
    'ewk_zll'    :"#9A9EAB",
    'ewkzll'    :"#9A9EAB",
    'wjets'  :"#FAAF08",
    'qcd_wjets'  :"#feb24c",
    'ewk_wjets'  :"#ffeda0",
    'zjets'  :"#258039",
    'ewk_zjets'  :"#74c476",
    'qcd_zjets'  :"#00441b"
  }

  binLowE = []

  # Pre-Fit
  h_prefit = {}
  h_prefit['total'] = f_mlfit.Get("shapes_prefit/"+channel[region]+"/total")
  for i in range(1,h_prefit['total'].GetNbinsX()+2):
    binLowE.append(h_prefit['total'].GetBinLowEdge(i))

  h_all_prefit = TH1F("h_all_prefit","h_all_prefit",len(binLowE)-1,array('d',binLowE))
  h_other_prefit = TH1F("h_other_prefit","h_other_prefit",len(binLowE)-1,array('d',binLowE))
  h_stack_prefit = THStack("h_stack_prefit","h_stack_prefit")

  # h_all_prefit = f_mlfit.Get("shapes_prefit/"+channel[region]+"/"+"total_background")
  for process in processes:
    h_prefit[process] = f_mlfit.Get("shapes_prefit/"+channel[region]+"/"+process)
    if (not h_prefit[process]): continue
    if (str(h_prefit[process].Integral())=="nan"): continue
    for i in range(1,h_prefit[process].GetNbinsX()+1):
      content = h_prefit[process].GetBinContent(i)
      width = h_prefit[process].GetBinLowEdge(i+1)-h_prefit[process].GetBinLowEdge(i)
      h_prefit[process].SetBinContent(i,content*width)
    h_prefit[process].SetLineColor(TColor.GetColor(colors[process]))
    h_prefit[process].SetFillColor(TColor.GetColor(colors[process]))
    h_all_prefit.Add(h_prefit[process])
    if (not process in mainbkgs[region]):
      h_other_prefit.Add(h_prefit[process])
    h_stack_prefit.Add(h_prefit[process])

  # Post-Fit
  h_postfit = {}
  h_postfit['totalsig'] = f_mlfit.Get("shapes_" + fit + "/"+channel[region]+"/total")
  h_postfit['total'] = f_mlfit.Get("shapes_" + fit + "/"+channel[region]+"/total")
  h_all_postfit = TH1F("h_all_postfit","h_all_postfit",len(binLowE)-1,array('d',binLowE))
  h_other_postfit = TH1F("h_other_postfit","h_other_postfit",len(binLowE)-1,array('d',binLowE))
  h_minor_postfit = TH1F("h_minor_postfit","h_minor_postfit",len(binLowE)-1,array('d',binLowE))

  h_stack_postfit = THStack("h_stack_postfit","h_stack_postfit")
  h_postfit['totalv2'] = f_mlfit.Get("shapes_" + fit + "/"+channel[region]+"/total_background")

  for i in range(1, h_postfit['totalv2'].GetNbinsX()+1):
    error = h_postfit['totalv2'].GetBinError(i)
    content = h_postfit['totalv2'].GetBinContent(i)

  for process in processes:
    h_postfit[process] = f_mlfit.Get("shapes_" + fit + "/"+channel[region]+"/"+process)
    if (not h_postfit[process]): continue
    if (str(h_postfit[process].Integral())=="nan"): continue
    for i in range(1,h_postfit[process].GetNbinsX()+1):
      error = h_postfit[process].GetBinError(i)
      content = h_postfit[process].GetBinContent(i)
      width = h_postfit[process].GetBinLowEdge(i+1)-h_postfit[process].GetBinLowEdge(i)
      h_postfit[process].SetBinContent(i,content*width)

    h_postfit[process].SetLineColor(1)
    h_postfit[process].SetFillColor(TColor.GetColor(colors[process]))
    h_all_postfit.Add(h_postfit[process])
    if (not process in mainbkgs[region]):
      h_other_postfit.Add(h_postfit[process])
    h_postfit[process].Scale(1,"width")

    if region in 'signal':
      if process is 'gjets' or process is 'zll':
        h_postfit[process].SetFillColor(TColor.GetColor(colors['gjets']))
        h_postfit[process].SetLineColor(TColor.GetColor(colors['gjets']))
        h_minor_postfit.Add(h_postfit[process])

      if process is 'gjets':
        h_postfit[process].SetLineColor(1)

    if process is 'zll':
      continue
    elif process is 'gjets':
      h_minor_postfit.SetLineColor(1)
      h_minor_postfit.SetFillColor(TColor.GetColor(colors['gjets']))
      h_stack_postfit.Add(h_minor_postfit)
    else:
      #if region is not 'signal':
      h_stack_postfit.Add(h_postfit[process])

  h_all_postfit.Scale(1,"width")
  h_all_prefit.Scale(1,"width")

  gStyle.SetOptStat(0)

  c = TCanvas("c","c",600,800)
  SetOwnership(c,False)
  c.cd()
  c.SetLogy()
  c.SetBottomMargin(0.38)
  c.SetRightMargin(0.06)
  c.SetTickx(1);
  c.SetTicky(1);

  dummy = h_all_prefit.Clone("dummy")
  dummy.SetFillColor(0)
  dummy.SetLineColor(0)
  dummy.SetLineWidth(0)
  dummy.SetMarkerSize(0)
  dummy.SetMarkerColor(0)
  dummy.GetYaxis().SetTitle("Events / GeV")
  dummy.GetXaxis().SetTitle("")
  dummy.GetXaxis().SetTitleSize(0)
  dummy.GetXaxis().SetLabelSize(0)
  if region is 'signal':
    dummy.SetMaximum(75*dummy.GetMaximum())
  else:
    dummy.SetMaximum(50*dummy.GetMaximum())
  dummy.SetMinimum(0.002)
  dummy.GetYaxis().SetTitleOffset(1.15)
  dummy.Draw()


  h_other_prefit.SetLineColor(1)
  h_other_prefit.SetFillColor(TColor.GetColor(colors["qcd"]))
  h_other_prefit.Scale(1,"width")

  h_all_prefit.SetLineColor(2)
  h_all_prefit.SetLineWidth(2)

  h_all_postfit.SetLineColor(kAzure-4)
  h_all_postfit.SetLineWidth(2)

  if region in 'signal':

    h_postfit['totalsig'].SetLineColor(1);
    h_postfit['totalsig'].SetFillColor(1);
    h_postfit['totalsig'].SetFillStyle(3144);
    if sb:
      h_postfit['totalsig'].Draw("samehist")

    h_stack_postfit.Draw("histsame")

  else:
    h_other_prefit.Draw("histsame")
    h_all_prefit.Draw("histsame")
    h_all_postfit.Draw("histsame")



  h_data.SetMarkerStyle(20)
  h_data.SetLineColor(1)
  h_data.SetMarkerSize(1.2)
  h_data.Scale(1,"width")
  if not blind:
    h_data.Draw("epsame")

  if region == "singlemuon":
    legname = "W #rightarrow #mu#nu"
  if region == "dimuon":
    legname = "Z #rightarrow #mu#mu"
  if region == "gjets":
    legname = "#gamma + jets"
  if region == "singleelectron":
    legname = "W #rightarrow e#nu"
  if region == "dielectron":
    legname = "Z #rightarrow ee"


  #legend.SetTextSize(0.04)
  if region in 'signal' :
    legend = TLegend(0.60, 0.65, 0.92, .92);
    legend.SetFillStyle(0);
    legend.SetBorderSize(0);
    legend.AddEntry(h_data, "Data", "elp")
    if 'mono' in category:
      legend.AddEntry(h_postfit['zjets'], "Z(#nu#nu)+jets", "f")
      legend.AddEntry(h_postfit['wjets'], "W(l#nu)+jets", "f")
      legend.AddEntry(h_postfit['zz'], "WW/ZZ/WZ", "f")
      legend.AddEntry(h_postfit['top'], "Top quark", "f")
      # legend.AddEntry(h_postfit['gjets'], "Z(ll)+jets, #gamma+jets", "f")
      legend.AddEntry(h_postfit['qcd'], "QCD", "f")
    else:
      # pass
      legend.AddEntry(h_postfit['qcd_zjets'], "QCD Z(#nu#nu)+jets", "f")
      legend.AddEntry(h_postfit['qcd_wjets'], "QCD W(l#nu)+jets", "f")
      legend.AddEntry(h_postfit['ewk_zjets'], "EWK Z(#nu#nu)+jets", "f")
      legend.AddEntry(h_postfit['ewk_wjets'], "EWK W(l#nu)+jets", "f")
      legend.AddEntry(h_postfit['diboson'], "WW/ZZ/WZ", "f")
      legend.AddEntry(h_postfit['top'], "Top quark", "f")
      # legend.AddEntry(h_postfit['gjets'], "Z(ll)+jets, #gamma+jets", "f")
      legend.AddEntry(h_postfit['qcd'], "QCD", "f")
    if sb:
      legend.AddEntry(h_postfit['totalsig'], "S+B post-fit", "f")

  else:
    legend = TLegend(.55,.67,.97,.92)
    legend.AddEntry(h_data,"Data","elp")
    legend.AddEntry(h_all_postfit, "Post-fit ("+legname+")", "l")
    legend.AddEntry(h_all_prefit, "Pre-fit ("+legname+")", "l")
    legend.AddEntry(h_other_prefit, "Other Backgrounds", "f")

  legend.SetShadowColor(0);
  legend.SetFillColor(0);
  legend.SetLineColor(0);
  legend.Draw("same")

  latex2 = TLatex()
  latex2.SetNDC()
  latex2.SetTextSize(0.6*c.GetTopMargin())
  latex2.SetTextFont(42)
  latex2.SetTextAlign(31) # align right
  latex2.DrawLatex(0.94, 0.95,"{LUMI:.1f} fb^{{-1}} (13 TeV)".format(LUMI=lumi))
  latex2.SetTextSize(0.6*c.GetTopMargin())
  latex2.SetTextFont(62)
  latex2.SetTextAlign(11) # align right

  latex2.DrawLatex(0.2, 0.87, "CMS")


  latex2.SetTextSize(0.6*c.GetTopMargin())
  latex2.SetTextFont(52)
  latex2.SetTextAlign(11)
  offset = 0.005
  
  if 'monojet' in category:
    channel = 'Monojet'
  elif 'loose' in category:
    channel = 'Mono-V (low-purity)'
  elif 'tight' in category:
    channel = 'Mono-V (high-purity)'


  categoryLabel = TLatex();
  categoryLabel.SetNDC();
  categoryLabel.SetTextSize(0.5*c.GetTopMargin());
  categoryLabel.SetTextFont(42);
  categoryLabel.SetTextAlign(11);
  # if region is "signal":
  categoryLabel.DrawLatex(0.2,0.83,channel);
  categoryLabel.DrawLatex(0.2,0.80,str(year));
  categoryLabel.Draw("same");


  gPad.RedrawAxis()


  pad2 = TPad("pad2", "pad2", 0.0, 0.0, 1.0, 1.0)
  SetOwnership(pad2,False)

  pad2.SetTopMargin(0.63)
  pad2.SetBottomMargin(0.25)
  pad2.SetRightMargin(0.06)
  pad2.SetFillColor(0)
  #pad2.SetGridy(1)
  pad2.SetFillStyle(0)
  pad2.Draw()
  pad2.cd(0)


  met = []; dmet = [];
  ratio_pre = []; ratio_pre_hi = []; ratio_pre_lo = [];
  ratio_post = []; ratio_post_hi = []; ratio_post_lo = [];

  # cutstring = "("

  for i in range(1,h_all_prefit.GetNbinsX()+1):

    ndata = h_data.GetBinContent(i)

    if (ndata>0.0):
      e_data_hi = h_data.GetBinError(i)/ndata
      e_data_lo = h_data.GetBinError(i)/ndata
    else:
      e_data_hi = 0.0
      e_data_lo = 0.0


    n_all_pre = h_all_prefit.GetBinContent(i)
    n_other_pre = h_other_prefit.GetBinContent(i)
    n_all_post = h_all_postfit.GetBinContent(i)


    # cutstring=cutstring+str((n_all_post-n_other_pre)/(n_all_pre-n_other_pre))+"*(met>"+str(h_all_prefit.GetBinLowEdge(i))+"&&met<="+str(h_all_prefit.GetBinLowEdge(i+1))+")"
    # if i<h_all_prefit.GetNbinsX():
    #   cutstring+="+"

    met.append(h_all_prefit.GetBinCenter(i))
    dmet.append((h_all_prefit.GetBinLowEdge(i+1)-h_all_prefit.GetBinLowEdge(i))/2)

    if (n_all_pre>0.0):
      ratio_pre.append(ndata/n_all_pre)
      ratio_pre_hi.append(ndata*e_data_hi/n_all_pre)
      ratio_pre_lo.append(ndata*e_data_lo/n_all_pre)
    else:
      ratio_pre.append(0.0)
      ratio_pre_hi.append(0.0)
      ratio_pre_lo.append(0.0)

    if (n_all_post>0.0):
      ratio_post.append(ndata/n_all_post)
      ratio_post_hi.append(ndata*e_data_hi/n_all_post)
      ratio_post_lo.append(ndata*e_data_lo/n_all_post)
    else:
      ratio_post.append(0.0)
      ratio_post_hi.append(0.0)
      ratio_post_lo.append(0.0)

  # cutstring+=")"
  #print 'cutstring for',region,cutstring

  a_met = array("d", met)
  v_met = TVectorD(len(a_met),a_met)

  a_dmet = array("d", dmet)
  v_dmet = TVectorD(len(a_dmet),a_dmet)

  a_ratio_pre = array("d", ratio_pre)
  a_ratio_pre_hi = array("d", ratio_pre_hi)
  a_ratio_pre_lo = array("d", ratio_pre_lo)

  v_ratio_pre = TVectorD(len(a_ratio_pre),a_ratio_pre)
  v_ratio_pre_hi = TVectorD(len(a_ratio_pre_hi),a_ratio_pre_hi)
  v_ratio_pre_lo = TVectorD(len(a_ratio_pre_lo),a_ratio_pre_lo)

  a_ratio_post = array("d", ratio_post)
  a_ratio_post_hi = array("d", ratio_post_hi)
  a_ratio_post_lo = array("d", ratio_post_lo)

  v_ratio_post = TVectorD(len(a_ratio_post),a_ratio_post)
  v_ratio_post_hi = TVectorD(len(a_ratio_post_hi),a_ratio_post_hi)
  v_ratio_post_lo = TVectorD(len(a_ratio_post_lo),a_ratio_post_lo)

  g_ratio_pre = TGraphAsymmErrors(v_met,v_ratio_pre,v_dmet,v_dmet,v_ratio_pre_lo,v_ratio_pre_hi)
  g_ratio_pre.SetLineColor(2)
  g_ratio_pre.SetMarkerColor(2)
  g_ratio_pre.SetMarkerStyle(20)

  g_ratio_post = TGraphAsymmErrors(v_met,v_ratio_post,v_dmet,v_dmet,v_ratio_post_lo,v_ratio_post_hi)
  #g_ratio_post.SetLineColor(4)
  g_ratio_post.SetLineColor(kAzure-4)
  #g_ratio_post.SetMarkerColor(4)
  g_ratio_post.SetMarkerColor(kAzure-4)
  g_ratio_post.SetMarkerStyle(20)

  ratiosys = h_postfit['totalv2'].Clone();
  for hbin in range(0,ratiosys.GetNbinsX()+1):

    ratiosys.SetBinContent(hbin+1,1.0)
    if (h_postfit['totalv2'].GetBinContent(hbin+1)>0):
      ratiosys.SetBinError(hbin+1,h_postfit['totalv2'].GetBinError(hbin+1)/h_postfit['totalv2'].GetBinContent(hbin+1))

      #print hbin+1, h_data.GetBinContent(hbin+1), h_postfit['totalv2'].GetBinContent(hbin+1),h_postfit['totalv2'].GetBinError(hbin+1)

    else:
      ratiosys.SetBinError(hbin+1,0)


  dummy2 = TH1F("dummy2","dummy2",len(binLowE)-1,array('d',binLowE))
  for i in range(1,dummy2.GetNbinsX()):
    dummy2.SetBinContent(i,1.0)
  dummy2.GetYaxis().SetTitle("Data / Pred.")
      #dummy2.GetXaxis().SetTitle("E_{T}^{miss} [GeV]")
  dummy2.GetXaxis().SetTitle("")

  dummy2.SetLineColor(0)
  dummy2.SetMarkerColor(0)
  dummy2.SetLineWidth(0)
  dummy2.SetMarkerSize(0)
  dummy2.GetYaxis().SetLabelSize(0.04)
  #if region is 'signal':
  dummy2.GetYaxis().SetLabelSize(0.03)
  dummy2.GetXaxis().SetLabelSize(0)
  dummy2.GetYaxis().SetNdivisions(5);
  dummy2.GetYaxis().CenterTitle()
  dummy2.GetYaxis().SetTitleSize(0.03)
  dummy2.GetYaxis().SetTitleOffset(1.6)

  if region is 'signal':
    dummy2.SetMaximum(1.20)
    dummy2.SetMinimum(0.80)

  else:
    dummy2.SetMaximum(1.40)
    dummy2.SetMinimum(0.6)

  dummy2.SetMaximum(1.5)
  dummy2.SetMinimum(0.5)
  dummy2.Draw("hist")

  ratiosys.SetFillColor(kGray)
  ratiosys.SetLineColor(kGray)
  ratiosys.SetLineWidth(1)
  ratiosys.SetMarkerSize(0)
  ratiosys.Draw("e2same")

  f1 = TF1("f1","1",-5000,5000);
  f1.SetLineColor(1);
  f1.SetLineStyle(2);
  f1.SetLineWidth(2);
  f1.Draw("same")

  if not blind:
    g_ratio_pre.Draw("epsame")
    g_ratio_post.Draw("epsame")

  legend2 = TLegend(0.147651,0.2314815,0.6979866,0.2810847,"","brNDC");

  legend2.AddEntry(g_ratio_post, "Background (post-fit)", "ple")
  legend2.AddEntry(g_ratio_pre, "Background (pre-fit)", "ple")

  legend2.SetNColumns(2)

  legend2.SetShadowColor(0);
  legend2.SetFillColor(0);
  legend2.SetLineColor(0);
  #legend2.Draw("same")

  pad = TPad("pad", "pad", 0.0, 0.0, 1.0, 1.0)
  SetOwnership(pad,False)

  pad.SetTopMargin(0.76)
  pad.SetRightMargin(0.06)
  pad.SetFillColor(0)
  #pad.SetGridy(1)
  pad.SetFillStyle(0)
  pad.Draw()
  pad.cd(0)

  ##Compute the pulls
  data_pull = h_data.Clone("pull")
  data_pull.Add(h_postfit['totalv2'],-1)

  data_pull.Sumw2()
  addedsqrt = 0
  mean = 0
  sigma = 0
  chi2 = 0
  TH1.StatOverflows(1)

  dummy_pull = TH1F("dummy33","dummy33",len(binLowE)-1,array('d',binLowE))

  for hbin in range(0,data_pull.GetNbinsX()+1):
    if (h_postfit['totalv2'].GetBinContent(hbin)>0):
      print(category, region, hbin)
      addedsqrt +=  (data_pull.GetBinContent(hbin)*data_pull.GetBinContent(hbin))/(h_postfit['totalv2'].GetBinError(hbin)*h_postfit['totalv2'].GetBinError(hbin))

      sigma = math.sqrt(h_postfit['totalv2'].GetBinError(hbin)* h_postfit['totalv2'].GetBinError(hbin) + h_data.GetBinError(hbin)*h_data.GetBinError(hbin))

      data_pull.SetBinContent(hbin,data_pull.GetBinContent(hbin)/sigma)

      data_pull.SetBinError(hbin,0)
      mean  += data_pull.GetBinContent(hbin)
      chi2  += (data_pull.GetBinContent(hbin)*data_pull.GetBinContent(hbin))

  data_pull.SetLineColor(kAzure-4)
  data_pull.SetFillColor(kAzure-4)
  data_pull.SetMarkerColor(kAzure-4)


  data_pull_sig = h_data.Clone("pull")
  data_pull_sig.Sumw2()
  for hbin in range(0,data_pull_sig.GetNbinsX()+1):
    if (h_postfit['totalv2'].GetBinContent(hbin)>0):
      data_pull_sig.SetBinContent(hbin,data_pull_sig.GetBinContent(hbin)/h_postfit['totalv2'].GetBinError(hbin))
      data_pull_sig.SetBinError(hbin,0)

  data_pull_sig.SetLineColor(2)
  data_pull_sig.SetFillColor(2)
  data_pull_sig.SetFillStyle(3004)
  data_pull_sig.SetMarkerColor(2)


  legend3 = TLegend(0.20,0.21,0.60,0.23,"","brNDC")
  legend3.AddEntry(data_pull    , "Background only", "f")
  legend3.SetNColumns(2)
  legend3.SetShadowColor(0)
  legend3.SetFillColor(0)
  legend3.SetLineColor(0)

  dummy3 = TH1F("dummy3","dummy3",len(binLowE)-1,array('d',binLowE))
  for i in range(1,dummy3.GetNbinsX()):
    dummy3.SetBinContent(i,1.0)
  dummy3.GetYaxis().SetTitle("#frac{(Data-Pred.)}{#sigma}")
  if region in 'signal':
      dummy3.GetXaxis().SetTitle("E_{T}^{miss} [GeV]"  if 'mono' in category else "M_{jj} [GeV]")
  else:
    dummy3.GetXaxis().SetTitle("Recoil [GeV]" if 'mono' in category else "M_{jj} [GeV]")
  dummy3.SetLineColor(0)
  dummy3.SetMarkerColor(0)
  dummy3.SetLineWidth(0)
  dummy3.SetMarkerSize(0)
  dummy3.GetYaxis().SetLabelSize(0.04)
  if region is 'signal':
    dummy3.GetYaxis().SetLabelSize(0.03)
  dummy3.GetYaxis().SetNdivisions(5);
  dummy3.GetYaxis().CenterTitle()
  dummy3.GetYaxis().SetTitleSize(0.03)
  dummy3.GetYaxis().SetTitleOffset(1.3)

  dummy3.SetMaximum(3.5)
  dummy3.SetMinimum(-3.5)

  dummy3.Draw("hist")
  data_pull.Draw("hist same")


  latex_chi = TLatex()
  latex_chi.SetNDC()
  latex_chi.SetTextSize(0.025)


  pad2.RedrawAxis("G sameaxis")

  gPad.RedrawAxis()

  import os
  if not os.path.exists(outdir):
    os.makedirs(outdir)
  c.SaveAs(outdir+"/"+category+"_PULLS_MASKED_prefit_postfit_"+region+"_" + str(year) + "_" + fit + ".pdf")
  c.SaveAs(outdir+"/"+category+"_PULLS_MASKED_prefit_postfit_"+region+"_" + str(year) + "_" + fit + ".png")

  c.Close()
  f_mlfit.Close()
  f_data.Close()
