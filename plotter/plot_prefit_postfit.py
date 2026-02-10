import os
import math
import ROOT as rt  # type: ignore
from array import array
import plotter.cmsstyle as CMS
from utils.generic.logger import initialize_colorized_logger

logger = initialize_colorized_logger(log_level="INFO")


def create_ratios(h_data: rt.TH1, h_all_prefit: rt.TH1, h_all_postfit: rt.TH1) -> tuple[rt.TGraphAsymmErrors, rt.TGraphAsymmErrors, rt.TH1]:
    xval, xerr = [], []
    ratio_pre, ratio_pre_hi, ratio_pre_lo = [], [], []
    ratio_post, ratio_post_hi, ratio_post_lo = [], [], []
    ratiosys_pre = h_all_prefit.Clone()
    ratiosys_post = h_all_postfit.Clone()
    for idx in range(1, h_all_prefit.GetNbinsX() + 1):
        yield_data = h_data.GetBinContent(idx)
        yield_pre = h_all_prefit.GetBinContent(idx)
        yield_post = h_all_postfit.GetBinContent(idx)
        prefit_error = h_all_prefit.GetBinError(idx)
        postfit_error = h_all_postfit.GetBinError(idx)
        ratiosys_pre.SetBinContent(idx, 1.0)
        ratiosys_post.SetBinContent(idx, 1.0)
        xval.append(h_all_prefit.GetBinCenter(idx))
        xerr.append(h_all_prefit.GetBinWidth(idx) / 2)

        if yield_data > 0.0:
            e_data_hi = h_data.GetBinError(idx)
            e_data_lo = h_data.GetBinError(idx)
        else:
            logger.critical("Empty data bin. Is this intendend?")
            # alpha = 1 - 0.6827
            # N = yield_data
            # L = 0 if N == 0 else rt.Math.gamma_quantile(alpha / 2, N, 1.0)
            # U = rt.Math.gamma_quantile_c(alpha / 2, N + 1, 1)
            # e_data_lo = (N - L) / width
            # e_data_hi = (U - N) / width

        if yield_pre > 0.0:
            ratio_pre.append(yield_data / yield_pre)
            ratio_pre_hi.append(e_data_hi / yield_pre)
            ratio_pre_lo.append(e_data_lo / yield_pre)
        else:
            ratio_pre.append(0.0)
            ratio_pre_hi.append(0.0)
            ratio_pre_lo.append(0.0)
            logger.warning("Empty pre-fit MC bin. Is this intendend?")

        if yield_post > 0.0:
            ratio_post.append(yield_data / yield_post)
            ratio_post_hi.append(e_data_hi / yield_post)
            ratio_post_lo.append(e_data_lo / yield_post)
            ratiosys_pre.SetBinError(idx, prefit_error / yield_pre)
            ratiosys_post.SetBinError(idx, postfit_error / yield_post)
            if prefit_error / yield_pre < postfit_error / yield_post:
                logger.warning(f"Larger post-fit error for bin={idx}")
        else:
            ratio_post.append(0.0)
            ratio_post_hi.append(0.0)
            ratio_post_lo.append(0.0)
            ratiosys_pre.SetBinError(idx, 0.0)
            ratiosys_post.SetBinError(idx, 0.0)
            logger.warning("Empty post-fit MC bin. Is this intendend?")

    xval = array("d", xval)
    xerr = array("d", xerr)

    g_ratio_pre = rt.TGraphAsymmErrors(len(xval), xval, array("d", ratio_pre), xerr, xerr, array("d", ratio_pre_lo), array("d", ratio_pre_hi))
    g_ratio_post = rt.TGraphAsymmErrors(len(xval), xval, array("d", ratio_post), xerr, xerr, array("d", ratio_post_lo), array("d", ratio_post_hi))
    return g_ratio_pre, g_ratio_post, ratiosys_pre, ratiosys_post


def plot_prefit_postfit(region: str, category: str, shapes_filename: str, outdir: str, lumi: str, year: str, sb: bool = False) -> None:
    logger.debug(f"Input parameters: {locals()}")

    os.makedirs(outdir, exist_ok=True)

    f_shapes = rt.TFile(shapes_filename, "READ")

    is_SR = "signal" in region
    channel = f"{category}_{region}"

    is_mono = "mono" in category

    if is_mono:
        mainbkgs = {
            "singlemu": ["qcd_wjets"],
            "singleel": ["qcd_wjets"],
            "dimuon": ["qcd_zll"],
            "dielec": ["qcd_zll"],
            "photon": ["qcd_gjets"],
            "signal": ["qcd_zjets", "qcd_wjets"],
        }
        processes = [
            "qcd",
            "qcd_estimate",
            "qcdzll",
            "ww",
            "zz",
            "wz",
            "ewkwjets",
            "ewkzll",
            "ewkgjets",
            "ewkzjets",
            "top",
            "qcdgjets",
            "qcd_gjets",
            "qcd_wjets",
            "qcd_zjets",
            "qcd_zll",
            "wgamma",
            "zgamma",
        ]
    else:
        mainbkgs = {
            "singlemu": ["qcd_wjets", "ewk_wjets"],
            "singleel": ["qcd_wjets", "ewk_wjets"],
            "dimuon": ["qcd_zll", "ewk_zll"],
            "dielec": ["qcd_zll", "ewk_zll"],
            "photon": ["qcd_gjets", "ewk_gjets"],
            "signal": ["qcd_zjets", "ewk_zjets"],
        }
        processes = [
            "qcd",
            "qcd_zll",
            "ewkzll",
            "ewk_zll",
            "qcdzll",
            "ewk_gjets",
            "qcd_gjets",
            "top",
            "ewk_wjets",
            "qcd_wjets",
            "qcd_zjets",
            "ewk_zjets",
        ]
    colors = {
        "qcd": "#9A9EAB",
        "qcd_estimate": "#9A9EAB",
        "top": "#CF3721",
        "ww": "#2267a1",
        "wz": "#4897D8",
        "zz": "#859ade",
        "wgamma": "#4897D8",
        "zgamma": "#4897D8",
        "qcd_gjets": "#859ade",
        "qcdgjets": "#82ba34",
        "ewk_gjets": "#9A9EAB",
        "ewkgjets": "#9A9EAB",
        "qcd_zll": "#82ba34",
        "qcdzll": "#82ba34",
        "ewk_zll": "#b4c754",
        "ewkzll": "#b4c754",
        "qcd_wjets": "#feb24c",
        "ewk_wjets": "#ffeda0",
        "ewkwjets": "#ffeda0",
        "ewk_zjets": "#74c476",
        "ewkzjets": "#74c476",
        "qcd_zjets": "#00441b",
        "prefit": rt.kRed + 1,
        "postfit": rt.kAzure - 4,
    }

    binLowE = []

    # Pre/Post Fit
    prefit_dir = f"{channel}_prefit/"
    postfit_dir = f"{channel}_postfit/"

    h_data = f_shapes.Get(f"{prefit_dir}/data_obs").Clone("data_obs")

    h_prefit = {}
    h_postfit = {}
    h_all_prefit = f_shapes.Get(f"{prefit_dir}/TotalBkg").Clone("h_all_prefit")
    h_all_postfit = f_shapes.Get(f"{postfit_dir}/TotalBkg").Clone("h_all_postfit")
    h_postfit_total_sig_bkg = f_shapes.Get(f"{postfit_dir}/TotalProcs").Clone("h_postfit_total_sig_bkg")

    h_data.Scale(1, "width")
    h_all_prefit.Scale(1, "width")
    h_all_postfit.Scale(1, "width")
    h_postfit_total_sig_bkg.Scale(1, "width")

    h_other_prefit = None
    h_other_postfit = None
    h_prefit["total"] = f_shapes.Get(f"{prefit_dir}/TotalProcs").Clone("h_prefit_total")
    for i in range(1, h_prefit["total"].GetNbinsX() + 2):
        binLowE.append(h_prefit["total"].GetBinLowEdge(i))

    h_stack_postfit = rt.THStack("h_stack_postfit", "h_stack_postfit")

    for process in processes:
        h_prefit[process] = f_shapes.Get(f"{prefit_dir}/{process}")
        if not h_prefit[process]:
            continue
        h_prefit[process] = h_prefit[process].Clone(f"h_prefit_{process}")
        h_postfit[process] = f_shapes.Get(f"{postfit_dir}/{process}")
        if not h_postfit[process]:
            continue
        h_postfit[process] = h_postfit[process].Clone(f"h_postfit_{process}")
        if str(h_prefit[process].Integral()) == "nan" or str(h_postfit[process].Integral()) == "nan":
            logger.critical(f"Found process with integral==Nan: {process}", exception_cls=RuntimeError)
        h_prefit[process].SetDirectory(0)
        h_postfit[process].SetDirectory(0)
        h_prefit[process].Scale(1, "width")
        h_postfit[process].Scale(1, "width")
        color = rt.TColor.GetColor(colors[process])
        h_prefit[process].SetLineColor(color)
        h_prefit[process].SetFillColor(color)
        if process not in mainbkgs[region]:
            logger.info(f"Adding process to other bkg for {region}: {process}")
            if h_other_prefit is None:
                h_other_prefit = h_prefit[process].Clone("h_other_prefit")
                h_other_postfit = h_postfit[process].Clone("h_other_postfit")
                h_other_prefit.SetDirectory(0)
                h_other_postfit.SetDirectory(0)
            else:
                h_other_prefit.Add(h_prefit[process])
                h_other_postfit.Add(h_postfit[process])

        h_postfit[process].SetLineColor(1)
        h_postfit[process].SetFillColor(color)

        if is_SR:
            h_stack_postfit.Add(h_postfit[process])

    if h_other_prefit is None:
        h_other_prefit = h_all_prefit.Clone("h_other_prefit")
        h_other_postfit = h_all_postfit.Clone("h_other_postfit")
        h_other_prefit.SetDirectory(0)
        h_other_postfit.SetDirectory(0)
        h_other_prefit.Scale(0)
        h_other_postfit.Scale(0)

    x_min = h_all_prefit.GetBinLowEdge(1)
    x_max = h_all_prefit.GetBinLowEdge(h_all_prefit.GetNbinsX() + 1)
    is_dnn = x_max < 10
    nameXaxis = "DNN score" if is_dnn else ("Recoil [GeV]" if is_mono else "m_{jj} [GeV]")
    nameYaxis = "Events / bin" if is_dnn else "Events / GeV"
    y_up_min, y_up_max = 10 if is_dnn else 0.002, (1000 if is_dnn else 100) * h_all_prefit.GetMaximum()
    CMS.SetEnergy(13.6)
    CMS.SetLumi(lumi)
    CMS.ResetAdditionalInfo()
    CMS.AppendAdditionalInfo("mono-V" if "monov" in category else ("monojet" if is_mono else "VBF") + " cat.")
    canv = CMS.cmsTriCanvas(
        canvName="canv",
        x_min=x_min,
        x_max=x_max,
        y_up_min=y_up_min,
        y_up_max=y_up_max,
        y_mid_min=0.7,
        y_mid_max=1.5,
        y_low_min=-3.5,
        y_low_max=3.5,
        nameXaxis=nameXaxis,
        nameYaxis_up=nameYaxis,
        nameYaxis_mid="Data / Pred.",
        nameYaxis_low="#frac{(Data-Pred.)}{#sigma}",
    )
    canv.cd(1).SetLogy(True)
    canv.cd(1)

    if is_SR:
        if sb:
            CMS.cmsDraw(h_postfit_total_sig_bkg, "hist", lcolor=1, fcolor=1, fstyle=3144)
        h_stack_postfit.Draw("hist same")

    else:
        CMS.cmsDraw(h_other_prefit, "hist", lwidth=1, lcolor=1, fcolor=33)
        CMS.cmsDraw(h_all_prefit, "hist", lwidth=2, lcolor=colors["prefit"], fstyle=0)
        CMS.cmsDraw(h_all_postfit, "hist", lwidth=2, lcolor=colors["postfit"], fstyle=0)

    CMS.cmsDraw(h_data, "ep", marker=20, msize=1.2, lcolor=1)

    if region == "singlemu":
        legname = "W #rightarrow #mu#nu"
    if region == "dimuon":
        legname = "Z #rightarrow #mu#mu"
    if region == "photon":
        legname = "#gamma + jets"
    if region == "singleel":
        legname = "W #rightarrow e#nu"
    if region == "dielec":
        legname = "Z #rightarrow ee"

    n_leg_entries = (len(h_postfit) / 2 + 1) if is_SR else 6
    legend = CMS.cmsLeg(x1=0.40 if is_SR else 0.55, y1=0.89 - (n_leg_entries) * 0.05, x2=0.89, y2=0.89, textSize=0.045)
    legend.SetNColumns(2 if is_SR else 1)

    def add_entry(name, leg):
        if name in h_postfit:
            legend.AddEntry(h_postfit[name], leg, "f")

    if is_SR:
        legend.AddEntry(h_data, "Pseudo data", "elp")
        add_entry(name="qcd_zjets", leg="QCD Z(#nu#nu)")
        add_entry(name="qcd_wjets", leg="QCD W(l#nu)")
        add_entry(name="top", leg="Top quark")
        add_entry(name="qcd_gjets", leg="QCD #gamma")
        add_entry(name="qcdgjets", leg="QCD #gamma")
        add_entry(name="ewkzjets", leg="EWK Z(#nu#nu)")
        add_entry(name="ewk_zjets", leg="EWK Z(#nu#nu)")
        add_entry(name="ewkwjets", leg="EWK W(l#nu)")
        add_entry(name="ewk_wjets", leg="EWK W(l#nu)")
        add_entry(name="wz", leg="WZ")
        add_entry(name="zz", leg="ZZ")
        add_entry(name="ww", leg="WW")
        add_entry(name="qcdzll", leg="QCD Z(ll)")
        add_entry(name="qcd_estimate", leg="QCD multijet")
        add_entry(name="qcd", leg="QCD multijet")
        if sb:
            legend.AddEntry(h_postfit_total_sig_bkg, "S+B post-fit", "f")

    else:
        legend.AddEntry(h_data, "Data", "elp")
        legend.AddEntry(h_all_postfit, f"Post-fit ({legname})", "l")
        legend.AddEntry(h_all_prefit, f"Pre-fit ({legname})", "l")
        legend.AddEntry(h_other_prefit, "Other backgrounds", "f")

    g_ratio_pre, g_ratio_post, ratiosys_pre, ratiosys_post = create_ratios(h_data=h_data, h_all_prefit=h_all_prefit, h_all_postfit=h_all_postfit)

    canv.cd(2)

    ref_line = rt.TLine(x_min, 1, x_max, 1)

    CMS.cmsDraw(ratiosys_pre, "e2", msize=0, lwidth=1, lcolor=rt.kGray + 2, fcolor=rt.kGray + 2)
    CMS.cmsDraw(ratiosys_post, "e2", msize=0, lwidth=1, lcolor=rt.kGray, fcolor=rt.kGray)
    CMS.cmsDrawLine(line=ref_line, lcolor=rt.kBlack, lstyle=rt.kDashed, lwidth=2)
    CMS.cmsDraw(g_ratio_pre, "ep", marker=20, msize=1.2, mcolor=colors["prefit"], lcolor=colors["prefit"])
    CMS.cmsDraw(g_ratio_post, "ep", marker=20, msize=1.2, mcolor=colors["postfit"], lcolor=colors["postfit"])

    legend_ratio = CMS.cmsLeg(x1=0.18, y1=0.70, x2=0.89, y2=0.92, textSize=0.14)
    legend_ratio.SetNColumns(4)
    legend_ratio.AddEntry(g_ratio_pre, "Pre-fit", "ple")
    legend_ratio.AddEntry(g_ratio_post, "Post-fit", "ple")
    legend_ratio.AddEntry(ratiosys_pre, "Pre-fit unc.", "f")
    legend_ratio.AddEntry(ratiosys_post, "Post-fit unc.", "f")
    legend_ratio.Draw("same")

    canv.cd(3)
    # Compute the pulls
    data_pull = h_data.Clone("pull")
    data_pull_sig = h_data.Clone("pull")

    def get_pull(hist_1: rt.TH1, hist_2: rt.TH1, hbin: int) -> float:
        # https://twiki.cern.ch/twiki/bin/viewauth/CMS/DataMCComparison
        # formula: pull = data-pred/sigma, with
        # sigma = sqrt(sigma_data^2-sigma_fit^2)
        # sigma_data = sqrt(mc_pred) -> Poisson statistical error estimated from the MC prediction
        # sigma_fit = mc_err -> mc postfit error
        # sigma = sqrt(mc_pred-mc_err^2)
        center = hist_2.GetBinCenter(hbin)
        width = hist_1.GetBinWidth(hbin)
        data_pred = width * hist_1.GetBinContent(hbin)
        mc_pred = width * hist_2.GetBinContent(hbin)
        postfit_err = width * hist_2.GetBinError(hbin)
        sigma = mc_pred - postfit_err**2
        if sigma < 0:
            # TODO
            logger.warning(
                f"Bin {hbin} at x={center} with too large post fit errors. err_data ={math.sqrt(data_pred)}, sigma_data ={math.sqrt(mc_pred)}, sigma_fit={postfit_err}."
            )
            sigma = mc_pred + postfit_err**2
        pull = (data_pred - mc_pred) / math.sqrt(sigma)
        # TODO
        logger.debug(
            f"Bin {hbin} at x={center} with pull={pull}, sigma={math.sqrt(sigma)}, sigma_data ={math.sqrt(mc_pred)}, sigma_fit={postfit_err}, diff={data_pred - mc_pred}, data_pred={data_pred}, mc_pred={mc_pred}."
        )
        return pull

    for hbin in range(1, data_pull.GetNbinsX() + 1):
        pull = get_pull(hist_1=h_data, hist_2=h_all_postfit, hbin=hbin)
        data_pull.SetBinContent(hbin, pull)
        data_pull.SetBinError(hbin, 0)
        pull = get_pull(hist_1=h_data, hist_2=h_postfit_total_sig_bkg, hbin=hbin)
        data_pull_sig.SetBinContent(hbin, pull)
        data_pull_sig.SetBinError(hbin, 0)

    data_pull_sig.SetLineColor(2)
    data_pull_sig.SetFillColor(2)
    data_pull_sig.SetFillStyle(3004)
    data_pull_sig.SetMarkerColor(2)
    CMS.cmsDraw(data_pull, "hist", mcolor=colors["postfit"], lcolor=colors["postfit"], fcolor=colors["postfit"])

    legend_pull = CMS.cmsLeg(x1=0.18, y1=0.80, x2=0.40, y2=0.92, textSize=0.11)
    legend_pull.Draw("same")
    legend_pull.AddEntry(data_pull, "Background only", "f")

    for i in range(1, 4):
        CMS.UpdatePad(canv.cd(i))

    # for extension in ["png", "pdf", "C","root"]:
    for extension in ["pdf"]:
        canv.SaveAs(f"{outdir}/prefit_postfit_{category}_{region}_{year}.{extension}")

    canv.Close()
    f_shapes.Close()
