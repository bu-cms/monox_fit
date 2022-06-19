import ROOT
from counting_experiment import *
from utils.jes_utils import get_jes_variations, get_jes_jer_source_file_for_tf
from utils.general import read_key_for_year, get_nuisance_name
from W_constraints import do_stat_unc, add_variation
# Define how a control region(s) transfer is made by defining *cmodel*, the calling pattern must be unchanged!
# First define simple string which will be used for the datacard
model = "qcd_zjets"

def cmodel(cid,nam,_f,_fOut, out_ws, diag, year,convention="BU", applyZcorrections=False):

  # Some setup
  _fin = _f.Get("category_%s"%cid)
  _wspace = _fin.Get("wspace_%s"%cid)

  # ############################ USER DEFINED ###########################################################
  # First define the nominal transfer factors (histograms of signal/control, usually MC
  # note there are many tools available inside include/diagonalize.h for you to make
  # special datasets/histograms representing these and systematic effects
  # example below for creating shape systematic for photon which is just every bin up/down 30%

  metname    = 'mjj'          # Observable variable name

  target             = _fin.Get("signal_qcdzjets")      # define monimal (MC) of which process this config will model
  controlmc          = _fin.Get("Zmm_qcdzll")           # defines Zmm MC of which process will be controlled by
  controlmc_e        = _fin.Get("Zee_qcdzll")           # defines Zmm MC of which process will be controlled by
  controlmc_w        = _fin.Get("signal_qcdwjets")
  controlmc_ewk      = _fin.Get('signal_ewkzjets')
  controlmc_photon   = _fin.Get("gjets_qcdgjets")       # defines Gjets MC of which process will be controlled by

  # Apply per bin corrections to Z production
  if applyZcorrections:
    z_corrections = [0.959838, 0.936492, 0.98899, 0.945835, 1.0628, 1.14563, 1.46808, 1.36499, 0.882986]

    # Scale Z production per mjj bin
    for idx in range(1,target.GetNbinsX()):
      content = target.GetBinContent(idx)
      target.SetBinContent(idx, z_corrections[idx-1] * content)

  # Create the transfer factors and save them (not here you can also create systematic variations of these
  # transfer factors (named with extention _sysname_Up/Down

  # QCD Z(vv) / Z(mm) transfer factor
  ZmmScales = target.Clone() 
  ZmmScales.SetName("qcd_zmm_weights_%s"%cid)
  ZmmScales.Divide(controlmc)
  _fOut.WriteTObject(ZmmScales)  # always write out to the directory

  # QCD Z(vv) / Z(ee) transfer factor
  ZeeScales = target.Clone() 
  ZeeScales.SetName("qcd_zee_weights_%s"%cid)
  ZeeScales.Divide(controlmc_e)
  _fOut.WriteTObject(ZeeScales)  # always write out to the directory

  # QCD Z(vv) / W(lv) transfer factor
  WZScales = target.Clone() 
  WZScales.SetName("qcd_w_weights_%s"%cid)
  WZScales.Divide(controlmc_w)
  _fOut.WriteTObject(WZScales)  # always write out to the directory

  # QCD Z(vv) / EWK Z(vv)
  EQScales = target.Clone()
  EQScales.SetName("ewkqcd_weights_%s"%cid)
  EQScales.Divide(controlmc_ewk)
  _fOut.WriteTObject(EQScales)  # always write out to the directory

  # QCD Z(vv) / Gamma+jet
  PhotonScales = target.Clone() 
  PhotonScales.SetName("qcd_photon_weights_%s"%cid)
  PhotonScales.Divide(controlmc_photon)
  _fOut.WriteTObject(PhotonScales) # always write out to the directory

  my_function(_wspace,_fin,_fOut,cid,diag, year)

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
    Channel("qcd_dimuon",_wspace,out_ws,cid+'_'+model,ZmmScales,convention=convention),
    Channel("qcd_dielectron",_wspace,out_ws,cid+'_'+model,ZeeScales,convention=convention),
    Channel("qcd_wjetssignal",_wspace,out_ws,cid+'_'+model,WZScales,convention=convention),
    Channel("qcd_photon",_wspace,out_ws,cid+'_'+model,PhotonScales,convention=convention),
    Channel("ewkqcd_signal",_wspace,out_ws,cid+'_'+model,EQScales,convention=convention),
  ]
  CRs[2].add_nuisance('CMS_veto{YEAR}_t'.format(YEAR=year),     -0.01)
  CRs[2].add_nuisance('CMS_veto{YEAR}_m'.format(YEAR=year),     -0.015)
  CRs[2].add_nuisance('CMS_veto{YEAR}_e'.format(YEAR=year),     -0.03)

  # Get the JES/JER uncertainty file for transfer factors
  # Read the JES/JER uncertainties for TFs from that file
  fjes = get_jes_jer_source_file_for_tf(category='vbf')
  jet_variations = get_jes_variations(fjes, year, proc='qcd')

  # Add the JES/JER variation to the relevant transfer factor
  for var in jet_variations:
    add_variation(WZScales, fjes, 'znunu_over_wlnu{YEAR}_qcd_{VARIATION}Up'.format(YEAR=year-2000, VARIATION=var), "qcd_w_weights_%s_%s_Up"%(cid, var), _fOut)
    add_variation(WZScales, fjes, 'znunu_over_wlnu{YEAR}_qcd_{VARIATION}Down'.format(YEAR=year-2000, VARIATION=var), "qcd_w_weights_%s_%s_Down"%(cid, var), _fOut)
    CRs[2].add_nuisance_shape(var, _fOut)

    add_variation(ZmmScales, fjes, 'znunu_over_zmumu{YEAR}_qcd_{VARIATION}Up'.format(YEAR=year-2000, VARIATION=var), "qcd_zmm_weights_%s_%s_Up"%(cid, var), _fOut)
    add_variation(ZmmScales, fjes, 'znunu_over_zmumu{YEAR}_qcd_{VARIATION}Down'.format(YEAR=year-2000, VARIATION=var), "qcd_zmm_weights_%s_%s_Down"%(cid, var), _fOut)
    CRs[0].add_nuisance_shape(var, _fOut)

    add_variation(ZeeScales, fjes, 'znunu_over_zee{YEAR}_qcd_{VARIATION}Up'.format(YEAR=year-2000, VARIATION=var), "qcd_zee_weights_%s_%s_Up"%(cid, var), _fOut)
    add_variation(ZeeScales, fjes, 'znunu_over_zee{YEAR}_qcd_{VARIATION}Down'.format(YEAR=year-2000, VARIATION=var), "qcd_zee_weights_%s_%s_Down"%(cid, var), _fOut)
    CRs[1].add_nuisance_shape(var, _fOut)

    add_variation(PhotonScales, fjes, 'znunu_over_gjets{YEAR}_qcd_{VARIATION}Up'.format(YEAR=year-2000, VARIATION=var), "qcd_photon_weights_%s_%s_Up"%(cid, var), _fOut)
    add_variation(PhotonScales, fjes, 'znunu_over_gjets{YEAR}_qcd_{VARIATION}Down'.format(YEAR=year-2000, VARIATION=var), "qcd_photon_weights_%s_%s_Down"%(cid, var), _fOut)
    CRs[3].add_nuisance_shape(var, _fOut)

  # ############################ USER DEFINED ###########################################################
  # Add systematics in the following, for normalisations use name, relative size (0.01 --> 1%)
  # for shapes use add_nuisance_shape with (name,_fOut)
  # note, the code will LOOK for something called NOMINAL_name_Up and NOMINAL_name_Down, where NOMINAL=WScales.GetName()
  # these must be created and writted to the same dirctory as the nominal (fDir)

  # Bin by bin nuisances to cover statistical uncertainties ...

  do_stat_unc(ZmmScales,    proc='qcd_zmm',      region='qcd_dimuonCR',     CR=CRs[0], cid=cid, outfile=_fOut)
  do_stat_unc(ZeeScales,    proc='qcd_zee',      region='qcd_dielectronCR', CR=CRs[1], cid=cid, outfile=_fOut)
  do_stat_unc(WZScales,     proc='qcd_w',        region='qcd_wzCR',         CR=CRs[2], cid=cid, outfile=_fOut)
  do_stat_unc(PhotonScales, proc='qcd_photon',   region='qcd_photonCR',     CR=CRs[3], cid=cid, outfile=_fOut)
  do_stat_unc(EQScales,     proc='ewkqcd',       region='ewkqcdzCR',        CR=CRs[4], cid=cid, outfile=_fOut)

  #######################################################################################################

  CRs[2].add_nuisance_shape("ZnunuWJets_QCD_renscale_vbf",_fOut)
  CRs[2].add_nuisance_shape("ZnunuWJets_QCD_facscale_vbf",_fOut)
  CRs[2].add_nuisance_shape("ZnunuWJets_QCD_pdf_vbf",_fOut)

  for b in range(target.GetNbinsX()):
    CRs[2].add_nuisance_shape("qcd_ewk_%s_bin%d"%(re.sub("_201(\d)","",cid),b),_fOut)


  CRs[3].add_nuisance_shape("Photon_QCD_renscale_vbf",_fOut)
  CRs[3].add_nuisance_shape("Photon_QCD_facscale_vbf",_fOut)
  CRs[3].add_nuisance_shape("Photon_QCD_pdf_vbf",_fOut)

  for b in range(target.GetNbinsX()):
    CRs[3].add_nuisance_shape("qcd_photon_ewk_%s_bin%d"%(re.sub("_201(\d)","",cid),b),_fOut)


  #######################################################################################################

  cat = Category(model,cid,nam,_fin,_fOut,_wspace,out_ws,_bins,metname,target.GetName(),CRs,diag,convention=convention)
  # Return of course
  return cat

# My Function. Just to put all of the complicated part into one function
def my_function(_wspace,_fin,_fOut,nam,diag, year):

  metname    = "mjj"   # Observable variable name

  target             = _fin.Get("signal_qcdzjets")      # define monimal (MC) of which process this config will model
  controlmc          = _fin.Get("Zmm_qcdzll")           # defines Zmm MC of which process will be controlled by
  controlmc_w        = _fin.Get("signal_qcdwjets")
  controlmc_photon   = _fin.Get("gjets_qcdgjets")

  #################################################################################################################


  #################################################################################################################
  WSpectrum      = controlmc_w.Clone(); WSpectrum.SetName("qcd_w_spectrum_%s_"%nam)
  ZvvSpectrum    = target.Clone(); ZvvSpectrum.SetName("qcd_zvv_spectrum_%s_"%nam)
  PhotonSpectrum = controlmc_photon.Clone(); PhotonSpectrum.SetName("qcd_gjets_spectrum_%s_"%nam)

  _fOut.WriteTObject( WSpectrum )
  _fOut.WriteTObject( PhotonSpectrum )
  #_fOut.WriteTObject( ZvvSpectrum ) No need to rewrite

  #################################################################################################################

  Wsig = controlmc_w.Clone(); Wsig.SetName("qcd_w_weights_denom_%s"%nam)
  Zvv_w = target.Clone(); Zvv_w.SetName("qcd_w_weights_nom_%s"%nam)

  vbf_sys = r.TFile.Open("sys/vbf_z_w_gjets_theory_unc_ratio_unc.root")

  uncertainty_zoverw_ewk_up   = vbf_sys.Get("uncertainty_ratio_z_qcd_mjj_unc_w_ewkcorr_overz_common_up_"+str(year))
  uncertainty_zoverw_ewk_down = vbf_sys.Get("uncertainty_ratio_z_qcd_mjj_unc_w_ewkcorr_overz_common_down_"+str(year))
  uncertainty_zoverw_mur_up   = vbf_sys.Get("uncertainty_ratio_z_qcd_mjj_unc_zoverw_nlo_mur_up_"+str(year))
  uncertainty_zoverw_mur_down = vbf_sys.Get("uncertainty_ratio_z_qcd_mjj_unc_zoverw_nlo_mur_down_"+str(year))
  uncertainty_zoverw_muf_up   = vbf_sys.Get("uncertainty_ratio_z_qcd_mjj_unc_zoverw_nlo_muf_up_"+str(year))
  uncertainty_zoverw_muf_down = vbf_sys.Get("uncertainty_ratio_z_qcd_mjj_unc_zoverw_nlo_muf_down_"+str(year))
  uncertainty_zoverw_pdf_up   = vbf_sys.Get("uncertainty_ratio_z_qcd_mjj_unc_zoverw_nlo_pdf_up_"+str(year))
  uncertainty_zoverw_pdf_down = vbf_sys.Get("uncertainty_ratio_z_qcd_mjj_unc_zoverw_nlo_pdf_down_"+str(year))

  uncertainty_zoverg_ewk_up   = vbf_sys.Get("uncertainty_ratio_gjets_qcd_mjj_unc_w_ewkcorr_overz_common_up_"+str(year))
  uncertainty_zoverg_ewk_down = vbf_sys.Get("uncertainty_ratio_gjets_qcd_mjj_unc_w_ewkcorr_overz_common_down_"+str(year))
  uncertainty_zoverg_mur_up   = vbf_sys.Get("uncertainty_ratio_gjets_qcd_mjj_unc_goverz_nlo_mur_up_"+str(year))
  uncertainty_zoverg_mur_down = vbf_sys.Get("uncertainty_ratio_gjets_qcd_mjj_unc_goverz_nlo_mur_down_"+str(year))
  uncertainty_zoverg_muf_up   = vbf_sys.Get("uncertainty_ratio_gjets_qcd_mjj_unc_goverz_nlo_muf_up_"+str(year))
  uncertainty_zoverg_muf_down = vbf_sys.Get("uncertainty_ratio_gjets_qcd_mjj_unc_goverz_nlo_muf_down_"+str(year))
  uncertainty_zoverg_pdf_up   = vbf_sys.Get("uncertainty_ratio_gjets_qcd_mjj_unc_goverz_nlo_pdf_up_"+str(year))
  uncertainty_zoverg_pdf_down = vbf_sys.Get("uncertainty_ratio_gjets_qcd_mjj_unc_goverz_nlo_pdf_down_"+str(year))

  def add_var(num, denom, name, factor):
    new = num.Clone(name)
    new.Divide(denom)
    new.Multiply(factor)
    _fOut.WriteTObject(new)

  # QCD uncertainties
  add_var(num=Zvv_w, denom=Wsig, name="qcd_w_weights_%s_ZnunuWJets_QCD_renscale_vbf_Up"%nam,   factor=uncertainty_zoverw_mur_up)
  add_var(num=Zvv_w, denom=Wsig, name="qcd_w_weights_%s_ZnunuWJets_QCD_renscale_vbf_Down"%nam, factor=uncertainty_zoverw_mur_down)
  add_var(num=Zvv_w, denom=Wsig, name="qcd_w_weights_%s_ZnunuWJets_QCD_facscale_vbf_Up"%nam,   factor=uncertainty_zoverw_muf_up)
  add_var(num=Zvv_w, denom=Wsig, name="qcd_w_weights_%s_ZnunuWJets_QCD_facscale_vbf_Down"%nam, factor=uncertainty_zoverw_muf_down)
  # PDF Uncertainty
  add_var(num=Zvv_w, denom=Wsig, name="qcd_w_weights_%s_ZnunuWJets_QCD_pdf_vbf_Up"%nam, factor=uncertainty_zoverw_pdf_up)
  add_var(num=Zvv_w, denom=Wsig, name="qcd_w_weights_%s_ZnunuWJets_QCD_pdf_vbf_Down"%nam, factor=uncertainty_zoverw_pdf_down)

  # EWK uncertainty (decorrelated among bins)
  wratio_ewk_up = Zvv_w.Clone();  wratio_ewk_up.SetName("qcd_w_weights_%s_ewk_Up"%nam);
  wratio_ewk_up.Divide(Wsig)
  wratio_ewk_up.Multiply(uncertainty_zoverw_ewk_up)

  wratio_ewk_down = Zvv_w.Clone();  wratio_ewk_down.SetName("qcd_w_weights_%s_ewk_Down"%nam);
  wratio_ewk_down.Divide(Wsig)
  wratio_ewk_down.Multiply(uncertainty_zoverw_ewk_down)

  Zvv_w.Divide(Wsig)

  for b in range(target.GetNbinsX()):
    ewk_up_w = Zvv_w.Clone(); ewk_up_w.SetName("qcd_w_weights_%s_qcd_ewk_%s_bin%d_Up"%(nam,re.sub("_201(\d)","",nam),b))
    ewk_down_w = Zvv_w.Clone(); ewk_down_w.SetName("qcd_w_weights_%s_qcd_ewk_%s_bin%d_Down"%(nam,re.sub("_201(\d)","",nam),b))
    for i in range(target.GetNbinsX()):
      if i==b:
        ewk_up_w.SetBinContent(i+1,wratio_ewk_up.GetBinContent(i+1))
        ewk_down_w.SetBinContent(i+1,wratio_ewk_down.GetBinContent(i+1))
        break

    _fOut.WriteTObject(ewk_up_w)
    _fOut.WriteTObject(ewk_down_w)




### Photons  #################################################################################################################

  Photon = controlmc_photon.Clone(); Photon.SetName("qcd_photon_weights_denom_%s"%nam)
  Zvv_g = target.Clone(); Zvv_g.SetName("qcd_photon_weights_nom_%s"%nam)

  # QCD Uncertainties
  add_var(num=target, denom=controlmc_photon, name="qcd_photon_weights_%s_Photon_QCD_renscale_vbf_Up"%nam, factor=uncertainty_zoverg_mur_up)
  add_var(num=target, denom=controlmc_photon, name="qcd_photon_weights_%s_Photon_QCD_renscale_vbf_Down"%nam, factor=uncertainty_zoverg_mur_down)
  add_var(num=target, denom=controlmc_photon, name="qcd_photon_weights_%s_Photon_QCD_facscale_vbf_Up"%nam, factor=uncertainty_zoverg_muf_up)
  add_var(num=target, denom=controlmc_photon, name="qcd_photon_weights_%s_Photon_QCD_facscale_vbf_Down"%nam, factor=uncertainty_zoverg_muf_down)

  # PDF Uncertainty
  add_var(num=target, denom=controlmc_photon, name="qcd_photon_weights_%s_Photon_QCD_pdf_vbf_Up"%nam, factor=uncertainty_zoverg_pdf_up)
  add_var(num=target, denom=controlmc_photon, name="qcd_photon_weights_%s_Photon_QCD_pdf_vbf_Down"%nam, factor=uncertainty_zoverg_pdf_down)

  # EWK uncertainty (decorrelated among bins)
  gratio_ewk_up = Zvv_g.Clone();  gratio_ewk_up.SetName("qcd_photon_weights_%s_ewk_Up"%nam);
  gratio_ewk_up.Divide(Photon)
  gratio_ewk_up.Multiply(uncertainty_zoverg_ewk_up)

  gratio_ewk_down = Zvv_g.Clone();  gratio_ewk_down.SetName("qcd_photon_weights_%s_ewk_Down"%nam);
  gratio_ewk_down.Divide(Photon)
  gratio_ewk_down.Multiply(uncertainty_zoverg_ewk_down)

  Zvv_g.Divide(Photon)

  #Now lets uncorrelate the bins:
  for b in range(target.GetNbinsX()):
    ewk_up_g = Zvv_g.Clone(); ewk_up_g.SetName("qcd_photon_weights_%s_qcd_photon_ewk_%s_bin%d_Up"%(nam,re.sub("_201(\d)","",nam),b))
    ewk_down_g = Zvv_g.Clone(); ewk_down_g.SetName("qcd_photon_weights_%s_qcd_photon_ewk_%s_bin%d_Down"%(nam,re.sub("_201(\d)","",nam),b))
    for i in range(target.GetNbinsX()):
      if i==b:
        ewk_up_g.SetBinContent(i+1,gratio_ewk_up.GetBinContent(i+1))
        ewk_down_g.SetBinContent(i+1,gratio_ewk_down.GetBinContent(i+1))
        break

    _fOut.WriteTObject(ewk_up_g)
    _fOut.WriteTObject(ewk_down_g)

