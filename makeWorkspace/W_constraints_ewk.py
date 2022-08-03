import ROOT
from counting_experiment import *
from utils.jes_utils import get_jes_variations, get_jes_jer_source_file_for_tf
from utils.general import read_key_for_year, get_nuisance_name
from W_constraints import do_stat_unc, add_variation
# Define how a control region(s) transfer is made by defining cmodel provide, the calling pattern must be unchanged!
# First define simple string which will be used for the datacard 
model = "ewk_wjets"
def cmodel(cid,nam,_f,_fOut, out_ws, diag,year, convention="BU"):
  
  # Some setup
  _fin    = _f.Get("category_%s"%cid)
  _wspace = _fin.Get("wspace_%s"%cid)


  # ############################ USER DEFINED ###########################################################
  # First define the nominal transfer factors (histograms of signal/control, usually MC 
  # note there are many tools available inside include/diagonalize.h for you to make 
  # special datasets/histograms representing these and systematic effects 
  # but for now this is just kept simple 
  processName  = "WJets" # Give a name of the process being modelled
  metname      = 'mjj'    # Observable variable name 
  targetmc     = _fin.Get("signal_ewkwjets")      # define monimal (MC) of which process this config will model
  controlmc    = _fin.Get("Wmn_ewkwjets")  # defines in / out acceptance
  controlmc_e  = _fin.Get("Wen_ewkwjets")  # defines in / out acceptance

  # Create the transfer factors and save them (not here you can also create systematic variations of these 
  # transfer factors (named with extention _sysname_Up/Down
  
  # EWK W(lv) / EWK W(munu) transfer factor
  WScales = targetmc.Clone()
  WScales.SetName("ewk_wmn_weights_%s"%cid)
  WScales.Divide(controlmc)
  _fOut.WriteTObject(WScales)  

  # EWK W(lv) / EWK W(enu) transfer factor
  WScales_e = targetmc.Clone()
  WScales_e.SetName("ewk_wen_weights_%s"%cid)
  WScales_e.Divide(controlmc_e)
  _fOut.WriteTObject(WScales_e)  



  #######################################################################################################

  _bins = []  # take bins from some histogram, can choose anything but this is easy 
  for b in range(targetmc.GetNbinsX()+1):
    _bins.append(targetmc.GetBinLowEdge(b+1))

  # Here is the important bit which "Builds" the control region, make a list of control regions which 
  # are constraining this process, each "Channel" is created with ...
  #   (name,_wspace,out_ws,cid+'_'+model,TRANSFERFACTORS) 
  # the second and third arguments can be left unchanged, the others instead must be set
  # TRANSFERFACTORS are what is created above, eg WScales

  CRs = [
   Channel("ewk_singlemuon",_wspace,out_ws,cid+'_'+model,WScales, convention=convention),
   Channel("ewk_singleelectron",_wspace,out_ws,cid+'_'+model,WScales_e, convention=convention),
  ]

  # Get the JES/JER unlcertainty file for transfer factors
  # Read the split uncertainties from there
  fjes = get_jes_jer_source_file_for_tf(category='vbf')
  jet_variations = get_jes_variations(fjes, year, proc='ewk')

  for var in jet_variations:
    add_variation(WScales, fjes, 'wlnu_over_wmunu{YEAR}_ewk_{VARIATION}Up'.format(YEAR=year-2000, VARIATION=var), "ewk_wmn_weights_%s_%s_Up"%(cid, var), _fOut)
    add_variation(WScales, fjes, 'wlnu_over_wmunu{YEAR}_ewk_{VARIATION}Down'.format(YEAR=year-2000, VARIATION=var), "ewk_wmn_weights_%s_%s_Down"%(cid, var), _fOut)
    CRs[0].add_nuisance_shape(var,_fOut)

    add_variation(WScales_e, fjes, 'wlnu_over_wenu{YEAR}_ewk_{VARIATION}Up'.format(YEAR=year-2000, VARIATION=var), "ewk_wen_weights_%s_%s_Up"%(cid, var), _fOut)
    add_variation(WScales_e, fjes, 'wlnu_over_wenu{YEAR}_ewk_{VARIATION}Down'.format(YEAR=year-2000, VARIATION=var), "ewk_wen_weights_%s_%s_Down"%(cid, var), _fOut)
    CRs[1].add_nuisance_shape(var,_fOut)

  # Prefire uncertainties
  f_pref = r.TFile.Open("sys/vbf_prefire_uncs_TF.root")
  variation = 'CMS_L1prefire_2017'

  add_variation(WScales, f_pref, "%sUp"%variation, "ewk_wmn_weights_%s_%s_Up"%(cid, variation), _fOut)
  add_variation(WScales, f_pref, "%sDown"%variation, "ewk_wmn_weights_%s_%s_Down"%(cid, variation), _fOut)
  CRs[0].add_nuisance_shape(variation,_fOut)

  add_variation(WScales_e, f_pref, "%sUp"%variation, "ewk_wen_weights_%s_%s_Up"%(cid, variation), _fOut)
  add_variation(WScales_e, f_pref, "%sDown"%variation, "ewk_wen_weights_%s_%s_Down"%(cid, variation), _fOut)
  CRs[1].add_nuisance_shape(variation,_fOut)

  # Veto weight uncertainties
  for c in CRs:
    c.add_nuisance('CMS_eff_tauveto_{YEAR}'.format(YEAR=year),     0.01)

    c.add_nuisance('CMS_eff_e_idiso_veto_{YEAR}'.format(YEAR=year),  0.005)
    c.add_nuisance('CMS_eff_e_reco_veto_{YEAR}'.format(YEAR=year),  0.01)

    c.add_nuisance('CMS_eff_m_id_veto', 0.001)
    c.add_nuisance('CMS_eff_m_iso_veto', 0.002)

  # ############################ USER DEFINED ###########################################################
  # Add systematics in the following, for normalisations use name, relative size (0.01 --> 1%)
  # for shapes use add_nuisance_shape with (name,_fOut)
  # note, the code will LOOK for something called NOMINAL_name_Up and NOMINAL_name_Down, where NOMINAL=WScales.GetName()
  # these must be created and writted to the same dirctory as the nominal (fDir)
  do_stat_unc(WScales,proc='ewk_wmn', region='ewk_singlemuon', CR=CRs[0], cid=cid,outfile=_fOut)
  do_stat_unc(WScales_e,proc='ewk_wen', region='ewk_singleelectron', CR=CRs[1], cid=cid,outfile=_fOut)

  #######################################################################################################

  cat = Category(model,cid,nam,_fin,_fOut,_wspace,out_ws,_bins,metname,targetmc.GetName(),CRs,diag, convention=convention)
  cat.setDependant("ewk_zjets","ewk_wjetssignal")  # Can use this to state that the "BASE" of this is already dependant on another process
  # EG if the W->lv in signal is dependant on the Z->vv and then the W->mv is depenant on W->lv, then 
  # give the arguments model,channel name from the config which defines the Z->vv => W->lv map! 
  # Return of course
  return cat

