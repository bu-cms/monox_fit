# ==============================
# Helper functions regarding JES/JER uncertainties
# ==============================

import ROOT as r
import re
from general import get_nuisance_name

def get_jes_variations(fjes, year, proc='qcd'):
    '''Given the JES file, get the list of JES variations.'''
    jet_variations = set()
    for key in list(fjes.GetListOfKeys()):
        if proc not in key.GetName():
            continue
        # var = re.sub("(.*qcd_|(Up|Down))","",key.GetName())
        var = get_nuisance_name(key.GetName(), year)
        if '201' in var and (str(year) not in var):
            continue
        if 'jesTotal' in var:
            continue
        jet_variations.add(var)
    
    return jet_variations

def get_jes_jer_source_file_for_tf(category):
    '''For the given analysis (monojet, mono-V or VBF), get the JES/JER uncertainty source file for transfer factors.'''
    f_jes_dict = {
        '(monoj|monov).*' : r.TFile("sys/monojet_jes_jer_tf_uncs_jer_smeared_symmetrized.root"),
        'vbf.*' : r.TFile("sys/vbf_jes_jer_tf_uncs.root")
    }
    # Determine the relevant JES/JER source file
    f_jes = None
    for regex, f in f_jes_dict.items():
        if re.match(regex, category):
            f_jes = f
    if not f_jes:
        raise RuntimeError('Could not find a JES source file for category: {}'.format(category))
    
    return f_jes    

def jes_nuisance_name(variable):
    if variable.startswith('jer'):
        return variable.replace("jer","CMS_res_j")
    if 'jes' in variable:
        return variable.replace("jes","CMS_scale_j_jes")
    else:
        raise RuntimeError("Could not derive nuisance name for variable: " + variable)