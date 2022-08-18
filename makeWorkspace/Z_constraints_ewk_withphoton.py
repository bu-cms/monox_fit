import ROOT
from counting_experiment import *
from utils.jes_utils import get_jes_variations, get_jes_jer_source_file_for_tf
from utils.general import read_key_for_year, get_nuisance_name
from W_constraints import do_stat_unc, add_variation
# Define how a control region(s) transfer is made by defining *cmodel*, the calling pattern must be unchanged!
# First define simple string which will be used for the datacard
model = "ewk_zjets"

def cmodel(cid,nam,_f,_fOut, out_ws, diag, year, convention="BU", applyZcorrections=False):

  # Some setup
  _fin = _f.Get("category_%s"%cid)
  _wspace = _fin.Get("wspace_%s"%cid)

  # ############################ USER DEFINED ###########################################################
  # First define the nominal transfer factors (histograms of signal/control, usually MC
  # note there are many tools available inside include/diagonalize.h for you to make
  # special datasets/histograms representing these and systematic effects
  # example below for creating shape systematic for photon which is just every bin up/down 30%

  metname    = 'mjj'           # Observable variable name

  target             = _fin.Get("signal_ewkzjets")      # define monimal (MC) of which process this config will model
  controlmc          = _fin.Get("Zmm_ewkzll")           # defines Zmm MC of which process will be controlled by
  controlmc_e        = _fin.Get("Zee_ewkzll")           # defines Zmm MC of which process will be controlled by
  controlmc_w        = _fin.Get("signal_ewkwjets")
  controlmc_g        = _fin.Get("gjets_ewkgjets")

  # Apply per bin corrections to Z production
  if applyZcorrections:
    z_corrections = [0.959838, 0.936492, 0.98899, 0.945835, 1.0628, 1.14563, 1.46808, 1.36499, 0.882986]

    # Scale Z production per mjj bin
    for idx in range(1,target.GetNbinsX()):
      content = target.GetBinContent(idx)
      target.SetBinContent(idx, z_corrections[idx-1] * content)

  # Create the transfer factors and save them (not here you can also create systematic variations of these
  # transfer factors (named with extention _sysname_Up/Down

  # EWK Z(vv) / Z(mm)
  ZmmScales = target.Clone() 
  ZmmScales.SetName("ewk_zmm_weights_%s"%cid)
  ZmmScales.Divide(controlmc)
  _fOut.WriteTObject(ZmmScales)  # always write out to the directory

  # EWK Z(vv) / Z(ee)
  ZeeScales = target.Clone() 
  ZeeScales.SetName("ewk_zee_weights_%s"%cid)
  ZeeScales.Divide(controlmc_e)
  _fOut.WriteTObject(ZeeScales)  # always write out to the directory

  # EWK Z(vv) / W(lv)
  WZScales = target.Clone()
  WZScales.SetName("ewk_w_weights_%s"%cid)
  WZScales.Divide(controlmc_w)
  _fOut.WriteTObject(WZScales)  # always write out to the directory

  # EWK Z(vv) / gamma+jets
  PhotonScales = target.Clone() 
  PhotonScales.SetName("ewk_photon_weights_%s"%cid)
  PhotonScales.Divide(controlmc_g)
  _fOut.WriteTObject(PhotonScales)


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
    Channel("ewk_dimuon",_wspace,out_ws,cid+'_'+model,ZmmScales,convention=convention),
    Channel("ewk_dielectron",_wspace,out_ws,cid+'_'+model,ZeeScales,convention=convention),
    Channel("ewk_wjetssignal",_wspace,out_ws,cid+'_'+model,WZScales,convention=convention),
    Channel("ewk_photon",_wspace,out_ws,cid+'_'+model,PhotonScales,convention=convention),
  ]

  # Veto weight uncertainties on Z / W
  CRs[2].add_nuisance('CMS_eff_tauveto_{YEAR}'.format(YEAR=year),     -0.01)
  
  CRs[2].add_nuisance('CMS_eff_e_idiso_veto_{YEAR}'.format(YEAR=year),  -0.005)
  CRs[2].add_nuisance('CMS_eff_e_reco_veto_{YEAR}'.format(YEAR=year),  -0.01)

  CRs[2].add_nuisance('CMS_eff_m_id_veto', -0.001)
  CRs[2].add_nuisance('CMS_eff_m_iso_veto', -0.002)

  # Pileup uncertainties on ratios
  for i in range(len(CRs)):
    CRs[i].add_nuisance('CMS_pileup', 0.01)

  # Get the JES/JER uncertainty file for transfer factors
  # Read the split uncertainties from there
  fjes = get_jes_jer_source_file_for_tf(category='vbf')
  jet_variations = get_jes_variations(fjes, year, proc='ewk')

  for var in jet_variations:
    add_variation(WZScales, fjes, 'znunu_over_wlnu{YEAR}_ewk_{VARIATION}Up'.format(YEAR=year-2000, VARIATION=var), "ewk_w_weights_%s_%s_Up"%(cid, var), _fOut)
    add_variation(WZScales, fjes, 'znunu_over_wlnu{YEAR}_ewk_{VARIATION}Down'.format(YEAR=year-2000, VARIATION=var), "ewk_w_weights_%s_%s_Down"%(cid, var), _fOut)
    CRs[2].add_nuisance_shape(var, _fOut)

    add_variation(ZmmScales, fjes, 'znunu_over_zmumu{YEAR}_ewk_{VARIATION}Up'.format(YEAR=year-2000, VARIATION=var), "ewk_zmm_weights_%s_%s_Up"%(cid, var), _fOut)
    add_variation(ZmmScales, fjes, 'znunu_over_zmumu{YEAR}_ewk_{VARIATION}Down'.format(YEAR=year-2000, VARIATION=var), "ewk_zmm_weights_%s_%s_Down"%(cid, var), _fOut)
    CRs[0].add_nuisance_shape(var, _fOut)

    add_variation(ZeeScales, fjes, 'znunu_over_zee{YEAR}_ewk_{VARIATION}Up'.format(YEAR=year-2000, VARIATION=var), "ewk_zee_weights_%s_%s_Up"%(cid, var), _fOut)
    add_variation(ZeeScales, fjes, 'znunu_over_zee{YEAR}_ewk_{VARIATION}Down'.format(YEAR=year-2000, VARIATION=var), "ewk_zee_weights_%s_%s_Down"%(cid, var), _fOut)
    CRs[1].add_nuisance_shape(var, _fOut)

    add_variation(PhotonScales, fjes, 'znunu_over_gjets{YEAR}_ewk_{VARIATION}Up'.format(YEAR=year-2000, VARIATION=var), "ewk_photon_weights_%s_%s_Up"%(cid, var), _fOut)
    add_variation(PhotonScales, fjes, 'znunu_over_gjets{YEAR}_ewk_{VARIATION}Down'.format(YEAR=year-2000, VARIATION=var), "ewk_photon_weights_%s_%s_Down"%(cid, var), _fOut)
    CRs[3].add_nuisance_shape(var, _fOut)

  # Prefire uncertainties
  f_pref = r.TFile.Open("sys/vbf_prefire_uncs_TF.root")
  variation = 'CMS_L1prefire_2017'

  add_variation(WZScales, f_pref, "%sUp"%variation, "ewk_w_weights_%s_%s_Up"%(cid, variation), _fOut)
  add_variation(WZScales, f_pref, "%sDown"%variation, "ewk_w_weights_%s_%s_Down"%(cid, variation), _fOut)
  CRs[2].add_nuisance_shape(variation, _fOut)

  add_variation(ZmmScales, f_pref, "%sUp"%variation, "ewk_zmm_weights_%s_%s_Up"%(cid, variation), _fOut)
  add_variation(ZmmScales, f_pref, "%sDown"%variation, "ewk_zmm_weights_%s_%s_Down"%(cid, variation), _fOut)
  CRs[0].add_nuisance_shape(variation, _fOut)

  add_variation(ZeeScales, f_pref, "%sUp"%variation, "ewk_zee_weights_%s_%s_Up"%(cid, variation), _fOut)
  add_variation(ZeeScales, f_pref, "%sDown"%variation, "ewk_zee_weights_%s_%s_Down"%(cid, variation), _fOut)
  CRs[1].add_nuisance_shape(variation, _fOut)

  add_variation(PhotonScales, f_pref, "%sUp"%variation, "ewk_photon_weights_%s_%s_Up"%(cid, variation), _fOut)
  add_variation(PhotonScales, f_pref, "%sDown"%variation, "ewk_photon_weights_%s_%s_Down"%(cid, variation), _fOut)
  CRs[3].add_nuisance_shape(variation, _fOut)

  f_pref.Close()


  # ############################ USER DEFINED ###########################################################
  # Add systematics in the following, for normalisations use name, relative size (0.01 --> 1%)
  # for shapes use add_nuisance_shape with (name,_fOut)
  # note, the code will LOOK for something called NOMINAL_name_Up and NOMINAL_name_Down, where NOMINAL=WScales.GetName()
  # these must be created and writted to the same dirctory as the nominal (fDir)

  # Bin by bin nuisances to cover statistical uncertainties ...

  do_stat_unc(ZmmScales,    proc='ewk_zmm',      region='ewk_dimuonCR',     CR=CRs[0], cid=cid, outfile=_fOut)
  do_stat_unc(ZeeScales,    proc='ewk_zee',      region='ewk_dielectronCR', CR=CRs[1], cid=cid, outfile=_fOut)
  do_stat_unc(WZScales,     proc='ewk_w',        region='ewk_wzCR',         CR=CRs[2], cid=cid, outfile=_fOut)
  do_stat_unc(PhotonScales, proc='ewk_photon',   region='ewk_photonCR',     CR=CRs[3], cid=cid, outfile=_fOut)

  #######################################################################################################


  CRs[2].add_nuisance_shape("ZnunuWJets_EWK_renscale_vbf",_fOut)
  CRs[2].add_nuisance_shape("ZnunuWJets_EWK_facscale_vbf",_fOut)
  CRs[2].add_nuisance_shape("ZnunuWJets_EWK_pdf_vbf",_fOut)

  for b in range(target.GetNbinsX()):
    CRs[2].add_nuisance_shape("ewk_ewk_%s_bin%d"%(re.sub("_201(\d)","",cid),b),_fOut)

  CRs[3].add_nuisance_shape("Photon_EWK_renscale_vbf",_fOut)
  CRs[3].add_nuisance_shape("Photon_EWK_facscale_vbf",_fOut)
  CRs[3].add_nuisance_shape("Photon_EWK_pdf_vbf",_fOut)

  for b in range(target.GetNbinsX()):
    CRs[3].add_nuisance_shape("ewkphoton_ewk_%s_bin%d"%(re.sub("_201(\d)","",cid),b),_fOut)

  #######################################################################################################

  cat = Category(model,cid,nam,_fin,_fOut,_wspace,out_ws,_bins,metname,target.GetName(),CRs,diag,convention=convention)
  cat.setDependant("qcd_zjets","ewkqcd_signal")
  # Return of course
  return cat


# My Function. Just to put all of the complicated part into one function
def my_function(_wspace,_fin,_fOut,nam,diag, year):

  metname    = "mjj"   # Observable variable name

  target             = _fin.Get("signal_ewkzjets")      # define monimal (MC) of which process this config will model
  controlmc          = _fin.Get("Zmm_ewkzll")           # defines Zmm MC of which process will be controlled by

  controlmc_w        = _fin.Get("signal_ewkwjets")
  controlmc_photon   = _fin.Get("gjets_ewkgjets")


  #################################################################################################################

  #################################################################################################################
  ### Now lets do the same thing for W

  vbf_sys = r.TFile.Open("sys/vbf_z_w_gjets_theory_unc_ratio_unc.root")

  uncertainty_zoverw_ewk_down = vbf_sys.Get("uncertainty_ratio_z_ewk_mjj_unc_w_ewkcorr_overz_common_down_"+str(year))
  uncertainty_zoverw_ewk_up   = vbf_sys.Get("uncertainty_ratio_z_ewk_mjj_unc_w_ewkcorr_overz_common_up_"+str(year))
  uncertainty_zoverw_muf_down = vbf_sys.Get("uncertainty_ratio_z_ewk_mjj_unc_zoverw_nlo_muf_down_"+str(year))
  uncertainty_zoverw_muf_up   = vbf_sys.Get("uncertainty_ratio_z_ewk_mjj_unc_zoverw_nlo_muf_up_"+str(year))
  uncertainty_zoverw_mur_down = vbf_sys.Get("uncertainty_ratio_z_ewk_mjj_unc_zoverw_nlo_mur_down_"+str(year))
  uncertainty_zoverw_mur_up   = vbf_sys.Get("uncertainty_ratio_z_ewk_mjj_unc_zoverw_nlo_mur_up_"+str(year))
  uncertainty_zoverw_pdf_down = vbf_sys.Get("uncertainty_ratio_z_ewk_mjj_unc_zoverw_nlo_pdf_down_"+str(year))
  uncertainty_zoverw_pdf_up   = vbf_sys.Get("uncertainty_ratio_z_ewk_mjj_unc_zoverw_nlo_pdf_up_"+str(year))

  uncertainty_zoverg_ewk_down = vbf_sys.Get("uncertainty_ratio_gjets_ewk_mjj_unc_w_ewkcorr_overz_common_down_"+str(year))
  uncertainty_zoverg_ewk_up   = vbf_sys.Get("uncertainty_ratio_gjets_ewk_mjj_unc_w_ewkcorr_overz_common_up_"+str(year))
  uncertainty_zoverg_muf_down = vbf_sys.Get("uncertainty_ratio_gjets_ewk_mjj_unc_goverz_nlo_muf_down_"+str(year))
  uncertainty_zoverg_muf_up   = vbf_sys.Get("uncertainty_ratio_gjets_ewk_mjj_unc_goverz_nlo_muf_up_"+str(year))
  uncertainty_zoverg_mur_down = vbf_sys.Get("uncertainty_ratio_gjets_ewk_mjj_unc_goverz_nlo_mur_down_"+str(year))
  uncertainty_zoverg_mur_up   = vbf_sys.Get("uncertainty_ratio_gjets_ewk_mjj_unc_goverz_nlo_mur_up_"+str(year))
  uncertainty_zoverg_pdf_down = vbf_sys.Get("uncertainty_ratio_gjets_ewk_mjj_unc_goverz_nlo_pdf_down_"+str(year))
  uncertainty_zoverg_pdf_up   = vbf_sys.Get("uncertainty_ratio_gjets_ewk_mjj_unc_goverz_nlo_pdf_up_"+str(year))

  WSpectrum = controlmc_w.Clone(); WSpectrum.SetName("ewk_w_spectrum_%s_"%nam)
  ZvvSpectrum    = target.Clone(); ZvvSpectrum.SetName("ewk_zvv_spectrum_%s_"%nam)
  PhotonSpectrum = controlmc_photon.Clone(); WSpectrum.SetName("ewk_photon_spectrum_%s_"%nam)

  _fOut.WriteTObject( WSpectrum )
  _fOut.WriteTObject( PhotonSpectrum )
  #_fOut.WriteTObject( ZvvSpectrum ) No need to rewrite

  #################################################################################################################

  Wsig = controlmc_w.Clone(); Wsig.SetName("ewk_w_weights_denom_%s"%nam)
  Zvv_w = target.Clone(); Zvv_w.SetName("ewk_w_weights_nom_%s"%nam)

  def add_var(num, denom, name, factor):
    new = num.Clone(name)
    new.Divide(denom)
    new.Multiply(factor)
    _fOut.WriteTObject(new)

  # QCD uncertainties
  add_var(num=Zvv_w, denom=Wsig, name="ewk_w_weights_%s_ZnunuWJets_EWK_renscale_vbf_Up"%nam,   factor=uncertainty_zoverw_mur_up)
  add_var(num=Zvv_w, denom=Wsig, name="ewk_w_weights_%s_ZnunuWJets_EWK_renscale_vbf_Down"%nam, factor=uncertainty_zoverw_mur_down)
  add_var(num=Zvv_w, denom=Wsig, name="ewk_w_weights_%s_ZnunuWJets_EWK_facscale_vbf_Up"%nam,   factor=uncertainty_zoverw_muf_up)
  add_var(num=Zvv_w, denom=Wsig, name="ewk_w_weights_%s_ZnunuWJets_EWK_facscale_vbf_Down"%nam, factor=uncertainty_zoverw_muf_down)
  # PDF Uncertainty
  add_var(num=Zvv_w, denom=Wsig, name="ewk_w_weights_%s_ZnunuWJets_EWK_pdf_vbf_Up"%nam, factor=uncertainty_zoverw_pdf_up)
  add_var(num=Zvv_w, denom=Wsig, name="ewk_w_weights_%s_ZnunuWJets_EWK_pdf_vbf_Down"%nam, factor=uncertainty_zoverw_pdf_down)

  uncertainty_zoverw_ewk_up= vbf_sys.Get("uncertainty_ratio_z_ewk_mjj_unc_w_ewkcorr_overz_common_up_"+str(year))
  uncertainty_zoverw_ewk_down = vbf_sys.Get("uncertainty_ratio_z_ewk_mjj_unc_w_ewkcorr_overz_common_down_"+str(year))

  wratio_ewk_up = Zvv_w.Clone();  wratio_ewk_up.SetName("ewk_w_weights_%s_ewk_Up"%nam);
  wratio_ewk_up.Divide(Wsig)
  wratio_ewk_up.Multiply(uncertainty_zoverw_ewk_up)

  # EWK uncertainty (decorrelated among bins)
  wratio_ewk_down = Zvv_w.Clone();  wratio_ewk_down.SetName("ewk_w_weights_%s_ewk_Down"%nam);
  wratio_ewk_down.Divide(Wsig)
  wratio_ewk_down.Multiply(uncertainty_zoverw_ewk_down)

  Zvv_w.Divide(Wsig)

  #Now lets uncorrelate the bins:
  for b in range(target.GetNbinsX()):
    #print "HELLO trying to fill up / down"
    ewk_up_w = Zvv_w.Clone(); ewk_up_w.SetName("ewk_w_weights_%s_ewk_ewk_%s_bin%d_Up"%(nam,re.sub("_201(\d)","",nam),b))
    ewk_down_w = Zvv_w.Clone(); ewk_down_w.SetName("ewk_w_weights_%s_ewk_ewk_%s_bin%d_Down"%(nam,re.sub("_201(\d)","",nam),b))
    for i in range(target.GetNbinsX()):
      if i==b:
        ewk_up_w.SetBinContent(i+1,wratio_ewk_up.GetBinContent(i+1))
        ewk_down_w.SetBinContent(i+1,wratio_ewk_down.GetBinContent(i+1))
        break

    #print "HELLO filled up / down ",ewk_up.GetBinContent(b+1), ewk_down.GetBinContent(b+1)

    _fOut.WriteTObject(ewk_up_w)
    _fOut.WriteTObject(ewk_down_w)



  ########PHOTON#########
  #################################################################################################################

  Photon = controlmc_photon.Clone(); Photon.SetName("ewk_photon_weights_denom_%s"%nam)
  Zvv_g = target.Clone(); Zvv_g.SetName("ewk_photon_weights_nom_%s"%nam)

  # QCD Uncertainties
  add_var(num=target, denom=controlmc_photon, name="ewk_photon_weights_%s_Photon_EWK_renscale_vbf_Up"%nam, factor=uncertainty_zoverg_mur_up)
  add_var(num=target, denom=controlmc_photon, name="ewk_photon_weights_%s_Photon_EWK_renscale_vbf_Down"%nam, factor=uncertainty_zoverg_mur_down)
  add_var(num=target, denom=controlmc_photon, name="ewk_photon_weights_%s_Photon_EWK_facscale_vbf_Up"%nam, factor=uncertainty_zoverg_muf_up)
  add_var(num=target, denom=controlmc_photon, name="ewk_photon_weights_%s_Photon_EWK_facscale_vbf_Down"%nam, factor=uncertainty_zoverg_muf_down)

  # PDF Uncertainty
  add_var(num=target, denom=controlmc_photon, name="ewk_photon_weights_%s_Photon_EWK_pdf_vbf_Up"%nam, factor=uncertainty_zoverg_pdf_up)
  add_var(num=target, denom=controlmc_photon, name="ewk_photon_weights_%s_Photon_EWK_pdf_vbf_Down"%nam, factor=uncertainty_zoverg_pdf_down)

  # EWK uncertainty (decorrelated among bins)
  gratio_ewk_up = Zvv_g.Clone();  gratio_ewk_up.SetName("ewk_photon_weights_%s_ewk_Up"%nam);
  gratio_ewk_up.Divide(Photon)
  gratio_ewk_up.Multiply(uncertainty_zoverg_ewk_up)

  gratio_ewk_down = Zvv_g.Clone();  gratio_ewk_down.SetName("ewk_photon_weights_%s_ewk_Down"%nam);
  gratio_ewk_down.Divide(Photon)
  gratio_ewk_down.Multiply(uncertainty_zoverg_ewk_down)

  Zvv_g.Divide(Photon)

  #Now lets uncorrelate the bins:
  for b in range(target.GetNbinsX()):
    #print "HELLO trying to fill up / down"
    ewk_up_g = Zvv_g.Clone(); ewk_up_g.SetName("ewk_photon_weights_%s_ewkphoton_ewk_%s_bin%d_Up"%(nam,re.sub("_201(\d)","",nam),b))
    ewk_down_g = Zvv_g.Clone(); ewk_down_g.SetName("ewk_photon_weights_%s_ewkphoton_ewk_%s_bin%d_Down"%(nam,re.sub("_201(\d)","",nam),b))
    for i in range(target.GetNbinsX()):
      if i==b:
        ewk_up_g.SetBinContent(i+1,gratio_ewk_up.GetBinContent(i+1))
        ewk_down_g.SetBinContent(i+1,gratio_ewk_down.GetBinContent(i+1))
        break

    #print "HELLO filled up / down ",ewk_up.GetBinContent(b+1), ewk_down.GetBinContent(b+1)

    _fOut.WriteTObject(ewk_up_g)
    _fOut.WriteTObject(ewk_down_g)

