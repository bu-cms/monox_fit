import os
import ROOT as rt  # type:ignore
import plotter.cmsstyle as CMS
from utils.generic.logger import initialize_colorized_logger

logger = initialize_colorized_logger(log_level="INFO")


def get_label_name(region1: str, region2: str) -> str:
    """Return the formatted label for the given region comparison."""
    label_map: dict[str, str] = {
        "combined": "Z #rightarrow ll",
        "combinedW": "W #rightarrow l#nu",
        "photon": "#gamma",
        "dielec": "Z #rightarrow ee",
        "dimuon": "Z #rightarrow #mu#mu",
        "singleel": "W #rightarrow e#nu",
        "singlemu": "W #rightarrow #mu#nu",
    }
    if region1 not in label_map:
        logger.critical(f"No label defined for {region1}", exception_cls=ValueError)
    if region2 not in label_map:
        logger.critical(f"No label defined for {region2}", exception_cls=ValueError)
    return f"{label_map[region1]} / {label_map[region2]}"


def get_regions(region: str) -> tuple[list[str], str]:
    if region == "combined":
        return ["dimuon", "dielec"]
    elif region == "combinedW":
        return ["singlemu", "singleel"]
    else:
        return [region]


def add_histograms(hists: list[rt.TH1]) -> rt.TH1:
    """Sum the histograms of a given process over multiple regions."""
    tot_hist = hists[0].Clone()
    for h in hists[1:]:
        tot_hist.Add(h)
    tot_hist.SetDirectory(0)
    return tot_hist


def get_data(region1: str, region2: str, shapes_filename: str, category: str) -> rt.TH1:
    """Return the data histogram ratio: region1 / region2."""
    f_shapes = rt.TFile.Open(shapes_filename, "READ")

    def retrieve(region: str) -> rt.TH1:
        if region == "combined":
            labels = ["dimuon", "dielec"]
        elif region == "combinedW":
            labels = ["singlemu", "singleel"]
        else:
            labels = [region]
        hists = [f_shapes.Get(f"{category}_{r}_prefit/data_obs").Clone() for r in labels]

        hist = add_histograms(hists=hists)
        return hist

    ratio = retrieve(region1)
    den = retrieve(region2)
    ratio.Divide(den)
    f_shapes.Close()
    return ratio


def get_pre_postfit_histograms(region1: str, region2: str, shapes_filename: str, category: str, shape: str) -> dict[str, rt.TH1]:
    fitdiag_file = rt.TFile.Open(shapes_filename, "READ")

    def get_shape(region: str, process: str) -> rt.TH1:
        """Retrieve a pre/postfit histogram from the diagnostics file for a given region and process."""
        path = f"{category}_{region}_{shape}/{process}"
        hist = fitdiag_file.Get(path)
        if not hist:
            logger.critical(f"Histogram not found at path: {path}", exception_cls=RuntimeError)
        hist.SetDirectory(0)
        return hist

    h_shapes = {}
    # Read pre/postfit histogram
    for region in [region1, region2]:
        h_shapes[region] = add_histograms(hists=[get_shape(region=r, process="TotalBkg") for r in get_regions(region)])
    fitdiag_file.Close()
    return h_shapes


def plot_data_validation(region1: str, region2: str, category: str, shapes_filename: str, outdir: str, lumi: float, year: str) -> None:
    """Compare data and MC prediction between two regions with pre/postfit uncertainties."""
    logger.debug(f"Input parameters: {locals()}")
    os.makedirs(outdir, exist_ok=True)

    # Retrieve histograms. This is to show the input to the workspace
    h_data = get_data(region1=region1, region2=region2, shapes_filename=shapes_filename, category=category)

    # Compute MC ratio histogram. This is to show the total syst as seen by combine
    h_prefit = get_pre_postfit_histograms(region1=region1, region2=region2, shapes_filename=shapes_filename, category=category, shape="prefit")
    h_mc = h_prefit[region1].Clone()
    h_mc.Divide(h_prefit[region2])
    h_tot_error_prefit = h_mc.Clone("h_tot_error_prefit")

    h_postfit = get_pre_postfit_histograms(region1=region1, region2=region2, shapes_filename=shapes_filename, category=category, shape="postfit")
    h_mc_postfit = h_postfit[region1].Clone()
    h_mc_postfit.Divide(h_postfit[region2])
    h_tot_error_postfit = h_mc_postfit.Clone("h_tot_error_postfit")

    # Canvas setup
    CMS.SetEnergy(13.6)
    CMS.SetLumi(lumi)
    CMS.ResetAdditionalInfo()
    category_label = "mono-V" if "monov" in category else ("monojet" if "mono" in category else "VBF")
    CMS.AppendAdditionalInfo(f"{category_label} cat.")

    x_min = h_mc.GetBinLowEdge(1) - h_mc.GetBinWidth(1)
    x_max = h_mc.GetBinLowEdge(h_mc.GetNbinsX() + 1) + h_mc.GetBinWidth(1)
    name_x_axis = "DNN score" if x_max < 10 else ("Recoil [GeV]" if "mono" in category else "m_{jj} [GeV]")

    canv = CMS.cmsDiCanvas(
        canvName="canv",
        x_min=x_min,
        x_max=x_max,
        y_min=0,
        y_max=2.0 * h_mc.GetMaximum(),
        r_min=0.7,
        r_max=1.3,
        nameXaxis=name_x_axis,
        nameYaxis=get_label_name(region1=region1, region2=region2),
        nameRatio="Data / Pred.",
        extraSpace=0.08,
    )

    # Upper pad: draw main distributions
    canv.cd(1)
    color_data, color_mc = rt.kBlack, CMS.cms_color_map["LightGray"]
    color_prefit, color_postfit = CMS.cms_color_map["SteelBlue"], CMS.cms_color_map["ForestGreen"]

    CMS.cmsDraw(h_tot_error_prefit, "e2", msize=0, lwidth=2, lcolor=color_prefit, fcolor=color_prefit)
    CMS.cmsDraw(h_tot_error_postfit, "e2", marker=0, lwidth=2, lcolor=color_postfit, fcolor=color_postfit, alpha=0.8)
    CMS.cmsDraw(h_mc, "hist", msize=0, lwidth=2, lcolor=color_mc, fstyle=0)
    CMS.cmsDraw(h_data, "Pe", marker=20, lwidth=2, lcolor=color_data)

    h_mc_leg = h_mc.Clone("h_mc_leg")
    h_mc_leg.SetLineColor(rt.kGray + 1)

    # Add legend
    legend = CMS.cmsLeg(x1=0.50, y1=0.89 - 5 * 0.05, x2=0.89, y2=0.89, textSize=0.05)
    legend.AddEntry(h_data, "Data", "lep")
    legend.AddEntry(h_mc_leg, "MC pre-fit", "l")
    legend.AddEntry(h_tot_error_prefit, "Total pre-fit unc.", "f")
    legend.AddEntry(h_tot_error_postfit, "Total post-fit unc.", "f")
    legend.Draw("same")

    # Lower pad: ratio plot
    canv.cd(2)
    ratio = h_data.Clone("ratio")
    ratio_post = h_tot_error_postfit.Clone("ratio_post")
    ratio_pre = h_tot_error_prefit.Clone("ratio_pre")
    for bin in range(1, ratio.GetNbinsX() + 1):
        den = h_mc.GetBinContent(bin)
        ratio.SetBinContent(bin, ratio.GetBinContent(bin) / den)
        ratio.SetBinError(bin, ratio.GetBinError(bin) / den)
        ratio_pre.SetBinContent(bin, ratio_pre.GetBinContent(bin) / den)
        ratio_pre.SetBinError(bin, ratio_pre.GetBinError(bin) / den)
        ratio_post.SetBinContent(bin, ratio_post.GetBinContent(bin) / den)
        ratio_post.SetBinError(bin, ratio_post.GetBinError(bin) / den)

    ref_line = rt.TLine(x_min, 1, x_max, 1)
    CMS.cmsDraw(ratio_pre, "e2", msize=0, lwidth=2, lcolor=color_prefit, fcolor=color_prefit)
    CMS.cmsDraw(ratio_post, "e2", msize=0, lwidth=2, lcolor=color_postfit, fcolor=color_postfit, alpha=0.8)
    CMS.cmsDrawLine(line=ref_line, lcolor=rt.kBlack, lstyle=rt.kDashed, lwidth=2)
    CMS.cmsDraw(ratio, "Pe", marker=20, lwidth=2, lcolor=color_data)

    CMS.UpdatePad(canv.cd(1))
    CMS.UpdatePad(canv.cd(2))

    # for extension in ["png", "pdf", "C","root"]:
    for extension in ["pdf"]:
        canv.SaveAs(f"{outdir}/ratio_{category}_{region1}_{region2}_{year}.{extension}")
    canv.Close()
