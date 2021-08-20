import ROOT
from counting_experiment import *
from W_constraints import do_stat_unc, add_variation, add_variation_flat_localized
from utils.jes_utils import get_jes_variations, get_jes_jer_source_file_for_tf, jes_nuisance_name
from utils.mistag import determine_region_wp,mistag_scale_and_flip
import re
ROOT.RooMsgService.instance().setSilentMode(True)

# Define how a control region(s) transfer is made by defining *cmodel*, the calling pattern must be unchanged!
# First define simple string which will be used for the datacard
model = "zjets"

def cmodel(cid,nam,_f,_fOut, out_ws, diag, year):
  filler = {
    "YEAR" : year,
    "CID" : cid,
    "CHANNEL" : "monojet" if "monojet" in cid else "monov"
  }
  # Some setup
  _fin = _f.Get("category_%s"%cid)
  _wspace = _fin.Get("wspace_%s"%cid)

  # ############################ USER DEFINED ###########################################################
  # First define the nominal transfer factors (histograms of signal/control, usually MC
  # note there are many tools available inside include/diagonalize.h for you to make
  # special datasets/histograms representing these and systematic effects
  # example below for creating shape systematic for photon which is just every bin up/down 30%

  metname    = "met"          # Observable variable name
  gvptname   = "genBosonPt"   # Weights are in generator pT

  target             = _fin.Get("signal_zjets")      # define monimal (MC) of which process this config will model
  controlmc          = _fin.Get("Zmm_zll")           # defines Zmm MC of which process will be controlled by
  controlmc_photon   = _fin.Get("gjets_gjets")       # defines Gjets MC of which process will be controlled by
  controlmc_e        = _fin.Get("Zee_zll")           # defines Zmm MC of which process will be controlled by
  controlmc_w        = _fin.Get("signal_wjets")

  # Save the original spectra
  WSpectrum      = controlmc_w.Clone("w_spectrum_%s_"%cid)
  PhotonSpectrum = controlmc_photon.Clone("photon_spectrum_%s_"%cid)
  ZvvSpectrum 	 = target.Clone("zvv_spectrum_%s_"%cid)
  _fOut.WriteTObject( WSpectrum )
  _fOut.WriteTObject( PhotonSpectrum )
  _fOut.WriteTObject( ZvvSpectrum )

  # Create the transfer factors and save them (not here you can also create systematic variations of these
  # transfer factors (named with extention _sysname_Up/Down
  ZmmScales = target.Clone("zmm_weights_%s"%cid)
  ZmmScales.Divide(controlmc)
  _fOut.WriteTObject(ZmmScales)

  ZeeScales = target.Clone("zee_weights_%s"%cid);
  ZeeScales.Divide(controlmc_e)
  _fOut.WriteTObject(ZeeScales)

  WZScales = target.Clone("w_weights_%s"%cid);
  WZScales.Divide(controlmc_w)
  _fOut.WriteTObject(WZScales)

  PhotonScales = target.Clone("photon_weights_%s"%cid);
  PhotonScales.Divide(controlmc_photon)
  _fOut.WriteTObject(PhotonScales)

  #######################################################################################################

  _bins = []  # take bins from some histogram, can choose anything but this is easy
  for b in range(target.GetNbinsX()+1):
    _bins.append(target.GetBinLowEdge(b+1))

  # Here is the important bit which "Builds" the control region, make a list of control regions which
  # are constraining this process, each "Channel" is created with ...
  # 	(name,_wspace,out_ws,cid+'_'+model,TRANSFERFACTORS)
  # the second and third arguments can be left unchanged, the others instead must be set
  # TRANSFERFACTORS are what is created above, eg WScales

  CRs = [
   Channel("photon",_wspace,out_ws,cid+'_'+model,PhotonScales)
  ,Channel("dimuon",_wspace,out_ws,cid+'_'+model,ZmmScales)
  ,Channel("dielectron",_wspace,out_ws,cid+'_'+model,ZeeScales)
  ,Channel("wjetssignal",_wspace,out_ws,cid+'_'+model,WZScales)
  ]
  # my_function(_wspace,_fin,_fOut,cid,diag, filler)

  # ############################ USER DEFINED ###########################################################
  # Add systematics in the following, for normalisations use name, relative size (0.01 --> 1%)
  # for shapes use add_nuisance_shape with (name,_fOut)
  # note, the code will LOOK for something called NOMINAL_name_Up and NOMINAL_name_Down, where NOMINAL=WScales.GetName()
  # these must be created and writted to the same dirctory as the nominal (fDir)

  if "monov" in cid:
    tag = "_monov"
  else:
    tag = ""

  do_stat_unc(PhotonScales, "photon", cid, "photonCR", CRs[0],_fOut)
  do_stat_unc(ZmmScales, "zmm", cid, "dimuonCR", CRs[1],_fOut)
  do_stat_unc(ZeeScales, "zee", cid, "dielectronCR", CRs[2],_fOut)
  do_stat_unc(WZScales, "w", cid, "wzCR", CRs[3],_fOut)

  ## Here now adding the trigger uncertainty
  fztoz_trig = r.TFile.Open("sys/all_trig_2017.root") # 250 - 1400 binning

  # We want to correlate experimental uncertainties between the loose and tight regions.
  cid_corr = re.sub("(loose|tight)","",cid)

  # Take the square of the uncertainty because we are going from zero to two leptons
  add_variation(ZmmScales,fztoz_trig,"trig_sys_sqr_down"+tag,"zmm_weights_%s_mettrig_%s_Down"%(cid,year), _fOut)
  add_variation(ZmmScales,fztoz_trig,"trig_sys_sqr_up"+tag,"zmm_weights_%s_mettrig_%s_Up"%(cid,year), _fOut)
  CRs[1].add_nuisance_shape("mettrig_%s"%year,_fOut, functype='quadratic')

  #######################################################################################################

  ftheo = ROOT.TFile("sys/vjets_reco_theory_unc.root")

  # Theory uncertainties on Z/Gamma
  for variation, name in [
                           ('d1k', 'qcd'),
                           ('d2k', 'qcdshape'),
                           ('d3k', 'qcdprocess'),
                           ('d1kappa', 'ewk'),
                           ('d2kappa_g', 'nnlomissG'),
                           ('d2kappa_z', 'nnlomissZ'),
                           ('d3kappa_g', 'sudakovG'),
                           ('d3kappa_z', 'sudakovZ'),
                           ('mix', 'cross')
                           ]:
    # Flip nuisance directions for compatibility with 2016
    invert = variation in ['d2kappa','d3kappa']
    for direction in 'up', 'down':
      add_variation(
                    PhotonScales,
                    ftheo,
                    "{CHANNEL}_z_over_g_{VARIATION}_{DIR}".format(VARIATION=variation,DIR=direction,**filler),
                    "photon_weights_{CID}_{NAME}_{DIR}".format(NAME=name,DIR=direction.capitalize(),**filler),
                    _fOut,
                    invert=invert
                    )

    CRs[0].add_nuisance_shape(name, _fOut, functype='quadratic')

  # Theory uncertainties on Z/W
  for variation, name in [
                           ('d1k', 'wqcd'),
                           ('d2k', 'wqcdshape'),
                           ('d3k', 'wqcdprocess'),
                           ('d1kappa', 'wewk'),
                           ('d2kappa_w', 'nnlomissW'),
                           ('d2kappa_z', 'nnlomissZ'),
                           ('d3kappa_w', 'sudakovW'),
                           ('d3kappa_z', 'sudakovZ'),
                           ('mix', 'wcross')
                           ]:
    # Flip nuisance directions for compatibility with 2016
    invert = variation in ['d1k','d3k','d1kappa','d2kappa_w','d3kappa_w']
    for direction in 'up', 'down':
      add_variation(
                  WZScales,
                  ftheo,
                  "{CHANNEL}_z_over_w_{VARIATION}_{DIR}".format(VARIATION=variation,DIR=direction,**filler),
                  "w_weights_{CID}_{NAME}_{DIR}".format(NAME=name,DIR=direction.capitalize(),**filler),
                  _fOut,
                  invert=invert
                  )
    CRs[3].add_nuisance_shape(name, _fOut, functype='quadratic')


  # Mistag nuisances
  fmistag = ROOT.TFile("sys/mistag_sf_variations.root")
  region_wp = determine_region_wp(cid)
  for sf_wp in 'loose','tight':
    scale, flip = mistag_scale_and_flip(sf_wp, region_wp)
    if scale == 0:
      continue
    # Gamma uncertainty on Z/gamma ratio
    for variation_index in range(2):
      name = 'CMS_eff{YEAR}_vmistag_g_stat_{SF_WP}_{INDEX}'.format(INDEX=variation_index,  SF_WP=sf_wp, **filler)
      for direction in 'up','down':
        add_variation(
          PhotonScales,
          fmistag,
          'g_{SF_WP}_{YEAR}_{CHANNEL}_var{INDEX}_{DIR}'.format(INDEX=variation_index,DIR=direction, SF_WP=sf_wp, **filler),
          "photon_weights_{CID}_{NAME}_{DIR}".format(NAME=name,DIR=direction.capitalize(),**filler),
          _fOut,
          invert = not flip,
          scale=scale
        )
      CRs[0].add_nuisance_shape(name, _fOut, functype='quadratic')

    # Z uncertainty on Z/gamma ratio
    for variation_index in range(2):
      name = 'CMS_eff{YEAR}_vmistag_z_stat_{SF_WP}_{INDEX}'.format(INDEX=variation_index,  SF_WP=sf_wp, **filler)
      for direction in 'up','down':
        add_variation(
          PhotonScales,
          fmistag,
          'z_{SF_WP}_{YEAR}_{CHANNEL}_var{INDEX}_{DIR}'.format(INDEX=variation_index,DIR=direction,  SF_WP=sf_wp, **filler),
          "photon_weights_{CID}_{NAME}_{DIR}".format(NAME=name,DIR=direction.capitalize(),**filler),
          _fOut,
          invert=flip,
          scale=scale
        )
      CRs[0].add_nuisance_shape(name, _fOut, functype='quadratic')

    # Z uncertainty on Z/W ratio
    for variation_index in range(2):
      name = 'CMS_eff{YEAR}_vmistag_z_stat_{SF_WP}_{INDEX}'.format(INDEX=variation_index,  SF_WP=sf_wp, **filler)
      for direction in 'up','down':
        add_variation(
          WZScales,
          fmistag,
          'z_{SF_WP}_{YEAR}_{CHANNEL}_var{INDEX}_{DIR}'.format(INDEX=variation_index, DIR=direction,  SF_WP=sf_wp, **filler),
          "w_weights_{CID}_{NAME}_{DIR}".format(NAME=name,DIR=direction.capitalize(),**filler),
          _fOut,
          invert=flip,
          scale=scale
        )
      CRs[3].add_nuisance_shape(name, _fOut, functype='quadratic')

    # W uncertainty on Z/W ratio
    for variation_index in range(2):
      name = 'CMS_eff{YEAR}_vmistag_w_stat_{SF_WP}_{INDEX}'.format(INDEX=variation_index,  SF_WP=sf_wp, **filler)
      for direction in 'up','down':
        add_variation(
          WZScales,
          fmistag,
          'w_{SF_WP}_{YEAR}_{CHANNEL}_var{INDEX}_{DIR}'.format(INDEX=variation_index,  SF_WP=sf_wp, DIR=direction, **filler),
          "w_weights_{CID}_{NAME}_{DIR}".format(NAME=name,DIR=direction.capitalize(),**filler),
          _fOut,
          invert=not flip,
          scale=scale
        )
      CRs[3].add_nuisance_shape(name, _fOut, functype='quadratic')





  # PDF uncertainties
  fpdf = ROOT.TFile("sys/tf_pdf_unc.root")

  for direction in 'up', 'down':
    add_variation(
      PhotonScales,
      fpdf,
      "{CHANNEL}_z_over_g_pdf_{YEAR}_{DIR}".format(DIR=direction,**filler),
      "photon_weights_{CID}_z_over_g_pdf_{DIR}".format(DIR=direction.capitalize(), **filler),
      _fOut
    )
    add_variation(
      ZmmScales,
      fpdf,
      "{CHANNEL}_z_over_zmm_pdf_{YEAR}_{DIR}".format(DIR=direction,**filler),
      "zmm_weights_{CID}_z_over_z_pdf_{DIR}".format(DIR=direction.capitalize(), **filler),
      _fOut
    )
    add_variation(
      ZeeScales,
      fpdf,
      "{CHANNEL}_z_over_zee_pdf_{YEAR}_{DIR}".format(DIR=direction,**filler),
      "zee_weights_{CID}_z_over_z_pdf_{DIR}".format(DIR=direction.capitalize(), **filler),
      _fOut
    )
    add_variation(
      WZScales,
      fpdf,
      "{CHANNEL}_z_over_w_pdf_{YEAR}_{DIR}".format(DIR=direction,**filler),
      "w_weights_{CID}_z_over_w_pdf_{DIR}".format(DIR=direction.capitalize(), **filler),
      _fOut
    )

  CRs[0].add_nuisance_shape("z_over_g_pdf",_fOut, functype='quadratic')
  CRs[1].add_nuisance_shape("z_over_z_pdf",_fOut, functype='quadratic')
  CRs[2].add_nuisance_shape("z_over_z_pdf",_fOut, functype='quadratic')
  CRs[3].add_nuisance_shape("z_over_w_pdf",_fOut, functype='quadratic')



  #######################################################################################################


  # Veto uncertainties
  ftauveto = r.TFile.Open("sys/tau_veto_unc.root")
  fmuveto = r.TFile.Open("sys/muon_veto_unc.root")
  felveto = r.TFile.Open("sys/ele_veto_unc.root")

  # The transfer factor here is Z(SR) / W(SR)
  # -> Invert the veto shapes relative to W_constraints, where the TF is W(SR) / W(CR)
  add_variation(WZScales, felveto, "ele_id_veto_sys_{CHANNEL}_up_{YEAR}".format(**filler), "w_weights_%s_eveto_id_%s_Up"%(cid, year), _fOut,invert=True)
  add_variation(WZScales, felveto, "ele_id_veto_sys_{CHANNEL}_down_{YEAR}".format(**filler), "w_weights_%s_eveto_id_%s_Down"%(cid, year), _fOut,invert=True)
  CRs[3].add_nuisance_shape("eveto_id_%s"%year,_fOut, functype='quadratic')

  add_variation(WZScales, felveto, "ele_reco_veto_sys_{CHANNEL}_up_{YEAR}".format(**filler), "w_weights_%s_eveto_reco_%s_Up"%(cid, year), _fOut,invert=True)
  add_variation(WZScales, felveto, "ele_reco_veto_sys_{CHANNEL}_down_{YEAR}".format(**filler), "w_weights_%s_eveto_reco_%s_Down"%(cid, year), _fOut,invert=True)
  CRs[3].add_nuisance_shape("eveto_reco_%s"%year,_fOut, functype='quadratic')

  add_variation(WZScales, ftauveto, "tau_id_veto_sys_{CHANNEL}_up_{YEAR}".format(**filler), "w_weights_%s_tauveto_%s_Up"%(cid, year), _fOut,invert=True)
  add_variation(WZScales, ftauveto, "tau_id_veto_sys_{CHANNEL}_down_{YEAR}".format(**filler), "w_weights_%s_tauveto_%s_Down"%(cid, year), _fOut,invert=True)
  CRs[3].add_nuisance_shape("tauveto_%s"%year,_fOut, functype='quadratic')

  add_variation(WZScales, fmuveto, "muon_id_veto_sys_{CHANNEL}_up_{YEAR}".format(**filler), "w_weights_%s_muveto_id_%s_Up"%(cid, year), _fOut,invert=True)
  add_variation(WZScales, fmuveto, "muon_id_veto_sys_{CHANNEL}_down_{YEAR}".format(**filler), "w_weights_%s_muveto_id_%s_Down"%(cid, year), _fOut,invert=True)
  CRs[3].add_nuisance_shape("muveto_id_%s"%year,_fOut, functype='quadratic')

  add_variation(WZScales, fmuveto, "muon_iso_veto_sys_{CHANNEL}_up_{YEAR}".format(**filler), "w_weights_%s_muveto_iso_%s_Up"%(cid, year), _fOut,invert=True)
  add_variation(WZScales, fmuveto, "muon_iso_veto_sys_{CHANNEL}_down_{YEAR}".format(**filler), "w_weights_%s_muveto_iso_%s_Down"%(cid, year), _fOut,invert=True)
  CRs[3].add_nuisance_shape("muveto_iso_%s"%year,_fOut, functype='quadratic')

  # Prefiring uncertainty
  # The shape in the input file is just one histogram to be used for up/down
  # -> need to invert for one variation
  # Note that the "invert" argument is the other way round for electrons and muons
  # To take into account the anticorrelation between them
  if year == 2017:
    fpref = r.TFile.Open("sys/pref_unc.root")

    add_variation(ZmmScales, fpref, "{CHANNEL}_pref_unc_z_over_mm".format(**filler), "zmm_weights_%s_prefiring_Up"%cid, _fOut)
    add_variation(ZmmScales, fpref, "{CHANNEL}_pref_unc_z_over_mm".format(**filler), "zmm_weights_%s_prefiring_Down"%cid, _fOut,invert=True)
    CRs[1].add_nuisance_shape("prefiring",_fOut, functype='quadratic')

    add_variation(ZeeScales, fpref, "{CHANNEL}_pref_unc_z_over_ee".format(**filler), "zee_weights_%s_prefiring_Up"%cid, _fOut,invert=True)
    add_variation(ZeeScales, fpref, "{CHANNEL}_pref_unc_z_over_ee".format(**filler), "zee_weights_%s_prefiring_Down"%cid, _fOut)
    CRs[2].add_nuisance_shape("prefiring",_fOut, functype='quadratic')


  fphotonid = r.TFile.Open("sys/photon_id_unc.root")
  add_variation(PhotonScales, fphotonid, "{CHANNEL}_{YEAR}_photon_id_up".format(**filler), "photon_weights_%s_CMS_eff%s_pho_Up"%(cid, year), _fOut, invert=True, scale=2.0)
  add_variation(PhotonScales, fphotonid, "{CHANNEL}_{YEAR}_photon_id_dn".format(**filler), "photon_weights_%s_CMS_eff%s_pho_Down"%(cid, year), _fOut, invert=True, scale=2.0)
  CRs[0].add_nuisance_shape("CMS_eff{YEAR}_pho".format(**filler),_fOut, functype='quadratic')
  add_variation(PhotonScales, fphotonid, "{CHANNEL}_{YEAR}_photon_id_extrap_up".format(**filler), "photon_weights_%s_CMS_eff%s_pho_extrap_Up"%(cid, year), _fOut, invert=True, scale=2.0)
  add_variation(PhotonScales, fphotonid, "{CHANNEL}_{YEAR}_photon_id_extrap_dn".format(**filler), "photon_weights_%s_CMS_eff%s_pho_extrap_Down"%(cid, year), _fOut, invert=True, scale=2.0)
  CRs[0].add_nuisance_shape("CMS_eff{YEAR}_pho_extrap".format(**filler),_fOut, functype='quadratic')

  felectronid = r.TFile.Open("sys/ele_id_unc.root")
  add_variation(ZeeScales, felectronid, "{CHANNEL}_{YEAR}_2e_id_stat_up".format(**filler), "zee_weights_%s_CMS_eff%s_e_stat_Up"%(cid, year), _fOut, invert=True, scale=2.0)
  add_variation(ZeeScales, felectronid, "{CHANNEL}_{YEAR}_2e_id_stat_dn".format(**filler), "zee_weights_%s_CMS_eff%s_e_stat_Down"%(cid, year), _fOut, invert=True, scale=2.0)
  CRs[2].add_nuisance_shape("CMS_eff{YEAR}_e_stat".format(**filler),_fOut, functype='quadratic')
  add_variation(ZeeScales, felectronid, "{CHANNEL}_{YEAR}_2e_id_syst_up".format(**filler), "zee_weights_%s_CMS_eff%s_e_syst_Up"%(cid, year), _fOut, invert=True, scale=2.0)
  add_variation(ZeeScales, felectronid, "{CHANNEL}_{YEAR}_2e_id_syst_dn".format(**filler), "zee_weights_%s_CMS_eff%s_e_syst_Down"%(cid, year), _fOut, invert=True, scale=2.0)
  CRs[2].add_nuisance_shape("CMS_eff{YEAR}_e_syst".format(**filler),_fOut, functype='quadratic')
  add_variation(ZeeScales, felectronid, "{CHANNEL}_{YEAR}_2e_reco_up".format(**filler), "zee_weights_%s_CMS_eff%s_e_reco_Up"%(cid, year), _fOut, invert=True)
  add_variation(ZeeScales, felectronid, "{CHANNEL}_{YEAR}_2e_reco_dn".format(**filler), "zee_weights_%s_CMS_eff%s_e_reco_Down"%(cid, year), _fOut, invert=True)
  CRs[2].add_nuisance_shape("CMS_eff{YEAR}_e_reco".format(**filler),_fOut, functype='quadratic')

  # JES uncertainties
  fjes = get_jes_jer_source_file_for_tf(category='monojet')
  jet_variations = get_jes_variations(fjes, year)

  print "VARIATIONS"
  print jet_variations
  for var in jet_variations:
    nuisance = jes_nuisance_name(var)

    for direction in 'Up', 'Down':
      filler_for_jes = {
        "CATEGORY" : cid,
        "YEAR" : year - 2000,
        "VARIATION" : var,
        "NUISANCE" : nuisance,
        "DIRECTION" : direction
      }

      add_variation(
                    nominal=WZScales,
                    unc_file=fjes,
                    unc_name='znunu_over_wlnu{YEAR}_qcd_{VARIATION}{DIRECTION}'.format(**filler_for_jes),
                    new_name="w_weights_{CATEGORY}_{NUISANCE}_{DIRECTION}".format(**filler_for_jes),
                    outfile=_fOut
                    )
      add_variation(
                    nominal=ZmmScales,
                    unc_file=fjes,
                    unc_name='znunu_over_zmumu{YEAR}_qcd_{VARIATION}{DIRECTION}'.format(**filler_for_jes),
                    new_name="zmm_weights_{CATEGORY}_{NUISANCE}_{DIRECTION}".format(**filler_for_jes),
                    outfile=_fOut
                    )
      add_variation(
                    nominal=ZeeScales,
                    unc_file=fjes,
                    unc_name='znunu_over_zee{YEAR}_qcd_{VARIATION}{DIRECTION}'.format(**filler_for_jes),
                    new_name="zee_weights_{CATEGORY}_{NUISANCE}_{DIRECTION}".format(**filler_for_jes),
                    outfile=_fOut
                  )
      add_variation(
                    nominal=PhotonScales,
                    unc_file=fjes,
                    unc_name='znunu_over_gjets{YEAR}_qcd_{VARIATION}{DIRECTION}'.format(**filler_for_jes),
                    new_name="photon_weights_{CATEGORY}_{NUISANCE}_{DIRECTION}".format(**filler_for_jes),
                    outfile=_fOut
                    )
      filler_for_jes = None
    for cr in CRs:
      cr.add_nuisance_shape(nuisance,_fOut, functype='quadratic')

  # Photon scale
  fphotonscale = ROOT.TFile("sys/photon_scale_unc.root")
  var = "photon_scale_%s"%year
  add_variation(
                PhotonScales,
                fphotonscale,
                'photon_pt_scale_{CHANNEL}_0.02_up'.format(**filler),
                "photon_weights_%s_%s_Up"%(cid, var),
                _fOut,
                invert=True,
                scale=0.5
                )
  add_variation(
                PhotonScales,
                fphotonscale,
                'photon_pt_scale_{CHANNEL}_0.02_dn'.format(**filler),
                "photon_weights_%s_%s_Down"%(cid, var),
                _fOut,
                invert=True,
                scale=0.5
                )
  CRs[0].add_nuisance_shape(var, _fOut, functype='quadratic')




  cat = Category(model,cid,nam,_fin,_fOut,_wspace,out_ws,_bins,metname,target.GetName(),CRs,diag)
  # Return of course
  return cat
