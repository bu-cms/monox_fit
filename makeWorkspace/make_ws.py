#!/usr/bin/env python

import argparse
import os
import re
from math import sqrt
from collections import defaultdict

import ROOT
from HiggsAnalysis.CombinedLimit.ModelTools import *
from utils.general import extract_year, extract_channel, is_MC_bkg

ROOT.gSystem.Load("libHiggsAnalysisCombinedLimit")
pjoin = os.path.join

def cli_args():
    parser = argparse.ArgumentParser(prog='Convert input histograms into RooWorkspace.')
    parser.add_argument('file', type=str, help='Input file to use.')
    parser.add_argument('--out', type=str, help='Path to save output under.', default='mono-x.root')
    parser.add_argument('--categories', type=str, default=None, help='Analysis category')
    parser.add_argument('--standalone', default=False, action='store_true', help='Treat this as a standalone conversion.')
    parser.add_argument('--indir', default=None, type=str, help='Input directory in the input file.')
    args = parser.parse_args()

    args.file = os.path.abspath(args.file)
    args.out = os.path.abspath(args.out)
    if not os.path.exists(args.file):
      raise IOError("Input file not found: " + args.file)
    if not args.file.endswith('.root'):
      raise IOError("Input file is not a ROOT file: " + args.file)
    if not args.categories:
      raise IOError("Please specify the --categories option.")

    args.categories = args.categories.split(',')

    return args

def get_jes_file(category):
  '''Get the relevant JES source file for the given category.'''
  # By default: Get the uncertainties with smearing for VBF, the opposite for monojet
  jer_suffix = 'jer_smeared' if 'vbf' in category else 'not_jer_smeared'
  # JES shape files for each category
  f_jes_dict = {
    '(monoj|monov).*': ROOT.TFile("sys/monoj_monov_shape_jes_uncs_smooth_{}.root".format(jer_suffix) ),
    'vbf.*': ROOT.TFile("sys/vbf_shape_jes_uncs_smooth_{}.root".format(jer_suffix) )
  }
  # Determine the relevant JES source file
  f_jes = None
  for regex, f in f_jes_dict.items():
    if re.match(regex, category):
      f_jes = f
  if not f_jes:
    raise RuntimeError('Could not find a JES source file for category: {}'.format(category))

  print('Using JES/JER uncertainty file: {}'.format(f_jes))

  return f_jes

def get_jes_variations(obj, f_jes, category):
  '''Get JES variations from JES source file, returns all the varied histograms stored in a dictionary.'''
  # Use QCD Z(vv) shapes from the source file
  # Save varied histograms for all JES variations and the histogram names in this dictionary
  varied_hists = {}

  keynames = [x.GetName() for x in f_jes.GetListOfKeys()]

  if 'vbf' in category:
    tag = 'ZJetsToNuNu'
    key_valid =lambda x: (tag in x) and (not 'jesTotal' in x), keynames
    regex_to_remove = '{TAG}20\d\d_'.format(TAG=tag)
  else:
    channel = 'monov' if 'monov' in category else 'monojet'
    key_valid = lambda x: x.startswith(channel)
    regex_to_remove = "{CHANNEL}_20\d\d_".format(CHANNEL=channel)

  for key in filter(key_valid, keynames):
    variation = re.sub(regex_to_remove, '', key)
    varied_name = obj.GetName()+"_"+variation
    varied_obj = obj.Clone(varied_name)
      # Multiply by JES factor to get the varied yields
    varied_obj.Multiply(f_jes.Get(key))
    # Save the varied histogram into a dict
    varied_hists[varied_name] = varied_obj

  return varied_hists

def get_photon_id_variations(obj, category):
  '''Get photon ID variations from file, returns all the varied histograms stored in a dictionary.'''



  channel = re.sub("(loose|tight)","", category)

  m = re.match(".*(201(6|7|8)).*", category)
  year = m.groups()[0]

  filler = {
    "CHANNEL" : channel,
    "YEAR" : year,
  }
  name_map = {
    "CMS_eff{YEAR}_phoUp"   : "{CHANNEL}_photon_id_up",
    "CMS_eff{YEAR}_phoDown" : "{CHANNEL}_photon_id_dn",
    "CMS_eff{YEAR}_pho_extrapUp"   : "{CHANNEL}_photon_id_extrap_up",
    "CMS_eff{YEAR}_pho_extrapDown" : "{CHANNEL}_photon_id_extrap_dn",
  }

  varied_hists = {}
  f = ROOT.TFile("sys/photon_id_unc.root")
  for variation, histo_name in name_map.items():
    variation = variation.format(**filler)
    histo_name = histo_name.format(**filler)

    varied_name = obj.GetName()+"_"+variation

    varied_obj = obj.Clone(varied_name)
    varied_obj.Multiply(f.Get(histo_name))
    varied_obj.SetDirectory(0)
    varied_hists[varied_name] = varied_obj

  if(f):
    f.Close()
  return varied_hists

def hist_apply(histogram, function):
  for i in range(1,histogram.GetNbinsX()+1):
    content = histogram.GetBinContent(i)
    error = histogram.GetBinError(i)

    scale = function (histogram.GetBinCenter(i))
    histogram.SetBinContent(i, content * scale)
    histogram.SetBinError(i, error * scale)

def get_photon_qcd_variations(obj, category):
  m = re.match(".*(201(6|7|8)).*", category)
  year = m.groups()[0]

  unc = 1.05 if year==2018 else 1.10

  varied_hists = {}
  func_up = lambda x: 1 + (unc-1)/550 *(x-250)
  func_dn = lambda x: 1 - (unc-1)/550 *(x-250)

  varname = 'purity_fit_{YEAR}'.format(YEAR=year)

  name = "{INITIAL}_{VARIATION}Up".format(INITIAL=obj.GetName(), VARIATION=varname)
  varied_obj = obj.Clone(name)
  varied_obj.SetDirectory(0)
  hist_apply(varied_obj, func_up)
  varied_hists[name] = varied_obj

  name = "{INITIAL}_{VARIATION}Down".format(INITIAL=obj.GetName(), VARIATION=varname)
  varied_obj = obj.Clone(name)
  varied_obj.SetDirectory(0)
  hist_apply(varied_obj, func_dn)
  varied_hists[name] = varied_obj

  return varied_hists


def get_diboson_variations(obj, category, process):
  '''Return list of varied histograms from diboson histogram file'''
  channel = re.sub("(loose|tight|_201\d)","", category)
  varied_hists = {}

  f = ROOT.TFile("sys/shape_diboson_unc.root")
  for key in [x.GetName() for x in f.GetListOfKeys()]:
    if not process in key:
      continue
    if not channel in key:
      continue
    variation = key.replace(channel + "_" + process + "_", "")

    name = obj.GetName()+"_"+variation
    varied_obj = obj.Clone(name)
    varied_obj.Multiply(f.Get(key))
    varied_obj.SetDirectory(0)
    varied_hists[name] = varied_obj
  if(f):
    f.Close()
  return varied_hists

def get_signal_theory_variations(obj, category):
  '''Return list of varied histograms from signal theory histogram file'''
  name = obj.GetName()
  if not name.startswith("signal_"):
    return {}

  channel = re.sub("(loose|tight|_201\d)","", category)
  varied_hists = {}

  real_process = name.replace("signal_","")
  process_for_unc = None

  m = re.match('(vbf|ggh|ggzh|zh|wh)(\d+)?',real_process)
  if m:
    process_for_unc = m.groups()[0]

  m = re.match('(vector|axial|pseudoscalar|scalar)_monow_.*',real_process)
  if m:
    process_for_unc = 'wh'

  m = re.match('(vector|axial|pseudoscalar|scalar)_(monoz|monov)_.*',real_process)
  if m:
    process_for_unc = 'zh'

  m = re.match('(vector|axial|pseudoscalar|scalar)_monojet_.*',real_process)
  if m:
    process_for_unc = 'ggh'

  m = re.match('add_md\d+_d\d',real_process)
  if m:
    process_for_unc = 'ggh'

  m = re.match('lq_m\d+_d[\d,p]+',real_process)
  if m:
    process_for_unc = 'ggh'
  
  m = re.match('.*S3D.*',real_process)
  if m:
    process_for_unc = 'ggh'
  
  m = re.match('.*svj.*',real_process)
  if m:
    process_for_unc = 'ggh'

  if not process_for_unc:
    return {}

  f = ROOT.TFile("sys/signal_theory_unc.root")

  for unctype in 'pdf','scale':
    for direction in 'Up','Down':
      filler={'CHANNEL':channel, 'PROCESS_FOR_UNC':process_for_unc, 'UNCTYPE':unctype,'DIRECTION':direction, 'REAL_PROCESS':real_process}

      if unctype=='scale':
        name = 'signal_{REAL_PROCESS}_QCDscale_{REAL_PROCESS}_ACCEPT{DIRECTION}'.format(**filler)
      elif unctype=='pdf':
        name = 'signal_{REAL_PROCESS}_pdf_{REAL_PROCESS}_ACCEPT{DIRECTION}'.format(**filler)

      varname = '{CHANNEL}_{PROCESS_FOR_UNC}_{UNCTYPE}{DIRECTION}'.format(**filler)
      variation = f.Get(varname)
      print varname, variation

      varied_obj = obj.Clone(name)
      varied_obj.Multiply(variation)
      varied_obj.SetDirectory(0)
      varied_hists[name] = varied_obj

  return varied_hists

def get_stat_variations(obj, category):
  name = obj.GetName()


  histograms = {}
  if any([x in name for x in ['scalar','pseudo','lq','axial','vector','add','S3D','vbf','ggh','zh','wh','ggzh','svj']]):
    return {}

  for ibin in range(1,obj.GetNbinsX()+1):
    variation_name_up =  "{NAME}_{category}_stat_bin{ibin}Up".format(category=category,NAME=name, ibin=ibin)
    variation_name_dn =  "{NAME}_{category}_stat_bin{ibin}Down".format(category=category,NAME=name, ibin=ibin)
    name_up = "{NAME}_{VARIATION}".format(NAME=name, VARIATION=variation_name_up)
    name_dn = "{NAME}_{VARIATION}".format(NAME=name, VARIATION=variation_name_dn)

    central = obj.GetBinContent(ibin)
    error = obj.GetBinError(ibin)
    if central <= 0:
      continue
    if error <= 5e-3:
      continue
    if error / central <= 5e-3:
      continue
    error = max(1e-3,abs(obj.GetBinError(ibin)))

    h_up = obj.Clone(name_up)
    h_up.SetBinContent(ibin, max(0, central+error))
    histograms[name_up] = h_up
    h_dn = obj.Clone(name_dn)
    if central > 0:
      h_dn.SetBinContent(ibin, max(0,central-error))
    else:
      # If central value is 0, we make
      # both sides of the nuisance go the
      # same direction
      h_dn.SetBinContent(ibin, max(0,central+error))
    histograms[name_dn] = h_dn
  return histograms

'''
Add a list of histograms into a new histogram with name new_name
the '+' operator uses ROOT.TH1.Add

'list_of_histograms' : [list of histograms to be added togather]
'new_name' : string
'''
def add_histograms(list_of_histograms, new_name):
    new_obj = list_of_histograms[0].Clone(new_name)
    if len(list_of_histograms)>1:
      for obj in list_of_histograms[1:]:
          new_obj = new_obj + obj
    return new_obj

'''
Create "autoMCstats"-like per-bin stat variations for multiple processes

to_merge_mc_bkgs = {
    'region1' : [list of per-process histograms to be considered],
    'region2' : [...]
}
'''
def get_mergedMC_stat_variations(to_merge_mc_bkgs, category):
  histograms = {}
  for region_name in to_merge_mc_bkgs.keys():
    merged_name = str(region_name) + "_mergedMCBkg"
    merged_obj = add_histograms(to_merge_mc_bkgs[region_name], merged_name)
    for ibin in range(1,merged_obj.GetNbinsX()+1):
      variation_name_up =  "{MERGED_NAME}_{category}_stat_bin{ibin}Up".format(  category=category, MERGED_NAME=merged_name, ibin=ibin)
      variation_name_dn =  "{MERGED_NAME}_{category}_stat_bin{ibin}Down".format(category=category, MERGED_NAME=merged_name, ibin=ibin)
      merged_central = merged_obj.GetBinContent(ibin)
      merged_error = merged_obj.GetBinError(ibin)
      if merged_central<=0:
          continue
      merged_ratio_up = 1.0 + merged_error/merged_central
      merged_ratio_dn = max(0, 1.0 - merged_error/merged_central)

      for obj in to_merge_mc_bkgs[region_name]:
        name = obj.GetName()
        name_up = "{NAME}_{VARIATION}".format(NAME=name, VARIATION=variation_name_up)
        name_dn = "{NAME}_{VARIATION}".format(NAME=name, VARIATION=variation_name_dn)

        central = obj.GetBinContent(ibin)
        h_up = obj.Clone(name_up)
        h_up.SetBinContent(ibin, max(0, central*merged_ratio_up))
        histograms[name_up] = h_up
        h_dn = obj.Clone(name_dn)
        h_dn.SetBinContent(ibin, max(0, central*merged_ratio_dn))
        histograms[name_dn] = h_dn
  return histograms

from utils.mistag import determine_region_wp, mistag_scale_and_flip
from W_constraints import scale_variation_histogram


def mistag_processes(name):
  processes = []
  if name.endswith("wjets") or name.startswith("Wen") or name.startswith("Wmn"):
    processes.append('w')
  if name.startswith('signal') or name.startswith("Zmm") or name.startswith("Zee") or name.endswith("zll"):
    processes.append('z')
  if 'gjets' in name:
    processes.append('g')
  return processes

def get_mistag_variations(obj, category):
  name = obj.GetName()
  histograms = {}
  region_wp = determine_region_wp(category)
  year = extract_year(category)
  channel = extract_channel(category)
  f = ROOT.TFile("sys/mistag_sf_variations.root")

  for sf_wp in 'loose','tight':
    scale, flip = mistag_scale_and_flip(sf_wp, region_wp)
    if scale == 0:
      continue
    if flip:
      scale = - scale
    for variation_index in range(2):

      for proc in mistag_processes(name):
        filler = {
          "YEAR":year,
          "PROC":proc,
          "SF_WP":sf_wp,
          "INDEX":variation_index,
          "CHANNEL":channel
        }

        variation_name = "CMS_eff{YEAR}_vmistag_{PROC}_stat_{SF_WP}_{INDEX}".format(**filler)
        for direction in 'up','down':
          var = f.Get('{PROC}_{SF_WP}_{YEAR}_{CHANNEL}_var{INDEX}_{DIRECTION}'.format(DIRECTION=direction, **filler))
          var = scale_variation_histogram(var, scale)
          varied_name = '{NAME}_{VARIATION}{DIRECTION}'.format(NAME=name, VARIATION=variation_name, DIRECTION=direction.capitalize())
          h_var = obj.Clone(varied_name)
          h_var.Multiply(var)
          h_var.SetDirectory(0)
          histograms[varied_name] = h_var


  return histograms

def treat_empty(obj):
  # Ensure non-zero integral for combine
  if not obj.Integral() > 0:
    obj.SetBinContent(1,0.0001)


def treat_overflow(obj):
  # Add overflow to last bin
  overflow        = obj.GetBinContent(obj.GetNbinsX()+1)
  overflow_err    = obj.GetBinError(obj.GetNbinsX()+1)
  lastbin         = obj.GetBinContent(obj.GetNbinsX())
  lastbin_err     = obj.GetBinError(obj.GetNbinsX())
  new_lastbin     = overflow + lastbin
  new_lastbin_err = sqrt(overflow_err**2 + lastbin_err**2)

  obj.SetBinContent(obj.GetNbinsX(), new_lastbin)
  obj.SetBinError(obj.GetNbinsX(), new_lastbin_err)
  obj.SetBinContent(obj.GetNbinsX()+1, 0)
  obj.SetBinError(obj.GetNbinsX()+1, 0)

def create_workspace(fin, fout, category, args):
  '''Create workspace and write the relevant histograms in it for the given category, returns the workspace.'''
  if args.indir:
    if args.indir=='.':
      fdir = fin
    else:
      fdir = fin.Get(args.indir)
  else:
    fdir = fin.Get("category_"+category)
  foutdir = fout.mkdir("category_"+category)
  # Get the relevant JES source file for the given category
  f_jes = get_jes_file(category)

  wsin_combine = ROOT.RooWorkspace("wspace_"+category,"wspace_"+category)
  wsin_combine._import = SafeWorkspaceImporter(wsin_combine)

  if args.standalone:
    variable_name = ("mjj_{0}" if ("vbf" in category) else "met_{0}").format(category)
  else:
    variable_name = "mjj" if ("vbf" in category) else "met"
  varl = ROOT.RooRealVar(variable_name, variable_name, 0,100000);

  # Helper function
  def write_obj(obj, name):
    '''Converts histogram to RooDataHist and writes to workspace + ROOT file'''
    print "Creating Data Hist for ", name
    dhist = ROOT.RooDataHist(
                          name,
                          "DataSet - %s, %s"%(category,name),
                          ROOT.RooArgList(varl),
                          obj
                          )
    wsin_combine._import(dhist)

    # Write the individual histograms
    # for easy transfer factor calculation
    # later on
    obj.SetDirectory(0)
    foutdir.cd()
    foutdir.WriteTObject(obj)

  # Helper function
  def write_dict(variation_dict):
    for k, v in variation_dict.items():
      if not v:
        raise RuntimeError("Could not write histogram for key: " + k)
      write_obj(v, k)

  # Loop over all keys in the input file
  # pick out the histograms, and add to
  # the work space.
  keys_local = fdir.GetListOfKeys()
  to_merge_mc_bkgs = defaultdict(list)
  for key in keys_local:
    obj = key.ReadObj()
    if type(obj) not in [ROOT.TH1D, ROOT.TH1F]:
      continue
    name = obj.GetName()

    treat_empty(obj)
    treat_overflow(obj)
    write_obj(obj, name)

    if not 'data' in name:
      # JES variations: Get them from the source file and save them to workspace
      jes_varied_hists = get_jes_variations(obj, f_jes, category)
      write_dict(jes_varied_hists)

      # Diboson variations
      vvprocs = ['wz','ww','zz','zgamma','wgamma']
      process = "_".join(key.GetName().split("_")[1:])
      if process in vvprocs:
        diboson_varied_hists = get_diboson_variations(obj, category, process)
        write_dict(diboson_varied_hists)

      if 'gjets' in key.GetName():
        photon_id_varied_hists = get_photon_id_variations(obj, category)
        write_dict(photon_id_varied_hists)

      if key.GetName() == 'gjets_qcd':
        photon_qcd_varied_hists = get_photon_qcd_variations(obj, category)
        write_dict(photon_qcd_varied_hists)

      # mistag variations
      mistag_varied_hists = get_mistag_variations(obj, category)
      write_dict(mistag_varied_hists)
      # Signal theory variations
      signal_theory_varied_hists = get_signal_theory_variations(obj, category)
      write_dict(signal_theory_varied_hists)

      # MC stat
      if is_MC_bkg(name):
        # for MC-based background, merge the stat unc into single nuisance
        region_name = key.GetName().split("_")[0]
        to_merge_mc_bkgs[region_name].append(obj)

  # now do the merging of MC-based bkg
  stat_varied_hists = get_mergedMC_stat_variations(to_merge_mc_bkgs, category)
  write_dict(stat_varied_hists)


  # Write the workspace
  foutdir.cd()
  foutdir.WriteTObject(wsin_combine)
  foutdir.Write()
  fout.Write()

  return wsin_combine

def main():
  # Commandline arguments
  args = cli_args()

  # Create output path
  outdir = os.path.dirname(args.out)
  if not os.path.exists(outdir):
    os.makedirs(outdir)

  fin = ROOT.TFile(args.file,'READ')
  fout = ROOT.TFile(args.out,'RECREATE')
  dummy = []
  for category in args.categories:
    wsin_combine = create_workspace(fin, fout, category, args)
    dummy.append(wsin_combine)

  # For reasons unknown, if we do not return
  # the workspace from this function, it goes
  # out of scope and segfaults.
  # ????
  # To be resolved.
  return dummy

if __name__ == "__main__":
  a = main()
