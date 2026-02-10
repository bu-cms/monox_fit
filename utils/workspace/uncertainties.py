from typing import Any, Optional, Union
from functools import partial
from collections.abc import Callable

from utils.workspace.processes import get_processes, get_all_regions, get_processes_by_region


def get_shape_systematic_sources(category: str) -> list[str]:
    """Return the list of shape-related systematic uncertainty sources."""
    analysis, year = category.split("_")
    sources = {
        "monojet": {
            "Run3": ["jecs", "btag", "prefiring_jet", "pdf_scale", "id_shapes", "diboson_unc", "qcd_estimate_closure"],
        },
    }
    return sources[analysis][year]


def get_all_shapes_functions() -> list[Callable[[str, str], dict[str, Any]]]:
    shapes = [
        get_jec_shape,
        get_objects_shape_unc,
        get_prefiring_shape,
        get_qcd_estimate_shape,
        get_purity_shape,
        get_higgs_theory_shape_unc,
        get_pdf_scale_shape_unc,
        get_diboson_shape,
    ]
    return shapes


def get_all_flat_systematics_functions() -> list[Callable[[str, str], dict[str, Any]]]:
    shapes = [
        get_pu_lumi_unc,
        get_objects_eff_unc,
        get_trigger_unc,
        get_theory_unc,
        get_higgs_theory_unc,
        get_misc_unc,
    ]
    return shapes


def get_generic_shape(
    systematics: list[str],
    analysis: str,
    regions: Optional[list[str]] = [],
    processes: Callable[[str], list[str]] = None,
) -> dict[str, dict[str, Any]]:
    """Return a generic shape for a list of systematics for a given year and analysis."""
    regions = regions or get_all_regions()
    processes = processes or partial(get_processes_by_region, analysis=analysis, types=["signals", "backgrounds"])
    results = {syst: {region: {"value": 1.0, "processes": processes(region=region)} for region in regions} for syst in systematics}
    return results


def get_veto_unc(model: str, analysis: str) -> dict[str, Union[float, str]]:
    systematics = {
        "vbf": {  # TODO for run3
            "qcd_zjets": {"t": -0.01, "m": -0.015, "e": -0.03},
            "qcd_wjets": {"t": 0.01, "m": 0.015, "e": 0.03},
            "ewk_zjets": {"t": -0.01, "m": -0.02, "e": -0.03},
            "ewk_wjets": {"t": 0.01, "m": 0.02, "e": 0.03},
        },
        "monojet": {
            "qcd_zjets": {"t": "shape", "m": 0.0001, "e": 0.006},  # TODO is this correct?
            "qcd_wjets": {"t": "shape", "m": -0.0001, "e": -0.006},
        },
    }[analysis]
    return systematics[model] if model in systematics else {}


def get_pu_lumi_unc(year: str, analysis: str) -> dict[str, Any]:
    """Return pileup and luminosity lnN systematics for a given year and analysis."""
    _ = analysis  # Currently unused
    types = ["signals", "backgrounds"]
    systematics = {
        "Run3": {
            "lumi_13p6TeV": {
                region: {"value": 1.014, "processes": get_processes_by_region(analysis=analysis, region=region, types=types)} for region in get_all_regions()
            },
            "CMS_pileup_13p6TeV": {
                region: {"value": 1.01, "processes": get_processes_by_region(analysis=analysis, region=region, types=types)} for region in get_all_regions()
            },
        },
    }
    return systematics[year]


def get_objects_eff_unc(year: str, analysis: str) -> dict[str, Any]:
    """Return lepton and photon efficiency lnN systematics for a given year and analysis."""
    _ = analysis  # Currently unused

    # Run-dependent efficiencies
    m_id_eff = {"Run3": -0.004}[year]
    m_iso_eff = {"Run3": -0.005}[year]
    m_reco_eff = {"Run3": 0.01}[year]  # TODO update for run3
    e_reco_eff = {"Run3": 0.01}[year]  # TODO update for run3

    results = {}

    lepton_unc = {
        # f"CMS_eff_e_reco_{year}": {"dielec": 2 * e_reco_eff, "singleel": e_reco_eff},
        f"CMS_eff_m_id_{year}": {"dimuon": 2 * m_id_eff, "singlemu": m_id_eff},
        f"CMS_eff_m_iso_{year}": {"dimuon": 2 * m_iso_eff, "singlemu": m_iso_eff},
        # f"CMS_eff_m_reco_{year}": {"dimuon": 2 * m_reco_eff, "singlemu": m_reco_eff},
    }

    for name, entries in lepton_unc.items():
        results[name] = {
            region: {"value": 1 + value, "processes": get_processes_by_region(analysis=analysis, region=region)} for region, value in entries.items()
        }

    return results


def get_trigger_unc(year: str, analysis: str) -> dict[str, Any]:
    """Return trigger-related lnN systematics for a given year and analysis."""
    _ = analysis  # Currently unused
    # All processes
    proc_list = partial(get_processes_by_region, analysis=analysis, types=["signals", "backgrounds", "models"])
    return {
        "Run3": {
            f"CMS_eff_g_trigger_{year}": {
                "photon": {"value": 0.99, "processes": proc_list(region="photon")},
            },
            f"CMS_eff_e_trigger_{year}": {
                "dielec": {"value": 0.99, "processes": proc_list(region="dielec")},
                "singleel": {"value": 0.99, "processes": proc_list(region="singleel")},
            },
            f"CMS_eff_met_trigger_{year}": {
                "dielec": {"value": 1.01, "processes": proc_list(region="dielec")},
                "singleel": {"value": 1.01, "processes": proc_list(region="singleel")},
                "photon": {"value": 1.01, "processes": proc_list(region="photon")},
            },
        },
    }[year]


def get_theory_unc(year: str, analysis: str) -> dict[str, Any]:
    """Return QCD scale lnN systematics for a given year and analysis."""
    _ = analysis  # Currently unused
    # merging all theory norm into a single parameter. Having them split is useful only when combining with other analyses/channels.
    sample_map = {
        "Run3": {
            "qcdzll": {"Norm_Z": 1.10},  # "QCDscale_ren_Z": 0.97, "QCDscale_fac_Z": 0.94, "pdf_Z": 1.06},
            "qcdwjet": {"Norm_W": 1.10},  # "QCDscale_ren_W": 0.95, "QCDscale_fac_W": 0.93, "pdf_W": 1.05},
            "qcdgjets": {"Norm_G": 1.10},  # "QCDscale_ren_G": 0.92, "QCDscale_fac_G": 0.97, "pdf_G": 1.05},
            "wz": {"Norm_WZ": 1.20},  # "QCDscale_ren_WZ": 1.10, "QCDscale_fac_WZ": 1.10, "pdf_WZ": 1.10},
            "zz": {"Norm_ZZ": 1.20},  # "QCDscale_ren_ZZ": 1.10, "QCDscale_fac_ZZ": 1.10, "pdf_ZZ": 1.10},
            "ww": {"Norm_WW": 1.20},  # "QCDscale_ren_WW": 1.10, "QCDscale_fac_WW": 1.10, "pdf_WW": 1.10},
            "wgamma": {"Norm_Wgamma": 1.10},  # "QCDscale_ren_Wgamma": 1.05, "QCDscale_fac_Wgamma": 1.02, "pdf_Wgamma": 1.02},
            "zgamma": {"Norm_Zgamma": 1.10},  # "QCDscale_ren_Zgamma": 1.05, "QCDscale_fac_Zgamma": 1.02, "pdf_Zgamma": 1.02},
            "top": {"Norm_ttbar": 1.15},  # "QCDscale_ren_ttbar": 0.90, "QCDscale_fac_ttbar": 0.95, "pdf_ttbar": 1.03},
            "ewkzll": {"Norm_ewkZ": 1.10},  # "QCDscale_ren_ewkZ": 0.95, "QCDscale_fac_ewkZ": 0.95, "pdf_ewkZ": 1.05},
            "ewkzjets": {"Norm_ewkZ": 1.10},  # "QCDscale_ren_ewkZ": 0.95, "QCDscale_fac_ewkZ": 0.95, "pdf_ewkZ": 1.05},
            "ewkwjets": {"Norm_ewkW": 1.10},  # "QCDscale_ren_ewkW": 0.95, "QCDscale_fac_ewkW": 0.95, "pdf_ewkW": 1.05},
            "ewkgjets": {"Norm_ewkG": 1.10},  # "QCDscale_ren_ewkG": 0.95, "QCDscale_fac_ewkG": 0.95, "pdf_ewkG": 1.05},
        }
    }
    systematics = {}
    for sample, variations in sample_map[year].items():
        for var, value in variations.items():
            systematics[var] = {"value": value, "processes": [sample]}
    systematics.update(
        {
            "Norm_QCD_multijet": {
                "singleel": {"value": 1.75, "processes": ["qcd"]},
                "singlemu": {"value": 1.50, "processes": ["qcd"]},
            }
        }
    )
    return systematics


def get_misc_unc(year: str, analysis: str) -> dict[str, Any]:
    """Return miscellaneous lnN systematics for a given year and analysis."""
    _ = analysis  # Currently unused
    return {
        "Run3": {
            "top_pt_reweighting": {"value": 1.1, "processes": ["top"]},
            # "UEPS": {"value": 1.168, "processes": ["ggh"]},  # TODO only for VBF?
            f"monojet_{year}_purity_closure": {"photon": {"value": 1.25, "processes": ["qcd_estimate"]}},
            f"monojet_{year}_qcd_closure": {"signal": {"value": 1.25, "processes": ["qcd_estimate"]}},
        },
    }[year]


def get_higgs_theory_unc(year: str, analysis: str) -> dict[str, Any]:
    """Return lnN Higgs related systematics for a given year and analysis."""
    _ = analysis  # Currently unused
    return {
        "Run3": {
            "QCDscale_ggH": {"value": (1.046, 0.933), "processes": ["ggh"]},  # YR checked
            "QCDscale_qqH": {"value": (1.005, 0.997), "processes": ["vbf"]},  # YR checked
            "QCDscale_wh": {"value": (1.004, 0.993), "processes": ["wh"]},  # YR checked
            "QCDscale_zh": {"value": (1.037, 0.968), "processes": ["zh"]},  # YR checked
            "QCDscale_ggzh": {"value": (1.251, 0.811), "processes": ["ggzh"]},  # Copied from Run2, No 13.6 TeV
            "pdf_ggH": {"value": 1.032, "processes": ["ggh"]},  # YR checked
            "pdf_qqH": {"value": 1.021, "processes": ["vbf"]},  # YR checked
            "pdf_wh": {"value": 1.019, "processes": ["wh"]},  # Copied from Run2, No 13.6 TeV
            "pdf_zh": {"value": (1.016, 0.987), "processes": ["zh"]},  # Copied from Run2, No 13.6 TeV # TODO was symmetric for VBF
            "pdf_ggzh": {"value": (1.024, 0.982), "processes": ["ggzh"]},  # Copied from Run2, No 13.6 TeV
        },
    }[year]


def get_higgs_theory_shape_unc(year: str, analysis: str) -> dict[str, Any]:
    """Return lnN Higgs related systematics for a given year and analysis."""
    _ = year
    regions = ["signal"]
    sources = ["QCDscale_ren", "QCDscale_fac", "pdf"]
    syst_map = {
        "ggh": [f"{source}_ggH_ACCEPT" for source in sources],
        "vbf": [f"{source}_qqH_ACCEPT" for source in sources],
    }
    systematics = {}
    for proc, theory_unc in syst_map.items():
        systematics.update(get_generic_shape(systematics=theory_unc, analysis=analysis, regions=regions, processes=lambda region: {proc}))
    return systematics


def get_pdf_scale_shape_unc(year: str, analysis: str) -> dict[str, Any]:
    """Return theory shape unc for minor backgrounds for a given year and analysis."""
    _ = year
    sources = ["QCDscale_ren", "QCDscale_fac", "pdf"]
    systematics = get_generic_shape(
        systematics=[f"{source}_minor_ACCEPT" for source in sources],
        analysis=analysis,
        processes=partial(get_processes_by_region, analysis=analysis, types=["backgrounds"]),
    )
    return systematics


def get_id_variations_names(year: str) -> list[str]:
    """Get the list of lepton id variations."""
    _ = year
    var_names = [
        "CMS_eff_e_id",
        "CMS_eff_e_id_high_pt",
        "CMS_eff_g_id_high_pt",
    ]
    return var_names


def get_btag_variations_names(year: str) -> list[str]:
    """Get the list of btag variations."""
    _ = year
    btag_names = [
        "CMS_btag_fixedWP_light_correlated",
        f"CMS_btag_fixedWP_light_uncorrelated_{year}",
        "CMS_btag_fixedWP_bc_correlated",
        f"CMS_btag_fixedWP_bc_uncorrelated_{year}",
    ]
    if year == "Run3":
        btag_src = []
        for y in ["2022", "2022EE", "2023", "2023BPix"]:
            btag_src += get_btag_variations_names(year=y)
        btag_names = list(sorted(set(btag_src)))
    return btag_names


def get_objects_shape_unc(year: str, analysis: str) -> dict[str, Any]:
    """Return lepton and photon efficiency lnN systematics for a given year and analysis."""
    _ = analysis  # Currently unused
    results = get_generic_shape(systematics=get_btag_variations_names(year=year), analysis=analysis)
    systematics = get_id_variations_names(year=year)
    for syst in systematics:
        regions = ["dielec", "singleel"] if "e_id" in syst else ["photon"]
        results.update(get_generic_shape(systematics=[syst], analysis=analysis, regions=regions))
    return results


def get_jes_variations_names(year: str) -> list[str]:
    """Get the list of JES variations."""
    jes_names = [
        f"CMS_res_j_{year}",
        "CMS_scale_j_Absolute",
        f"CMS_scale_j_Absolute_{year}",
        "CMS_scale_j_BBEC1",
        f"CMS_scale_j_BBEC1_{year}",
        "CMS_scale_j_EC2",
        f"CMS_scale_j_EC2_{year}",
        "CMS_scale_j_FlavorQCD",
        "CMS_scale_j_HF",
        f"CMS_scale_j_HF_{year}",
        "CMS_scale_j_RelativeBal",
        f"CMS_scale_j_RelativeSample_{year}",
    ]
    if year == "Run3":
        jec_src = []
        for y in ["2022", "2022EE", "2023", "2023BPix"]:
            jec_src += get_jes_variations_names(year=y)
        jes_names = list(sorted(set(jec_src)))
    return jes_names


def get_jec_shape(year: str, analysis: str) -> dict[str, dict[str, Any]]:
    """Return JER and JES shape systematics for a given year and analysis."""
    jecs = get_jes_variations_names(year=year)
    return get_generic_shape(systematics=jecs, analysis=analysis)


def get_prefiring_shape(year: str, analysis: str) -> dict[str, Any]:
    """Return prefiring shape systematics for a given year and analysis."""
    systematics = {
        "vbf": {"Run3": {}},
        "monojet": {"Run3": get_generic_shape(systematics=["prefiring_jet"], analysis=analysis)},
    }
    return systematics[analysis][year]


def get_qcd_variations_names() -> list[str]:
    """Get the list of QCD variations."""
    qcd_names = [
        "syst_binning1",
        "syst_binning2",
        "syst_extrap1",
        "syst_extrap2",
    ]
    return qcd_names


def get_qcd_estimate_shape(year: str, analysis: str) -> dict[str, Any]:
    """Return prefiring shape systematics for a given year and analysis."""
    systematics = {
        "vbf": {"Run3": {}},
        "monojet": {
            "Run3": {
                f"{analysis}_{year}_{syst}": {
                    "signal": {"value": 1.0, "processes": get_processes_by_region(analysis=analysis, region="signal", types=["data_driven"])}
                }
                for syst in get_qcd_variations_names()
            },
        },
    }
    return systematics[analysis][year]


def get_diboson_shape(year: str, analysis: str) -> dict[str, Any]:
    """Return prefiring shape systematics for a given year and analysis."""
    systematics = {
        "vbf": {"Run3": {}},
        "monojet": {
            "Run3": {f"{vv}_ewkqcd_mix": {region: {"value": 1.0, "processes": [vv]} for region in get_all_regions()} for vv in ["wz", "zz", "ww"]}
            | {f"{vv}_ewkqcd_mix": {"photon": {"value": 1.0, "processes": [vv]}} for vv in ["wgamma", "zgamma"]}
        },
    }
    return systematics[analysis][year]


def get_purity_shape(year: str, analysis: str) -> dict[str, Any]:
    """Return purity shape systematics for a given year and analysis."""
    systematics = {
        "vbf": {"Run3": {}},
        "monojet": {"Run3": {f"purity_fit_{year}": {"photon": {"value": 1.0, "processes": ["qcd_estimate"]}}}},
    }
    return systematics[analysis][year]


def get_automc_stat(year: str, analysis: str, n_bins: int) -> dict[str, dict[str, Any]]:
    """Return autoMC stat shapes for minor backgrounds for a given year and analysis."""

    automc_shape = {
        f"{region}_mergedMCBkg_{analysis}_{year}_stat_bin{idx}": {
            region: {"value": 1.0, "processes": get_processes_by_region(analysis=analysis, region=region, types=["backgrounds"])},
        }
        for region in get_all_regions()
        for idx in range(n_bins)
    }
    return automc_shape


if __name__ == "__main__":
    year = "Run3"
    analysis = "monojet"
    models = {proc for region in get_all_regions() for proc in get_processes(analysis=analysis, region=region, type="models")}

    def get_process_list(list_of_procs, is_models=False):
        processes = ["multijet" if proc == "qcd" else proc for proc in list_of_procs]
        if is_models:
            processes = list(filter(lambda x: x in models, processes))
        else:
            processes = list(filter(lambda x: x not in models, processes))
        # import pdb

        # pdb.set_trace()
        processes = [proc.replace("qcd_", "").replace("qcd", "") for proc in processes]
        processes = [proc.replace("_", r"\_") for proc in processes]
        processes = list(sorted(processes))
        groups = {
            "diboson": ["ww", "wz", "zz"],
            "vgamma": ["wgamma", "zgamma"],
            "signals": ["zh", "wh", "vbf", "ggzh", "ggh"],
        }
        for group_name, components in groups.items():
            if all(proc in processes for proc in components):
                processes = [p for p in processes if p not in components]
                processes.append(group_name)
        processes = [
            proc.replace("ggh", "ggH")
            .replace("wh", "\\WH")
            .replace("zh", "\\ZH")
            .replace("ww", "\\WW")
            .replace("zz", "\\ZZ")
            .replace("wz", "\\WZ")
            .replace("vgamma", "\\Vgamma")
            .replace("zgamma", "\\Zgamma")
            .replace("wgamma", "\\Wgamma")
            for proc in processes
        ]
        return processes

    def get_value(value):
        text = ""
        if isinstance(value, float):
            text = "shape" if value == 1 else f"{100.0 * (float(value) - 1):.1f}\%"
        elif isinstance(value, tuple):
            text = f"{100.0 * (float(value[0]) - 1):.1f}/{100.0 * (float(value[1]) - 1):.1f}\%"
        else:
            import pdb

            pdb.set_trace()
        return text

    def get_uncertainties(grouped, is_models=False):
        for unc_name, entry in uncertainties.items():
            unc_name = unc_name.replace("_", "\_")
            if "value" in entry and "processes" in entry:
                processes = get_process_list(list_of_procs=entry["processes"], is_models=is_models)
                if not processes:
                    continue
                value = get_value(entry["value"])
                grouped.setdefault(unc_name, []).append(("All", value, ", ".join(processes)))
            else:
                for reg, info in entry.items():
                    processes = get_process_list(list_of_procs=info["processes"], is_models=is_models)
                    if not processes:
                        continue
                    processes = ", ".join(sorted(processes)) if processes else "All"
                    value = get_value(info["value"])
                    grouped.setdefault(unc_name, []).append((reg, value, processes))

    def print_table(grouped: dict) -> None:
        # Print LaTeX table
        print("\\begin{table}[htbp] \n\\centering")
        print(f"\\topcaption{{Summary systematic uncertainties applied lnN variations.}}")
        print("\\begin{tabular}{l c l l}\nUncertainty name & Uncertainty & Region & Processes \\\ \n\\hline\\hline")
        for unc_name, rows in sorted(grouped.items()):
            nrows = len(rows)
            for i, (reg, value, procs) in enumerate(rows):
                if nrows == 1:
                    unc_col = unc_name
                else:
                    unc_col = f"\\multirow{{{nrows}}}{{*}}{{{unc_name}}}" if i == 0 else ""
                reg = (
                    reg.replace("dielec", "\\twoEleCR")
                    .replace("dimuon", "\\twoMuoCR")
                    .replace("signal", "SR")
                    .replace("singleel", "\\oneEleCR")
                    .replace("singlemu", "\\oneMuoCR")
                    .replace("photon", "\\onePhoCR")
                )
                print(f"{unc_col} & {value} & {reg} & {procs} \\\\")
            print("\\hline")
        print("\\end{tabular} \n\\label{tab:sf_systematics} \n\\end{table}")

    grouped = {}

    for unc_func in get_all_flat_systematics_functions() + get_all_shapes_functions():
        if unc_func in [get_pu_lumi_unc, get_theory_unc, get_higgs_theory_unc, get_misc_unc, get_prefiring_shape]:
            continue
        uncertainties = unc_func(year=year, analysis=analysis)
        get_uncertainties(grouped=grouped, is_models=True)
    print_table(grouped)

    for unc_func in get_all_flat_systematics_functions() + get_all_shapes_functions():
        if unc_func in [get_higgs_theory_shape_unc, get_higgs_theory_unc, get_pdf_scale_shape_unc, get_theory_unc]:
            continue
        uncertainties = unc_func(year=year, analysis=analysis)
        # get_uncertainties(grouped=grouped, is_models=False)
    # print_table(grouped)

    for unc_func in [get_pdf_scale_shape_unc, get_theory_unc]:
        uncertainties = unc_func(year=year, analysis=analysis)
        # get_uncertainties(grouped=grouped, is_models=False)
    # print_table(grouped)

    for unc_func in [get_higgs_theory_unc, get_higgs_theory_shape_unc]:
        uncertainties = unc_func(year=year, analysis=analysis)
        # get_uncertainties(grouped=grouped, is_models=False)
    # print_table(grouped)
