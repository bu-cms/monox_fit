#!/usr/bin/env python

import argparse
import os
import re
from math import sqrt

import ROOT
from HiggsAnalysis.CombinedLimit.ModelTools import *

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
  for ibin in range(1,obj.GetNbinsX()+1):
    variation_name_up =  "{NAME}_{category}_stat_bin{ibin}Up".format(category=category,NAME=name, ibin=ibin)
    variation_name_dn =  "{NAME}_{category}_stat_bin{ibin}Down".format(category=category,NAME=name, ibin=ibin)
    name_up = "{NAME}_{VARIATION}".format(NAME=name, VARIATION=variation_name_up)
    name_dn = "{NAME}_{VARIATION}".format(NAME=name, VARIATION=variation_name_dn)

    central = obj.GetBinContent(ibin)
    error = obj.GetBinError(ibin)

    h_up = obj.Clone(name_up)
    h_up.SetBinContent(ibin, central+error)
    histograms[name_up] = h_up
    h_dn = obj.Clone(name_dn)
    h_dn.SetBinContent(ibin, central-error)
    histograms[name_dn] = h_dn
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
  for key in keys_local:
    obj = key.ReadObj()
    if type(obj) not in [ROOT.TH1D, ROOT.TH1F]:
      continue
    title = obj.GetTitle()
    name = obj.GetName()

    if any([x in name for x in ['scalar','pseudo','lq','axial','vector','add']]):
      continue

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

      # Signal theory variations
      signal_theory_varied_hists = get_signal_theory_variations(obj, category)
      write_dict(signal_theory_varied_hists)

      stat_varied_hists = get_stat_variations(obj, category)
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
