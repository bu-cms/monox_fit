import os
import ROOT as rt  # type: ignore
from collections import defaultdict
import plotter.cmsstyle as CMS
from utils.generic.general import oplus
from utils.workspace.uncertainties import get_all_flat_systematics_functions, get_veto_unc
from utils.generic.logger import initialize_colorized_logger

logger = initialize_colorized_logger(log_level="INFO")


def plot_ratio(region: str, category: str, model_filename: str, outdir: str, lumi: float, year: str) -> None:
    """Plot transfer factors and their systematic uncertainties as ratio plots."""
    logger.debug(f"Input parameters: {locals()}")

    os.makedirs(outdir, exist_ok=True)

    analysis = category.replace(f"_{year}", "")
    is_mono_category = "mono" in category
    production_modes = ["qcd"] if is_mono_category else ["qcd", "ewk"]
    tag = "mono" if is_mono_category else "vbf"

    model_file = rt.TFile.Open(model_filename, "READ")

    region_config = {
        "dimuon": {"sample": "zll", "process": "zmm", "model": "z", "label": "#mu#mu"},
        "dielec": {"sample": "zll", "process": "zee", "model": "z", "label": "ee"},
        "photon": {"sample": "gjets", "process": "photon", "model": "z", "label": "#gamma"},
        "signal": {"sample": "zjets", "process": "w", "model": "z", "label": "Z/W"},
        "singleel": {"sample": "wjets", "process": "wen", "model": "w", "label": "e#nu"},
        "singlemu": {"sample": "wjets", "process": "wmn", "model": "w", "label": "#mu#nu"},
    }
    config = region_config[region]

    for mode in production_modes:
        dirname = f"{tag}_{mode}_{config['model']}_category_{category}"
        base_name = f"{mode}_{config['process']}_weights_{category}"
        label = f"R_{{{mode}}}^{{{config['label']}}}"
        ratio = model_file.Get(f"{dirname}/{base_name}")
        subdir = model_file.Get(dirname)
        model = f"{mode}_{config['sample']}"

        flat_uncertainties = {}
        for syst_func in get_all_flat_systematics_functions():
            systematics = syst_func(year=year, analysis=analysis)
            for name, region_map in systematics.items():
                region_entry = region_map.get(region, {})
                signal_entry = region_map.get("signal", {})
                if not ("value" in region_entry or "value" in signal_entry):
                    continue
                in_region = model in region_entry.get("processes", [])
                in_signal = f"{mode}_zjets" in signal_entry.get("processes", [])
                unc = None
                if in_region and in_signal:
                    unc = region_entry["value"] / signal_entry["value"]
                elif in_signal:
                    unc = signal_entry["value"]
                elif in_region:
                    unc = region_entry["value"]
                if unc is not None:
                    flat_uncertainties[name] = unc
                    logger.info(f"Adding to exp: {name} for {region} with value = {unc}")

        for lep, unc in get_veto_unc(model=model, analysis=analysis).items():
            if unc == "shape":
                continue
            name = f"veto_{lep}"
            flat_uncertainties[name] = 1 + unc
            logger.info(f"Adding to exp: {name} for {region} with value = {unc}")

        logger.info(f"Total flat syst: {flat_uncertainties}")
        # Collect systematics
        unc_dict = defaultdict(lambda: defaultdict(float))
        for key in subdir.GetListOfKeys():
            name = key.GetName()
            if "TH1" not in key.GetClassName():
                continue
            if base_name not in name or "Up" not in name:
                continue

            up_hist = model_file.Get(f"{dirname}/{name}")
            if "stat_error" in name:
                syst = "stat"
            elif any(word in name for word in ["trig", "prefiring", "veto", "eff", "scale_j", "res_j", "photon_scale"]):
                syst = "exp"
            elif any(word in name for word in ["theory_sudakov", "theory_nnlo", "ewk", "EWK_ren_scale", "EWK_fac_scale", "EWK_pdf"]):
                syst = "ewk"
            elif any(word in name for word in ["theory", "pdf", "QCD_ren_scale", "QCD_fac_scale"]):
                syst = "qcd"
            else:
                logger.critical(f"Unrecognized variation: {name}", exception_cls=ValueError)
            logger.info(f"Adding to {syst}: {name}")
            logger.debug(f"Processing systematic '{syst}' for histogram '{name}'")

            for b in range(1, ratio.GetNbinsX() + 1):
                diff = up_hist.GetBinContent(b) - ratio.GetBinContent(b)
                unc_dict[syst][b] = oplus(unc_dict[syst][b], diff)

        # Build uncertainty bands
        bands = {
            "ewk": ratio.Clone("band_ewk"),
            "ewk_qcd": ratio.Clone("band_ewk_qcd"),
            "total": ratio.Clone("band_total"),
        }

        for b in range(1, ratio.GetNbinsX() + 1):
            stat = unc_dict["stat"][b]
            ewk = oplus(stat, unc_dict["ewk"][b])
            qcd = oplus(ewk, unc_dict["qcd"][b])
            tot = oplus(qcd, unc_dict["exp"][b], (oplus(*[x - 1 for x in flat_uncertainties.values()])) * ratio.GetBinContent(b))
            bands["ewk"].SetBinError(b, ewk)
            bands["ewk_qcd"].SetBinError(b, qcd)
            bands["total"].SetBinError(b, tot)

        CMS.SetEnergy(13.6)
        CMS.SetLumi(lumi)
        CMS.ResetAdditionalInfo()
        CMS.AppendAdditionalInfo("mono-V" if "monov" in category else ("monojet" if "mono" in category else "VBF") + " cat.")

        x_min = ratio.GetBinLowEdge(1) - ratio.GetBinWidth(1)
        x_max = ratio.GetBinLowEdge(ratio.GetNbinsX() + 1) + ratio.GetBinWidth(1)
        y_min = 0.5 * ratio.GetMinimum()
        y_max = 2.0 * ratio.GetMaximum()
        nameXaxis = "DNN score" if x_max < 10 else ("Recoil [GeV]" if "mono" in category else "m_{jj} [GeV]")

        canv = CMS.cmsCanvas(
            canvName="canv",
            x_min=x_min,
            x_max=x_max,
            y_min=y_min,
            y_max=y_max,
            nameXaxis=nameXaxis,
            nameYaxis=label,
            square=True,
            extraSpace=0.03,
            yTitOffset=1.2,
        )

        CMS.cmsDraw(bands["total"], "e2", fcolor=rt.TColor.GetColor(CMS.petroff_6[2]))
        CMS.cmsDraw(bands["ewk_qcd"], "e2", fcolor=rt.TColor.GetColor(CMS.petroff_6[1]))
        CMS.cmsDraw(bands["ewk"], "e2", fcolor=rt.TColor.GetColor(CMS.petroff_6[0]))
        CMS.cmsDraw(ratio, "", marker=20, lcolor=1, lwidth=2)

        legend = CMS.cmsLeg(x1=0.40, y1=0.89 - 5 * 0.045, x2=0.89, y2=0.89, textSize=0.045)
        legend.AddEntry(ratio, "Transfer factor", "lpe")
        legend.AddEntry(bands["ewk"], "#oplus ewk", "f")
        legend.AddEntry(bands["ewk_qcd"], "#oplus qcd", "f")
        legend.AddEntry(bands["total"], "#oplus exp.", "f")
        legend.Draw("same")

        CMS.UpdatePad(canv)

        # for extension in ["png", "pdf", "C","root"]:
        for extension in ["pdf"]:
            canv.SaveAs(f"{outdir}/rfactor_{category}_{mode}_{config['process']}_{year}.{extension}")
        canv.Close()
    model_file.Close()
