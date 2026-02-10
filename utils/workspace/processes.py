from typing import Any


def get_processes(analysis: str, region: str, type: str) -> list[str]:
    """Return the list of processes for a given analysis, region, and type."""
    processes = {
        "vbf": {
            "signal": {
                "signals": ["zh", "wh", "vbf", "ggh", "ggzh"],
                "models": ["qcd_zjets", "qcd_wjets", "ewk_zjets", "ewk_wjets"],
                "backgrounds": ["qcdzll", "top", "wz", "zz", "ww"],
            },
            "dimuon": {
                "models": ["qcd_zll", "ewk_zll"],
                "backgrounds": ["top", "wz", "zz", "ww"],
            },
            "dielec": {
                "models": ["qcd_zll", "ewk_zll"],
                "backgrounds": ["top", "wz", "zz", "ww"],
            },
            "singlemu": {
                "models": ["qcd_wjets", "ewk_wjets"],
                "backgrounds": ["qcdzll", "ewkzll", "top", "wz", "zz", "ww"],
            },
            "singleel": {
                "models": ["qcd_wjets", "ewk_wjets"],
                "backgrounds": ["qcdzll", "qcdgjets", "ewkzll", "top", "wz", "zz", "ww"],
            },
            "photon": {
                "models": ["qcd_gjets", "ewk_gjets"],
            },
        },
        "monojet": {
            "signal": {
                "signals": ["zh", "wh", "vbf", "ggh", "ggzh"],
                "models": ["qcd_zjets", "qcd_wjets"],
                "backgrounds": ["top", "qcdgjets", "wz", "zz", "ww", "ewkzjets", "ewkwjets"],
                "data_driven": ["qcd_estimate"],
            },
            "dimuon": {
                "models": ["qcd_zll"],
                "backgrounds": ["top", "wz", "zz", "ww", "ewkzll"],
            },
            "dielec": {
                "models": ["qcd_zll"],
                "backgrounds": ["top", "wz", "zz", "ww", "ewkzll"],
            },
            "singlemu": {
                "models": ["qcd_wjets"],
                "backgrounds": ["qcdzll", "top", "wz", "zz", "ww", "qcd", "ewkwjets"],
            },
            "singleel": {
                "models": ["qcd_wjets"],
                "backgrounds": ["qcdzll", "qcdgjets", "top", "wz", "zz", "ww", "qcd", "ewkwjets"],
            },
            "photon": {
                "models": ["qcd_gjets"],
                "backgrounds": ["wgamma", "zgamma", "ewkgjets"],
                "data_driven": ["qcd_estimate"],
            },
        },
    }

    return processes.get(analysis, {}).get(region, {}).get(type, [])


def get_all_regions() -> list[str]:
    return [region for region, _ in get_region_label_map()]


def get_region_label_map() -> list[tuple[str, str]]:
    return [
        ("signal", "signal"),
        ("singlemu", "Wmn"),
        ("singleel", "Wen"),
        ("dimuon", "Zmm"),
        ("dielec", "Zee"),
        ("photon", "gjets"),
    ]


def get_process_model_map(region: str) -> dict[str, dict[str, str]]:
    return {
        "dielec": {
            "ewk_zll": "ewk_dielectron_ewk_zjets",
            "qcd_zll": "qcd_dielectron_qcd_zjets",
        },
        "dimuon": {
            "ewk_zll": "ewk_dimuon_ewk_zjets",
            "qcd_zll": "qcd_dimuon_qcd_zjets",
        },
        "signal": {
            "ewk_wjets": "ewk_wjetssignal_ewk_zjets",
            "ewk_zjets": "ewkqcd_signal_qcd_zjets",
            "qcd_wjets": "qcd_wjetssignal_qcd_zjets",
            "qcd_zjets": "signal_qcd_zjets",
        },
        "singleel": {
            "ewk_wjets": "ewk_singleelectron_ewk_wjets",
            "qcd_wjets": "qcd_singleelectron_qcd_wjets",
        },
        "singlemu": {
            "ewk_wjets": "ewk_singlemuon_ewk_wjets",
            "qcd_wjets": "qcd_singlemuon_qcd_wjets",
        },
        "photon": {
            "ewk_gjets": "ewk_photon_ewk_zjets",
            "qcd_gjets": "qcd_photon_qcd_zjets",
        },
    }[region]


def get_processes_by_region(analysis: str, region: str, types: list[str] = ["backgrounds", "models"]) -> set[str]:
    """Return the set of all processes of the given types used in all regions of the given analysis."""
    return {proc for category in types for proc in get_processes(analysis=analysis, region=region, type=category)}


if __name__ == "__main__":
    year = "Run3"
    analysis = "monojet"

    groups = {
        "vv": ["ww", "wz", "zz"],
        "vgamma": ["wgamma", "zgamma"],
    }

    def _latex_region_label(reg: str) -> str:
        return (
            reg.replace("dielec", "\\twoEleCR")
            .replace("dimuon", "\\twoMuoCR")
            .replace("signal", "SR")
            .replace("singleel", "\\oneEleCR")
            .replace("singlemu", "\\oneMuoCR")
            .replace("photon", "\\onePhoCR")
        )

    def _apply_grouping_and_labels(processes: list[str]) -> list[str]:
        """Group components, remove grouped items, apply LaTeX labels."""
        processes = processes.copy()

        # Grouping
        for group_name, components in groups.items():
            if all(c in processes for c in components):
                seen = False
                new_list = []
                for p in processes:
                    if p in components:
                        if not seen:
                            new_list.append(group_name)
                            seen = True
                    else:
                        new_list.append(p)
                processes = new_list

        # LaTeX replacements
        replacements = {
            "ggh": "ggH",
            "wh": "\\WH",
            "zh": "\\ZH",
            "ggzh": "ggZH",
            "ww": "\\WW",
            "zz": "\\ZZ",
            "wz": "\\WZ",
            "vv": "\\VV",
            "vgamma": "\\Vgamma",
            "zgamma": "\\Zgamma",
            "wgamma": "\\Wgamma",
            "qcd_estimate": "qcd",
            "ewk": "EWK ",
            "qcd_": " ",
            "zll": "\\Zll",
            "zjets": "\\Znn",
            "wjets": "\\Wjets",
            "gjets": "\\Gjets",
        }
        out = []
        for p in processes:
            for old, new in replacements.items():
                p = p.replace(old, new)
            out.append(p)
        return out

    def _chunk(items: list[str]) -> list[list[str]]:
        """Return each item as its own chunk; empty list => [['-']]."""
        if not items:
            return [["-"]]
        return [[item] for item in items]

    def build_region_matrix(analysis: str) -> list[dict]:
        """Return list of dicts with region and categorized processes."""
        rows = []
        for reg in get_all_regions():
            row = {"region": _latex_region_label(reg)}
            for cat in ["models", "backgrounds", "data_driven", "signals"]:
                row[cat] = [", ".join(c) for c in _chunk(_apply_grouping_and_labels(get_processes(analysis, reg, cat)))]
            rows.append(row)
        return rows

    def print_region_table(analysis: str) -> None:
        rows = build_region_matrix(analysis)
        print("\\begin{table}[htbp]")
        print("\\centering")
        print("\\topcaption{Samples used per region, split by category.}")
        print("\\begin{tabular}{l p{3.2cm} p{3.2cm} p{3.2cm} p{2.4cm}}")
        print("Region & Models & Backgrounds & Data-driven & Signals \\\\")
        print("\\hline\\hline")
        for row in rows:
            nrows = max(len(row["signals"]), len(row["models"]), len(row["backgrounds"]), len(row["data_driven"]))

            # Pad columns to nrows with blanks
            def _pad(col_lines):
                return col_lines + [""] * (nrows - len(col_lines))

            reg_label = row["region"]
            sig_lines = _pad(row["signals"])
            mod_lines = _pad(row["models"])
            bkg_lines = _pad(row["backgrounds"])
            dd_lines = _pad(row["data_driven"])

            for i in range(nrows):
                if nrows == 1:
                    reg_col = reg_label
                else:
                    reg_col = f"\\multirow{{{nrows}}}{{*}}{{{reg_label}}}" if i == 0 else ""
                print(f"{reg_col} & {mod_lines[i]} & {bkg_lines[i]} & {dd_lines[i]} & {sig_lines[i]} \\\\")
            print("\\hline")
        print("\\end{tabular}")
        print("\\label{tab:samples_by_region}")
        print("\\end{table}")

    print_region_table(analysis)
