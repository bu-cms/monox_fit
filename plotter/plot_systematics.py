import os
import argparse
import ROOT as rt  # type: ignore
from collections import defaultdict
import plotter.cmsstyle as CMS
from utils.generic.general import oplus
from utils.workspace.uncertainties import get_all_flat_systematics_functions
from utils.generic.logger import initialize_colorized_logger

logger = initialize_colorized_logger(log_level="INFO")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate standard plots for a given analysis channel.")
    parser.add_argument("--channel", default="monojet", help="Analysis channel name (e.g. vbf, monojet)")
    parser.add_argument("--year", default="Run3", choices=["2017", "2018", "Run3"], help="Dataset year (default: Run3)")
    return parser.parse_args()


def plot_systematics(inputdir: str, outdir: str, canvas_name: str, filename: str, hist_names: list[str]) -> None:
    """Plot transfer factors and their systematic uncertainties as ratio plots."""
    logger.debug(f"Input parameters: {locals()}")

    os.makedirs(outdir, exist_ok=True)

    syst_file = rt.TFile.Open(f"{inputdir}/{filename}.root", "READ")

    hists = {}
    y_min = 10
    y_max = 0
    for hname in hist_names:
        for variation in ["Up", "Down"]:
            name = f"{hname}{variation}"
            hist = syst_file.Get(name)
            hist.SetDirectory(0)
            hists[name] = hist
            y_min = min(y_min, hist.GetMinimum())
            y_max = max(y_max, hist.GetMaximum())

    CMS.SetEnergy(13.6)
    CMS.SetLumi("")
    href = list(hists.values())[0]
    x_min = href.GetBinLowEdge(1) - href.GetBinWidth(1)
    x_max = href.GetBinLowEdge(href.GetNbinsX() + 1) + href.GetBinWidth(1)
    y_min = 1 + 1.2 * (y_min - 1)
    y_max = 1 + 2 * (y_max - 1)
    nameXaxis = "Recoil [GeV]"
    canv = CMS.cmsCanvas(
        canvName=canvas_name,
        x_min=x_min,
        x_max=x_max,
        y_min=y_min,
        y_max=y_max,
        nameXaxis=nameXaxis,
        nameYaxis="Variation",
        square=True,
        extraSpace=0.05,
        yTitOffset=1.5,
    )

    legend = CMS.cmsLeg(x1=0.40, y1=0.89 - 0.045 * len(hists) / 2, x2=0.89, y2=0.89, textSize=0.045)

    renaming = [
        ("d2kappa_z", "Z nnlo missing"),
        ("d2kappa_w", "W nnlo missing"),
        ("d2kappa_g", "#gamma nnlo missing"),
        ("d1kappa", "sudakov ewk"),
        ("d3kappa_z", "Z sudakov missing"),
        ("d3kappa_w", "W sudakov missing"),
        ("d3kappa_g", "#gamma sudakov missing"),
        ("d1k", "qcd scale"),
        ("d2k", "qcd shape"),
        ("d3k", "qcd process"),
        ("mix", "qcd-ewk mix"),
    ]
    for idx, (hname, hist) in enumerate(hists.items()):
        is_up = hname.endswith("Up")
        color = CMS.cms_colors_ordered[idx // 2]
        CMS.cmsDraw(hist, "hist", lcolor=color, lwidth=2, lstyle=rt.kSolid if is_up else rt.kDashed, fstyle=0)
        if is_up:
            legname = hname
            for old, new in renaming:
                legname = legname.replace(old, new)
            legname = legname.replace("_mix", "").replace("monojet_", "")
            legname = legname.replace("z_over_z_", "Z(#nu#nu)/Z(#mu#mu) ").replace("w_over_w_", "W(l#nu)/W(#mu#nu) ")
            legname = legname.replace("z_over_w_", "Z/W ").replace("z_over_g_", "Z/#gamma ")

            if "missing" in legname:
                legname = legname.replace("Z/W ", "").replace("Z/#gamma ", "")
            legname = legname.replace("Up", "").replace("_", " ")
            legend.AddEntry(hist, legname, "l")

    CMS.UpdatePad(canv)
    canv.SaveAs(f"{outdir}/{canvas_name}.pdf")
    canv.Close()

    syst_file.Close()


def main():
    args = parse_args()
    base_path = f"inputs/sys/recoil/{args.channel}_{args.year}"
    outdir = f"{base_path}/pdf"
    info_map = {
        "diboson_unc": {
            "filename": "shapes_diboson_unc",
            "hist_names": ["zz_ewkqcd_mix", "wz_ewkqcd_mix", "ww_ewkqcd_mix", "wgamma_ewkqcd_mix", "zgamma_ewkqcd_mix"],
        },
        "theory_unc_qcd_scale_shape_w": {
            "filename": "systematics_vjets_theory",
            "hist_names": [f"monojet_z_over_w_{var}" for var in ["d1k", "d2k", "d3k", "mix"]],
        },
        "theory_unc_qcd_scale_shape_g": {
            "filename": "systematics_vjets_theory",
            "hist_names": [f"monojet_z_over_g_{var}" for var in ["d1k", "d2k", "d3k", "mix"]],
        },
        "theory_unc_sudakov": {
            "filename": "systematics_vjets_theory",
            "hist_names": [f"{args.channel}_{var}" for var in ["z_over_w_d3kappa_z", "z_over_w_d3kappa_w", "z_over_g_d3kappa_g"]],
        },
        "theory_unc_sudakov_ewk": {
            "filename": "systematics_vjets_theory",
            "hist_names": [f"{args.channel}_z_over_{proc}_d1kappa" for proc in ["w", "g"]],
        },
        "theory_unc_nnlomiss": {
            "filename": "systematics_vjets_theory",
            "hist_names": [f"{args.channel}_{var}" for var in ["z_over_w_d2kappa_z", "z_over_w_d2kappa_w", "z_over_g_d2kappa_g"]],
        },
        "theory_unc_pdf": {"filename": "systematics_pdf_ratios", "hist_names": ["z_over_z_pdf", "w_over_w_pdf", "z_over_w_pdf", "z_over_g_pdf"]},
        "met_trigger_sys": {"filename": "systematics_trigger_met_muondep", "hist_names": ["met_trigger_sys"]},
    }
    for canvas_name, info in info_map.items():
        plot_systematics(inputdir=base_path, outdir=outdir, canvas_name=canvas_name, **info)


if __name__ == "__main__":
    main()
