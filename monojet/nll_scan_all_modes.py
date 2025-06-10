import os
import subprocess
import ROOT
from multiprocessing import Pool

# -------- SETTINGS --------
WORKSPACE = "cards/card_monojet_2017.root"
FIT_FILE = "diagnostics/fitDiagnostics_monojet_2017_hesse_SRincluded.root"
MODES = ["postfit"]
POINTS = 1000
SCAN_RANGE = (-10, 10)
SKIP_NUISANCES = []
# --------------------------

def get_nuisances(workspace_file, skip_list=None):
    f = ROOT.TFile.Open(workspace_file)
    ws = f.Get("w")
    nuisances = []
    for var in ws.allVars():
        name = var.GetName()
        if var.isConstant():
            continue
        #print(f"Running {var}")
        if skip_list and name in skip_list:
            continue
        nuisances.append(name)
    return nuisances

def get_postfit_values(fit_file):
    f = ROOT.TFile.Open(fit_file)
    fit_result = f.Get("fit_s")
    values = {}
    if not fit_result:
        print("ERROR: Could not find 'fit_s' in fitDiagnostics.root")
        return values
    pars = fit_result.floatParsFinal()
    for i in range(pars.getSize()):
        p = pars.at(i)
        values[p.GetName()] = p.getVal()
    return values

def run_scan(nuisance, mode, workspace, postfit_vals=None):
    outdir = f"nllscan/{mode}"
    os.makedirs(outdir, exist_ok=True)
    set_pars = []
    freeze_pars = []

    all_nuisances = get_nuisances(workspace, skip_list=[nuisance])
    if mode == "postfit":
        for n in all_nuisances:
            if n in postfit_vals:
                set_pars.append(f"{n}={postfit_vals[n]}")
        freeze_pars = all_nuisances
    elif mode == "prefit":
        freeze_pars = all_nuisances
    elif mode == "prefit0":
        set_pars = [f"{n}=0" for n in all_nuisances]
        freeze_pars = all_nuisances

        
    cmd = [
        "combine", "-M", "MultiDimFit", workspace,
        "--redefineSignalPOIs", nuisance,
        "--algo", "grid",
        f"--setParameterRanges {nuisance}={SCAN_RANGE[0]},{SCAN_RANGE[1]}",
        f"--points {POINTS}",
        f"--name _{nuisance}_{mode}",
        f"--freezeParameters {','.join(freeze_pars)}",
        "--saveNLL",
        "--cminDefaultMinimizerStrategy 0",
        "--robustHesse 1"
    ]
    if set_pars:
        cmd.append(f"--setParameters {','.join(set_pars)}")

    #print(f"Command is {cmd}")
    print(f"Running {mode} scan for {nuisance}")
    subprocess.run(" ".join(cmd), shell=True)

    # Move result
    out_root = f"higgsCombine_{nuisance}_{mode}.MultiDimFit.mH120.root"
    if os.path.exists(out_root):
        os.rename(out_root, f"{outdir}/scan_{nuisance}.root")

def plot_scan(nuisance, mode):
    plot_cmd = (
        f"python3 ${CMSSW_BASE}/src/HiggsAnalysis/CombinedLimit/scripts/plot1DScan.py nllscan/{mode}/scan_{nuisance}.root "
        f"--POI {nuisance} "
        f"--output nllscan/{mode}/scan_{nuisance} "
        f"--main-label {mode} "
        f"--main-color {1 if mode=='prefit' else (2 if mode=='prefit0' else 4)}"
    )
    os.system(plot_cmd)
    #now copy
    #copy_cmd = (
    #    f"cp nllscan/{mode}/scan_{nuisance}*pdf nllscan/{mode}/scan_{nuisance}*png /eos/user/z/zdemirag/www/monojet/jun25_v1/nllscans/{mode}/"
    #    )
    #os.system(copy_cmd)
    
def one_scan(args):
    nuisance, mode, postfit_vals = args
    run_scan(nuisance, mode, WORKSPACE, postfit_vals if mode == "postfit" else None)
    plot_scan(nuisance, mode)

def main():
    nuisances = get_nuisances(WORKSPACE, skip_list=SKIP_NUISANCES)
    postfit_vals = get_postfit_values(FIT_FILE)

    all_tasks = [(n, m, postfit_vals) for n in nuisances for m in MODES]

    # Adjust number of processes as needed (e.g., os.cpu_count())
    with Pool(processes=10) as pool:
        pool.map(one_scan, all_tasks)
    
#def main():
#    nuisances = get_nuisances(WORKSPACE, skip_list=SKIP_NUISANCES)
#    postfit_vals = get_postfit_values(FIT_FILE)
#
#    for n in nuisances:
#        for mode in MODES:
#            run_scan(n, mode, WORKSPACE, postfit_vals if mode == "postfit" else None)
#            plot_scan(n, mode)

if __name__ == "__main__":
    main()
