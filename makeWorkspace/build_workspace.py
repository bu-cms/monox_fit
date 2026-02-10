#!/usr/bin/env python3

import os
import hashlib
import argparse
from typing import Optional
from datetime import date
from utils.generic.parallelize import timeit
from utils.generic.logger import initialize_colorized_logger
from makeWorkspace.make_workspace import create_workspace
from makeWorkspace.generate_combine_model import generate_combine_model


def compute_md5(file_path: str) -> str:
    """Compute the MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def collect_md5_checksums(file_paths: list[str]) -> list[str]:
    """Return lines with MD5 checksums for given file paths."""
    return [f"{compute_md5(file)}  {os.path.basename(file)}" for file in file_paths]


def collect_git_info() -> list[str]:
    """Return lines with Git commit, branch, and diff information."""
    return [
        "--- REPO INFO ---",
        "Commit hash: " + os.popen("git rev-parse HEAD").read().strip(),
        "Branch name: " + os.popen("git rev-parse --abbrev-ref HEAD").read().strip(),
        os.popen("git diff").read(),
    ]


def create_makefile_symlink(output_dir: str) -> None:
    """Create or update symlink to the Makefile in the parent of the output directory."""
    makefile_source = os.path.realpath("utils/datacards/Makefile")
    makefile_link = os.path.join(os.path.dirname(output_dir), "Makefile")
    if os.path.exists(makefile_link) or os.path.islink(makefile_link):
        os.remove(makefile_link)
    os.symlink(makefile_source, makefile_link)


def generate_info_lines(input_dir: str, input_filename: str, output_dir: str) -> list[str]:
    """Gather and return all lines for INFO.txt."""
    lines = [
        f"Input directory: {input_dir}",
        "--- INPUT ---",
        *collect_md5_checksums([input_filename]),
        *collect_git_info(),
        "--- OUTPUT ---",
        *collect_md5_checksums([os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(".root")]),
    ]
    return lines


def build_workspace(input_dir: str, analysis: str, year: str, tag: str, variable: str, root_folder: Optional[str] = None) -> None:
    """Run the full pipeline for a given category and date tag."""
    input_dir = os.path.realpath(input_dir)
    category = f"{analysis}_{year}"
    output_dir = os.path.realpath(os.path.join(os.getenv("FIT_FRAMEWORK_PATH", ""), analysis, year, tag, variable, "root"))
    os.makedirs(output_dir, exist_ok=True)

    input_filename = os.path.join(input_dir, f"histograms_{analysis}.root")
    workspace_file = os.path.join(output_dir, f"ws_{analysis}.root")
    combined_model_file = os.path.join(output_dir, f"combined_model_{analysis}.root")
    info_file = os.path.join(output_dir, "INFO.txt")

    logger.info(f"Creating workspace for category '{category}'...")
    create_workspace(input_filename=input_filename, output_filename=workspace_file, category=category, variable=variable, root_folder=root_folder)

    logger.info("Running model generation...")
    generate_combine_model(input_filename=workspace_file, output_filename=combined_model_file, category=category, variable=variable)

    logger.info("Finalizing...")

    with open(info_file, "w") as f:
        info_lines = generate_info_lines(input_dir, input_filename, output_dir)
        f.write("\n".join(info_lines) + "\n")

    create_makefile_symlink(output_dir)

    logger.info(f"Done! Output path: {os.path.dirname(output_dir)}")


@timeit
def main() -> None:
    """Main function to generate RooWorkspace and datacards for analysis."""
    parser = argparse.ArgumentParser(description="Arguments for workspace creation.")
    # parser.add_argument("-a", "--analysis", type=str, default="vbf", help="Analysis name (e.g., 'vbf', 'monojet', 'monov').")
    parser.add_argument("-a", "--analysis", type=str, default="monojet", help="Analysis name (e.g., 'vbf', 'monojet', 'monov').")
    # parser.add_argument("-v", "--variable", type=str, default="mjj", help="Observable variable name (e.g., 'mjj', 'met').")
    parser.add_argument("-v", "--variable", type=str, default="recoil", help="Observable variable name (e.g., 'mjj', 'met').")
    parser.add_argument("-y", "--year", type=str, default="Run3", help="Data-taking year (e.g., '2017', '2018', 'Run3').")
    parser.add_argument("-d", "--dir", type=str, default=None, help="Path to the directory containing the input ROOT files")
    parser.add_argument("-f", "--folder", type=str, default=None, help="Optional folder name inside the ROOT file to read histograms from.")
    parser.add_argument("-t", "--tag", type=str, default=None, help="Custom tag for the output directory (default: today's date in YYYY_MM_DD format).")

    args = parser.parse_args()

    input_dir = args.dir or f"inputs/histograms/{args.variable}/{args.analysis}_{args.year}/"
    root_folder = args.folder or f"category_{args.analysis}_{args.year}"
    tag = args.tag or date.today().strftime("%Y_%m_%d")

    build_workspace(input_dir=input_dir, analysis=args.analysis, year=args.year, tag=tag, variable=args.variable, root_folder=root_folder)


if __name__ == "__main__":
    log_level = "INFO"
    # log_level = "DEBUG"
    logger = initialize_colorized_logger(log_level=log_level)
    main()
