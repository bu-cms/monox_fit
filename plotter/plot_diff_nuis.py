#!/usr/bin/env python3
import os
import ROOT as rt  # type: ignore
import plotter.cmsstyle as CMS
from utils.generic.logger import initialize_colorized_logger

logger = initialize_colorized_logger(log_level="INFO")


def get_canvas(category: str, group: str) -> rt.TCanvas:
    """Create a CMS-style canvas for plotting."""
    CMS.setCMSStyle()
    CMS.cmsStyle.SetPadGridX(True)
    canv = rt.TCanvas(f"{category}_{group}", f"{category}_{group}", 800, 600)
    canv.SetFillColor(0)
    canv.SetBorderMode(0)
    canv.SetFrameFillStyle(0)
    canv.SetFrameBorderMode(0)

    canv.SetLeftMargin(0.05)
    canv.SetRightMargin(0.01)
    canv.SetTopMargin(0.06)
    canv.SetBottomMargin(0.4)
    CMS.UpdatePad(canv)
    canv.RedrawAxis()
    canv.GetFrame().Draw()
    return canv


def add_title(category: str, group: str) -> None:
    """Draw category/group title on canvas."""
    latex = rt.TLatex()
    latex.SetNDC()
    latex.SetTextFont(42)
    latex.SetTextSize(0.04)
    latex.DrawLatex(0.05, 0.95, f"Nuisances: {group} -- cat. {category.replace('_', ' ')}")


def get_validated_nuisance(fname: str) -> list[str]:
    """Return list of nuisances that exist in prefit tree."""
    file_ = rt.TFile.Open(fname.replace("diffnuisances", "fitDiagnostics"), "READ")
    prefit = file_.Get("nuisances_prefit")
    nps = file_.Get("fit_s").floatParsFinal()
    total = nps.getSize()
    valid_nps = []
    n_model_pars = 0
    for idx in range(total):
        name = nps.at(idx).GetName()
        if name == "r" or "model_mu_cat" in name:
            n_model_pars += 1
            continue
        nuisance_prefit = prefit.find(name)
        if nuisance_prefit == None:
            logger.warning(f"Null NP found: {name}")
        else:
            valid_nps.append(name)
    logger.info(f"NPs found: total={total}, not null={len(valid_nps)}, null={total - len(valid_nps)-n_model_pars}")
    file_.Close()
    return valid_nps


def validate_categories(indices_map: dict[str, dict[str, int]], nuis_names: list[str]) -> None:
    """Ensure labels are uniquely categorized and all nuisances are assigned."""
    label_to_groups = {}
    for group, labels in indices_map.items():
        for label in labels:
            label_to_groups.setdefault(label, []).append(group)

    duplicated = {l: g for l, g in label_to_groups.items() if len(g) > 1}
    if duplicated:
        logger.warning("Some labels appear in multiple categories:")
        for label, cats in duplicated.items():
            logger.warning(f"  '{label}' in categories: {cats}")
    else:
        logger.debug("No duplicated labels across categories.")

    uncategorized = [l for l in nuis_names if l not in label_to_groups]
    if uncategorized:
        logger.warning("Some nuisances are not categorized:")
        for label in uncategorized:
            logger.warning(f"  '{label}' not in any category")
    else:
        logger.debug("All labels are categorized.")


def plot_diff_nuis(diffnuis_file: str, outdir: str, category: str) -> None:
    """Plot nuisance parameter by category."""
    os.makedirs(outdir, exist_ok=True)
    if not os.path.exists(diffnuis_file):
        logger.critical(f"Input file does not exist: {diffnuis_file}", exception_cls=IOError)

    nuis_names = get_validated_nuisance(fname=diffnuis_file)

    file_ = rt.TFile(diffnuis_file)
    canvas = file_.Get("nuisances")
    nuisances = canvas.GetListOfPrimitives().FindObject("prefit_nuisancs")

    categories = {
        "exp": lambda l: any(k in l for k in ("CMS_", "lumi", "trigger", "prefiring", "pu", "qcd_closure", "syst", "qcdfit", "gamma_norm")),
        "theory": lambda l: any(k in l for k in ("QCDscale", "pdf", "top_pt_reweighting", "UEPS", "Norm", "theory", "ewkqcd")),
        "nlo": lambda l: "ewk_vbf" in l,
        "singlemuon": lambda l: "stat_error" in l and "singlemuon" in l,
        "singleelectron": lambda l: "stat_error" in l and "singleelectron" in l,
        "photonCR": lambda l: "stat_error" in l and "photonCR" in l,
        "dimuonCR": lambda l: "stat_error" in l and "dimuonCR" in l,
        "dielectronCR": lambda l: "stat_error" in l and "dielectronCR" in l,
        "zCR": lambda l: "stat_error" in l and "zCR" in l,
        "mcstat": lambda l: "mergedMCBkg" in l,
    }

    indices_map = {name: {} for name in categories}

    for name, match_fn in categories.items():
        for idx in range(nuisances.GetNbinsX() + 1):
            label = nuisances.GetXaxis().GetBinLabel(idx)
            if match_fn(label):
                indices_map[name][label] = idx

    validate_categories(indices_map=indices_map, nuis_names=nuis_names)

    graph_bonly_all, graphs_sb_all = None, None
    for item in canvas.GetListOfPrimitives():
        title = item.GetTitle()
        if title == "fit_b_g":
            graph_bonly_all = item.Clone("fit_bonly")
        if title == "fit_b_s":
            graphs_sb_all = item.Clone("fit_sb")

    for group, label_idx in indices_map.items():
        num_nuis = len(label_idx)
        if not num_nuis:
            continue
        canv = get_canvas(category=category, group=group)
        h_axis = rt.TH1F(f"h_axis_{group}", "", num_nuis, 0, num_nuis)
        h_prefit_err = rt.TH1F(f"prefit_{group}", "", num_nuis, 0, num_nuis)
        gr_bonly, gr_sb = rt.TGraphAsymmErrors(), rt.TGraphAsymmErrors()
        y_bonly = list(graph_bonly_all.GetY())
        ere_up_bonly = list(graph_bonly_all.GetEYhigh())
        err_dn_bonly = list(graph_bonly_all.GetEYlow())
        y_sb = list(graphs_sb_all.GetY())
        ere_up_sb = list(graphs_sb_all.GetEYhigh())
        err_dn_sb = list(graphs_sb_all.GetEYlow())
        for h_idx, (np_name, np_idx) in enumerate(sorted(label_idx.items())):
            h_axis.GetXaxis().SetBinLabel(h_idx + 1, np_name)
            h_prefit_err.SetBinContent(h_idx + 1, nuisances.GetBinContent(np_idx))
            h_prefit_err.SetBinError(h_idx + 1, nuisances.GetBinError(np_idx))
            x = h_idx + 0.5
            gr_bonly.SetPoint(h_idx, x - 0.1, y_bonly[np_idx - 1])
            gr_bonly.SetPointError(h_idx, 0, 0, ere_up_bonly[np_idx - 1], err_dn_bonly[np_idx - 1])
            gr_sb.SetPoint(h_idx, x + 0.1, y_sb[np_idx - 1])
            gr_sb.SetPointError(h_idx, 0, 0, ere_up_sb[np_idx - 1], err_dn_sb[np_idx - 1])

        h_axis.LabelsOption("v")
        h_axis.GetXaxis().SetLabelSize(0.03)
        h_axis.GetYaxis().SetLabelOffset(0.01)
        h_axis.SetMinimum(-3)
        h_axis.SetMaximum(3)
        h_axis.Draw("AXIS")
        add_title(category=category, group=group)
        ref_line = rt.TLine(0, 0, num_nuis, 0)
        CMS.cmsDraw(h_prefit_err, "e2", marker=0, fcolor=rt.kGray, lwidth=0)
        CMS.cmsDrawLine(line=ref_line, lcolor=rt.kBlack, lstyle=rt.kSolid, lwidth=2)
        CMS.cmsDraw(gr_bonly, "ep", lcolor=rt.kBlue, mcolor=rt.kBlue, marker=20, lwidth=2)
        CMS.cmsDraw(gr_sb, "ep", lcolor=rt.kRed, mcolor=rt.kRed, marker=20, lwidth=2)
        leg = CMS.cmsLeg(x1=0.55, y1=0.94, x2=0.98, y2=1.0, textSize=0.05)
        leg.SetNColumns(3)
        leg.AddEntry(h_prefit_err, "Prefit", "FL")
        leg.AddEntry(gr_bonly, "B-only fit", "EPL")
        leg.AddEntry(gr_sb, "S+B fit", "EPL")
        leg.Draw("same")
        CMS.UpdatePad(canv)
        canv.RedrawAxis("g")
        canv.SaveAs(os.path.join(outdir, f"diffnuis_{category}_{group}.pdf"))

    file_.Close()
