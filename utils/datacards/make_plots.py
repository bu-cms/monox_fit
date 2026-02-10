#!/bin/env python3

import argparse
from plotter.plot_prefit_postfit import plot_prefit_postfit
from plotter.plot_data_validation import plot_data_validation
from plotter.plot_ratio import plot_ratio
from plotter.plot_diff_nuis import plot_diff_nuis


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate standard plots for a given analysis channel.")
    parser.add_argument("--channel", required=True, help="Analysis channel name (e.g. vbf, monojet)")
    parser.add_argument("--year", default="Run3", choices=["2017", "2018", "Run3"], help="Dataset year (default: Run3)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    lumi = {
        "2017": 41.5,
        "2018": 59.7,
        "Run3": 62.5,
    }

    regions = ["singlemu", "dimuon", "photon", "singleel", "dielec", "signal"]
    region_pairs = [
        # Flavor integrated
        ("combined", "photon"),
        ("combinedW", "photon"),
        ("combined", "combinedW"),
        # Split by flavor
        ("dimuon", "singlemu"),
        ("dielec", "singleel"),
        ("singleel", "photon"),
        ("singlemu", "photon"),
        ("dielec", "photon"),
        ("dimuon", "photon"),
    ]

    year = args.year
    channel = args.channel
    category = f"{channel}_{year}"
    outdir = f"./plots/{year}/"
    shapes_filename = f"diagnostics/prefit_postfit_shapes_{category}.root"
    diffnuis_file = f"diagnostics/diffnuisances_{category}.root"
    model_filename = f"root/combined_model_{channel}.root"

    common_args = {"category": category, "outdir": outdir, "lumi": lumi[year], "year": year}

    for region in regions:
        plot_prefit_postfit(region=region, shapes_filename=shapes_filename, **common_args)
        plot_ratio(region=region, model_filename=model_filename, **common_args)

    for region1, region2 in region_pairs:
        plot_data_validation(region1=region1, region2=region2, shapes_filename=shapes_filename, **common_args)

    plot_diff_nuis(diffnuis_file=diffnuis_file, outdir=outdir, category=category)


if __name__ == "__main__":
    main()
