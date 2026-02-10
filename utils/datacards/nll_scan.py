#!/usr/bin/env python3
"""Run 1D NLL scans for nuisance parameters and plot results."""

import os
import argparse
from typing import Any, Optional
import ROOT as rt  # type: ignore
from utils.generic.colors import prettydict
from utils.generic.logger import initialize_colorized_logger
from utils.generic.parallelize import parallelize


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run 1D NLL scans for nuisance parameters and plot results.")
    parser.add_argument("--channel", required=True, help="Analysis channel (e.g. vbf, monojet).")
    parser.add_argument("--year", default="Run3", choices=["2017", "2018", "Run3"], help="Dataset year (default: Run3).")
    parser.add_argument("--ncores", type=int, default=64, help="Parallel cores for command execution.")
    parser.add_argument("--points", type=int, default=200, help="Number of grid points for scans.")
    parser.add_argument("--mode", choices=["postfit"], default="postfit", help="Scan mode (only 'postfit' slice supported).")
    return parser.parse_args()


def _get_model_config(ws: rt.RooWorkspace) -> Any:
    """Return the ModelConfig from the workspace 'w'."""
    mc = ws.obj("ModelConfig")
    if not mc:
        logger.critical("ModelConfig not found in workspace 'w'.", exception_cls=RuntimeError)
    return mc


def get_pois(snapshot_filename: str) -> list[str]:
    """Return list of POI names from ModelConfig."""
    ws_file = rt.TFile.Open(snapshot_filename)
    ws: rt.RooWorkspace = ws_file.Get("w")
    mc = _get_model_config(ws)
    pois = [p.GetName() for p in mc.GetParametersOfInterest()]
    ws_file.Close()
    logger.info(f"POIs: {pois}")
    return pois


def get_nuisances(snapshot_filename: str, skip_nuisances: Optional[list[str]] = None) -> list[str]:
    """Return list of nuisance parameter names from ModelConfig, excluding any in skip_nuisances."""
    skip_nuisances = skip_nuisances or []
    ws_file = rt.TFile.Open(snapshot_filename)
    ws: rt.RooWorkspace = ws_file.Get("w")
    mc = _get_model_config(ws)
    nuisances = [n.GetName() for n in mc.GetNuisanceParameters() if n.GetName() not in skip_nuisances]
    ws_file.Close()
    logger.info(f"Extracted {len(nuisances)} nuisance parameters from ModelConfig")
    return nuisances


def get_postfit_values(diag_filename: str, postfit_dir: str = "fit_b") -> dict[str, float]:
    """Extract post-fit parameter values from a FitDiagnostics ROOT file."""
    diag_file = rt.TFile.Open(diag_filename)
    fit_result = diag_file.Get(postfit_dir)
    if not fit_result:
        logger.critical(f"Could not find '{postfit_dir}' in {diag_filename}", exception_cls=ValueError)
    values: dict[str, float] = {p.GetName(): (p.getVal(), p.getError()) for p in fit_result.floatParsFinal()}
    diag_file.Close()

    prettydict(values)
    logger.info(f"Extracted {len(values)} post-fit values from '{postfit_dir}'")
    return values


def ensure_snapshot(workspace_filename: str, outdir: str, category: str) -> str:
    """Ensure a file with the MultiDimFit snapshot exists, or create it."""
    snapshot_name = f"higgsCombine_snapshot_{category}.MultiDimFit.mH120.root"
    snapshot_filename = os.path.join(outdir, snapshot_name)

    if os.path.exists(snapshot_filename):
        logger.info(f"Reusing existing snapshot: {snapshot_filename}")
        return snapshot_filename

    cmd = [
        "combine -M MultiDimFit",
        workspace_filename,
        "--algo none",
        "--saveWorkspace",
        "--saveFitResult",
        f"--name _snapshot_{category}",
        "--cminDefaultMinimizerStrategy 0",
        "--robustHesse 1",
        "--rMin -100 --rMax 100",
    ]
    cmd = " ".join(cmd)
    logger.info(f"Creating post-fit snapshot (category={category})")
    logger.info(f"Executing: {cmd}")
    os.system(cmd)
    if not os.path.exists(snapshot_name):
        logger.critical(f"Snapshot creation failed for {snapshot_name}; check combine output.", exception_cls=RuntimeError)

    os.system(f"mv {snapshot_name} {snapshot_filename}")
    return snapshot_filename


def scan_tag(nuisance: str, mode: str) -> str:
    """Return a consistent suffix for outputs."""
    return f"_{nuisance}_{mode}"


def build_single_scan_command(
    nuisance: str,
    mode: str,
    snapshot_filename: str,
    nuisances: list[str],
    points: int,
    postfit_vals: Optional[dict[str, float]] = None,
    pois: Optional[list[str]] = None,
) -> str:
    """Build the shell command to run a 1D MultiDimFit scan (slice) for one NP."""
    if mode != "postfit":
        logger.critical(f"Unsupported mode '{mode}'.", exception_cls=ValueError)

    pois = pois or []
    others = [n for n in nuisances if n != nuisance]
    freeze_pars = others + pois  # freeze all but the scanned nuisance (includes r)

    # Range: symmetric default; if postfit known, center around it
    scan_range = (-3.0, 3.0)
    if postfit_vals and nuisance in postfit_vals:
        val, err = postfit_vals[nuisance]
        span = 3.0 * err  # allow up to ±3err around the postfit value
        scan_range = (val - span, val + span)

    cmd = [
        "combine -M MultiDimFit",
        snapshot_filename,
        "--snapshotName MultiDimFit",  # load the global post-fit point
        "--algo grid",
        f"--points {points}",
        f"-P {nuisance}",  # scan this nuisance (constraint stays active)
        f"--setParameterRanges {nuisance}={scan_range[0]},{scan_range[1]}",
        f"--name {scan_tag(nuisance=nuisance, mode=mode)}",
        "--saveNLL",
        "--cminDefaultMinimizerStrategy 0",
        "--robustHesse 1",
        "--X-rtd FAST_VERTICAL_MORPH",
    ]

    # We rely on the snapshot for values; just freeze others.
    if freeze_pars:
        cmd += ["--freezeParameters", ",".join(freeze_pars)]

    cmd = " ".join(cmd)
    logger.debug(f"[scan] {nuisance} ({mode}) -> {cmd}")
    return cmd


def run_all_scans(
    nuisances: list[str],
    snapshot_filename: str,
    postfit_vals: dict[str, float],
    pois: list[str],
    args: argparse.Namespace,
) -> None:
    """Run all scans."""
    scan_cmds = [
        build_single_scan_command(
            nuisance=nuisance,
            mode=args.mode,
            snapshot_filename=snapshot_filename,
            nuisances=nuisances,
            points=args.points,
            postfit_vals=postfit_vals,
            pois=pois,
        )
        for nuisance in nuisances
    ]

    logger.debug(scan_cmds[0])
    parallelize(commands=scan_cmds, ncores=args.ncores, remove_temp_files=False)


def build_single_plot_command(outdir: str, nuisance: str, mode: str) -> str:
    """Build the shell command to plot a 1D scan."""
    filename = f"higgsCombine{scan_tag(nuisance=nuisance, mode=mode)}.MultiDimFit.mH120.root"
    plot_name = f"{outdir}/scan{scan_tag(nuisance=nuisance, mode=mode)}"

    if os.path.exists(filename):
        os.system(f"mv {filename} {outdir}")

    plot_script = f"{str(os.environ.get('CMSSW_BASE'))}/src/HiggsAnalysis/CombinedLimit/scripts/plot1DScan.py"
    cmd = [
        "python3",
        plot_script,
        f"{outdir}/{filename}",
        f"--POI {nuisance}",
        f"--output {plot_name}",
    ]
    cmd = " ".join(cmd)
    logger.debug(f"[plot] {nuisance} ({mode}) -> {cmd}")
    return cmd


def plot_scans(outdir: str, nuisances: list[str], args: argparse.Namespace) -> None:
    """Plot all nuisance scans."""
    plot_cmds = [
        build_single_plot_command(
            outdir=outdir,
            nuisance=nuisance,
            mode=args.mode,
        )
        for nuisance in nuisances
    ]

    logger.debug(plot_cmds[0])
    parallelize(commands=plot_cmds, ncores=args.ncores)


def cleanup() -> None:
    """Remove temporary files created during scanning and plotting."""
    cleanup_patterns = [
        "parallelize*txt",
        "combine_logger.out",
        "robustHesse_*.root",
        "multidimfit_snapshot_*.root",
    ]
    for pattern in cleanup_patterns:
        os.system(f"rm -f {pattern}")


def main() -> None:
    """Run NP scans and plot results."""
    args = parse_args()
    category = f"{args.channel}_{args.year}"
    diag_filename = f"diagnostics/fitDiagnostics_{category}.root"
    workspace_filename = f"cards/card_{category}.root"
    outdir = f"./nllscan/{args.year}/{args.mode}"
    os.makedirs(outdir, exist_ok=True)

    # Create or reuse post-fit snapshot workspace
    snapshot_filename = ensure_snapshot(workspace_filename=workspace_filename, outdir=outdir, category=category)

    # Get POIs/NPs/post-fit values from the snapshot workspace
    skip_nuisances = [f"recoil_{category}"]
    pois = get_pois(snapshot_filename=snapshot_filename)
    nuisances = get_nuisances(snapshot_filename=snapshot_filename, skip_nuisances=skip_nuisances)
    postfit_vals = get_postfit_values(diag_filename=diag_filename) if args.mode == "postfit" else {}

    # Run scans
    run_all_scans(nuisances=nuisances, snapshot_filename=snapshot_filename, postfit_vals=postfit_vals, pois=pois, args=args)

    # Plot scans
    plot_scans(outdir=outdir, nuisances=nuisances, args=args)

    # Cleanup
    cleanup()


if __name__ == "__main__":
    log_level = "INFO"
    # log_level = "DEBUG"
    logger = initialize_colorized_logger(log_level=log_level)
    main()
