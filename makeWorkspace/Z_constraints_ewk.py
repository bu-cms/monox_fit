import ROOT
from counting_experiment import *
import fitConfig
# Define how a control region(s) transfer is made by defining *cmodel*, the calling pattern must be unchanged!
# First define simple string which will be used for the datacard 
model = "ewk_zjets"

def cmodel(cid,nam,_f,_fOut, out_ws, diag):
  
  # Some setup
  _fin = _f.Get("category_%s"%cid)
  _wspace = _fin.Get("wspace_%s"%cid)

  # ############################ USER DEFINED ###########################################################
  # First define the nominal transfer factors (histograms of signal/control, usually MC 
  # note there are many tools available inside include/diagonalize.h for you to make 
  # special datasets/histograms representing these and systematic effects 
  # example below for creating shape systematic for photon which is just every bin up/down 30% 

  metname    = fitConfig.metname          # Observable variable name 
  gvptname   = "genBosonPt"    # Weights are in generator pT

  target             = _fin.Get("signal_ewkzjets")      # define monimal (MC) of which process this config will model
  controlmc          = _fin.Get("Zmm_ewkzll")           # defines Zmm MC of which process will be controlled by
  controlmc_e        = _fin.Get("Zee_ewkzll")           # defines Zmm MC of which process will be controlled by
  controlmc_w        = _fin.Get("signal_ewkwjets")

  # Create the transfer factors and save them (not here you can also create systematic variations of these 
  # transfer factors (named with extention _sysname_Up/Down
  ZmmScales = target.Clone(); ZmmScales.SetName("ewk_zmm_weights_%s"%cid)
  ZmmScales.Divide(controlmc)
  _fOut.WriteTObject(ZmmScales)  # always write out to the directory 

  ZeeScales = target.Clone(); ZeeScales.SetName("ewk_zee_weights_%s"%cid)
  ZeeScales.Divide(controlmc_e)
  _fOut.WriteTObject(ZeeScales)  # always write out to the directory 

  WZScales = target.Clone(); WZScales.SetName("ewk_w_weights_%s"%cid)
  WZScales.Divide(controlmc_w)
  _fOut.WriteTObject(WZScales)  # always write out to the directory 
  my_function(_wspace,_fin,_fOut,cid,diag)

  #######################################################################################################

  _bins = []  # take bins from some histogram, can choose anything but this is easy 
  for b in range(target.GetNbinsX()+1):
    _bins.append(target.GetBinLowEdge(b+1))

  # Here is the important bit which "Builds" the control region, make a list of control regions which 
  # are constraining this process, each "Channel" is created with ...
  #   (name,_wspace,out_ws,cid+'_'+model,TRANSFERFACTORS) 
  # the second and third arguments can be left unchanged, the others instead must be set
  # TRANSFERFACTORS are what is created above, eg WScales

  CRs = [
  Channel("ewk_dimuon",_wspace,out_ws,cid+'_'+model,ZmmScales)
  ,Channel("ewk_dielectron",_wspace,out_ws,cid+'_'+model,ZeeScales)
  ,Channel("ewk_wjetssignal",_wspace,out_ws,cid+'_'+model,WZScales)
  ]
  for c in CRs[:2]:
    c.add_nuisance('CMS_trigger2016_met',0.02)
    c.add_nuisance('CMS_scale2016_j_vbf',0.01)

  # ############################ USER DEFINED ###########################################################
  # Add systematics in the following, for normalisations use name, relative size (0.01 --> 1%)
  # for shapes use add_nuisance_shape with (name,_fOut)
  # note, the code will LOOK for something called NOMINAL_name_Up and NOMINAL_name_Down, where NOMINAL=WScales.GetName()
  # these must be created and writted to the same dirctory as the nominal (fDir)

  # Bin by bin nuisances to cover statistical uncertainties ...

  for b in range(target.GetNbinsX()):
    err = ZmmScales.GetBinError(b+1)
    if not ZmmScales.GetBinContent(b+1)>0: continue 
    relerr = err/ZmmScales.GetBinContent(b+1)
    if relerr<0.01: continue
    byb_u = ZmmScales.Clone(); byb_u.SetName("ewk_zmm_weights_%s_%s_stat_error_%s_bin%d_Up"%(cid,cid,"ewk_dimuonCR",b))
    byb_u.SetBinContent(b+1,ZmmScales.GetBinContent(b+1)+err)
    byb_d = ZmmScales.Clone(); byb_d.SetName("ewk_zmm_weights_%s_%s_stat_error_%s_bin%d_Down"%(cid,cid,"ewk_dimuonCR",b))
    if (ZmmScales.GetBinContent(b+1)-err > 0):
      byb_d.SetBinContent(b+1,ZmmScales.GetBinContent(b+1)-err)
    else:
      byb_d.SetBinContent(b+1,1)
    _fOut.WriteTObject(byb_u)
    _fOut.WriteTObject(byb_d)
    print "Adding an error -- ", byb_u.GetName(),err
    CRs[0].add_nuisance_shape("%s_stat_error_%s_bin%d"%(cid,"ewk_dimuonCR",b),_fOut)

  for b in range(target.GetNbinsX()):
    err = ZeeScales.GetBinError(b+1)
    if not ZeeScales.GetBinContent(b+1)>0: continue 
    relerr = err/ZeeScales.GetBinContent(b+1)
    if relerr<0.01: continue
    byb_u = ZeeScales.Clone(); byb_u.SetName("ewk_zee_weights_%s_%s_stat_error_%s_bin%d_Up"%(cid,cid,"ewk_dielectronCR",b))
    byb_u.SetBinContent(b+1,ZeeScales.GetBinContent(b+1)+err)
    byb_d = ZeeScales.Clone(); byb_d.SetName("ewk_zee_weights_%s_%s_stat_error_%s_bin%d_Down"%(cid,cid,"ewk_dielectronCR",b))
    if (ZeeScales.GetBinContent(b+1)-err > 0):
      byb_d.SetBinContent(b+1,ZeeScales.GetBinContent(b+1)-err)
    else:
      byb_d.SetBinContent(b+1,1)
    _fOut.WriteTObject(byb_u)
    _fOut.WriteTObject(byb_d)
    print "Adding an error -- ", byb_u.GetName(),err
    CRs[1].add_nuisance_shape("%s_stat_error_%s_bin%d"%(cid,"ewk_dielectronCR",b),_fOut)

  for b in range(target.GetNbinsX()):
    err = WZScales.GetBinError(b+1)
    if not WZScales.GetBinContent(b+1)>0: continue 
    relerr = err/WZScales.GetBinContent(b+1)
    if relerr<0.01: continue
    byb_u = WZScales.Clone(); byb_u.SetName("ewk_w_weights_%s_%s_stat_error_%s_bin%d_Up"%(cid,cid,"ewk_wzCR",b))
    byb_u.SetBinContent(b+1,WZScales.GetBinContent(b+1)+err)
    byb_d = WZScales.Clone(); byb_d.SetName("ewk_w_weights_%s_%s_stat_error_%s_bin%d_Down"%(cid,cid,"ewk_wzCR",b))
    if (WZScales.GetBinContent(b+1)-err > 0):
      byb_d.SetBinContent(b+1,WZScales.GetBinContent(b+1)-err)
    else:
      byb_d.SetBinContent(b+1,1)
    _fOut.WriteTObject(byb_u)
    _fOut.WriteTObject(byb_d)
    print "Adding an error -- ", byb_u.GetName(),err
    CRs[2].add_nuisance_shape("%s_stat_error_%s_bin%d"%(cid,"ewk_wzCR",b),_fOut)


  #######################################################################################################
  
  
  CRs[2].add_nuisance_shape("ZnunuWJets_EWK_renscale_vbf",_fOut)
  CRs[2].add_nuisance_shape("ZnunuWJets_EWK_facscale_vbf",_fOut)
  CRs[2].add_nuisance_shape("ZnunuWJets_EWK_pdf_vbf",_fOut) 

  for b in range(target.GetNbinsX()):
    CRs[2].add_nuisance_shape("ewk_ewk_%s_bin%d"%(cid,b),_fOut)

  #######################################################################################################

  cat = Category(model,cid,nam,_fin,_fOut,_wspace,out_ws,_bins,metname,target.GetName(),CRs,diag)
  cat.setDependant("qcd_zjets","ewkqcd_signal")  
  # Return of course
  return cat


# My Function. Just to put all of the complicated part into one function
def my_function(_wspace,_fin,_fOut,nam,diag):

  metname    = fitConfig.metname   # Observable variable name 
  gvptname   = "genBosonPt"    # Weights are in generator pT

  target             = _fin.Get("signal_ewkzjets")      # define monimal (MC) of which process this config will model
  controlmc          = _fin.Get("Zmm_ewkzll")           # defines Zmm MC of which process will be controlled by

  controlmc_w        = _fin.Get("signal_ewkwjets")


  #################################################################################################################


  #################################################################################################################                                                                   

  #################################################################################################################
  ### Now lets do the same thing for W

  #fztow = r.TFile.Open("files/wtoz_unc.root")
  fztow = r.TFile.Open("files/new/wtoz_unc.root") 

  ztow_renscale_up   = fztow.Get("znlo1_over_wnlo1_renScaleUp")
  ztow_renscale_down = fztow.Get("znlo1_over_wnlo1_renScaleDown")

  ztow_facscale_up   = fztow.Get("znlo1_over_wnlo1_facScaleUp")
  ztow_facscale_down = fztow.Get("znlo1_over_wnlo1_facScaleDown")

  ztow_pdf_up   = fztow.Get("znlo1_over_wnlo1_pdfUp")
  ztow_pdf_down = fztow.Get("znlo1_over_wnlo1_pdfDown")

  WSpectrum = controlmc_w.Clone(); WSpectrum.SetName("ewk_w_spectrum_%s_"%nam)
  ZvvSpectrum    = target.Clone(); ZvvSpectrum.SetName("ewk_zvv_spectrum_%s_"%nam)

  _fOut.WriteTObject( WSpectrum )
  #_fOut.WriteTObject( ZvvSpectrum ) No need to rewrite

  #################################################################################################################

  Wsig = controlmc_w.Clone(); Wsig.SetName("ewk_w_weights_denom_%s"%nam)
  Zvv_w = target.Clone(); Zvv_w.SetName("ewk_w_weights_nom_%s"%nam)

  wratio_ren_scale_up = Zvv_w.Clone();  wratio_ren_scale_up.SetName("ewk_w_weights_%s_ZnunuWJets_EWK_renscale_vbf_Up"%nam);
  for b in range(wratio_ren_scale_up.GetNbinsX()): wratio_ren_scale_up.SetBinContent(b+1,0)  
  diag.generateWeightedTemplate(wratio_ren_scale_up,ztow_renscale_up,gvptname,metname,_wspace.data("signal_ewkzjets"))
  wratio_ren_scale_up.Divide(Wsig)
  _fOut.WriteTObject(wratio_ren_scale_up)
  
  wratio_ren_scale_down = Zvv_w.Clone();  wratio_ren_scale_down.SetName("ewk_w_weights_%s_ZnunuWJets_EWK_renscale_vbf_Down"%nam);
  for b in range(wratio_ren_scale_down.GetNbinsX()): wratio_ren_scale_down.SetBinContent(b+1,0)  
  diag.generateWeightedTemplate(wratio_ren_scale_down,ztow_renscale_down,gvptname,metname,_wspace.data("signal_ewkzjets"))
  wratio_ren_scale_down.Divide(Wsig)
  _fOut.WriteTObject(wratio_ren_scale_down)

  wratio_fac_scale_up = Zvv_w.Clone(); wratio_fac_scale_up.SetName("ewk_w_weights_%s_ZnunuWJets_EWK_facscale_vbf_Up"%nam);
  for b in range(wratio_fac_scale_up.GetNbinsX()): wratio_fac_scale_up.SetBinContent(b+1,0)  
  diag.generateWeightedTemplate(wratio_fac_scale_up,ztow_facscale_up,gvptname,metname,_wspace.data("signal_ewkzjets"))
  wratio_fac_scale_up.Divide(Wsig)
  _fOut.WriteTObject(wratio_fac_scale_up)
  
  wratio_fac_scale_down = Zvv_w.Clone();  wratio_fac_scale_down.SetName("ewk_w_weights_%s_ZnunuWJets_EWK_facscale_vbf_Down"%nam);
  for b in range(wratio_fac_scale_down.GetNbinsX()): wratio_fac_scale_down.SetBinContent(b+1,0)  
  diag.generateWeightedTemplate(wratio_fac_scale_down,ztow_facscale_down,gvptname,metname,_wspace.data("signal_ewkzjets"))
  wratio_fac_scale_down.Divide(Wsig)
  _fOut.WriteTObject(wratio_fac_scale_down)

  wratio_pdf_up = Zvv_w.Clone();  wratio_pdf_up.SetName("ewk_w_weights_%s_ZnunuWJets_EWK_pdf_vbf_Up"%nam);
  for b in range(wratio_pdf_up.GetNbinsX()): wratio_pdf_up.SetBinContent(b+1,0)  
  diag.generateWeightedTemplate(wratio_pdf_up,ztow_pdf_up,gvptname,metname,_wspace.data("signal_ewkzjets"))
  wratio_pdf_up.Divide(Wsig)
  _fOut.WriteTObject(wratio_pdf_up)
  
  wratio_pdf_down = Zvv_w.Clone();  wratio_pdf_down.SetName("ewk_w_weights_%s_ZnunuWJets_EWK_pdf_vbf_Down"%nam);
  for b in range(wratio_pdf_down.GetNbinsX()): wratio_pdf_down.SetBinContent(b+1,0)  
  diag.generateWeightedTemplate(wratio_pdf_down,ztow_pdf_down,gvptname,metname,_wspace.data("signal_ewkzjets"))
  wratio_pdf_down.Divide(Wsig)
  _fOut.WriteTObject(wratio_pdf_down)

  #fztowewk = r.TFile.Open("files/wtoz_ewkunc.root")
  fztowewk = r.TFile.Open("files/new/wtoz_unc.root")
  ztow_ewk_up   = fztowewk.Get("w_ewkcorr_overz_Upcommon")
  ztow_ewk_down = fztowewk.Get("w_ewkcorr_overz_Downcommon")

  wratio_ewk_up = Zvv_w.Clone();  wratio_ewk_up.SetName("ewk_w_weights_%s_ewk_Up"%nam);
  for b in range(wratio_ewk_up.GetNbinsX()): wratio_ewk_up.SetBinContent(b+1,0)  
  diag.generateWeightedTemplate(wratio_ewk_up,ztow_ewk_up,gvptname,metname,_wspace.data("signal_ewkzjets"))
  wratio_ewk_up.Divide(Wsig)
  # We are now going to uncorrelate the bins
  #_fOut.WriteTObject(ratio_ewk_up)
  
  wratio_ewk_down = Zvv_w.Clone();  wratio_ewk_down.SetName("ewk_w_weights_%s_ewk_Down"%nam);
  for b in range(wratio_ewk_down.GetNbinsX()): wratio_ewk_down.SetBinContent(b+1,0)  
  diag.generateWeightedTemplate(wratio_ewk_down,ztow_ewk_down,gvptname,metname,_wspace.data("signal_ewkzjets"))
  wratio_ewk_down.Divide(Wsig)
  # We are now going to uncorrelate the bins
  #_fOut.WriteTObject(ratio_ewk_down)


  ############### GET SOMETHING CENTRAL PLEASE ############################
  #Wsig = controlmc_w.Clone(); Wsig.SetName("w_weights_denom_%s"%nam)
  #Zvv_w = target.Clone(); Zvv_w.SetName("w_weights_nom_%s"%nam)

  Zvv_w.Divide(Wsig)

  #Now lets uncorrelate the bins:
  for b in range(target.GetNbinsX()):
    #print "HELLO trying to fill up / down"
    ewk_up_w = Zvv_w.Clone(); ewk_up_w.SetName("ewk_w_weights_%s_ewk_ewk_%s_bin%d_Up"%(nam,nam,b))
    ewk_down_w = Zvv_w.Clone(); ewk_down_w.SetName("ewk_w_weights_%s_ewk_ewk_%s_bin%d_Down"%(nam,nam,b))
    for i in range(target.GetNbinsX()):
      if i==b:
        ewk_up_w.SetBinContent(i+1,wratio_ewk_up.GetBinContent(i+1))
        ewk_down_w.SetBinContent(i+1,wratio_ewk_down.GetBinContent(i+1))
        break

    #print "HELLO filled up / down ",ewk_up.GetBinContent(b+1), ewk_down.GetBinContent(b+1)

    _fOut.WriteTObject(ewk_up_w)
    _fOut.WriteTObject(ewk_down_w)

