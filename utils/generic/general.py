# ==============================
# Helper functions for general usage
# ==============================

import numpy as np
from utils.workspace.processes import get_region_label_map, get_processes


def oplus(*args: float) -> float:
    """Compute the quadrature sum of an arbitrary number of inputs."""
    return np.sqrt(np.sum(np.array(args) ** 2))


def extract_analysis(category):
    channels = ["monojet", "monov", "vbf"]
    matches = [c for c in channels if c in category]
    assert len(matches) == 1
    return matches[0]


def rename_region(label: str) -> str:
    region = None
    for key, value in get_region_label_map():
        if value == label:
            region = key
    if not region:
        raise ValueError(f"Region not found for {label}.")
    return region


def is_minor_bkg(category: str, hname: str):
    if hname.lower().endswith(("up", "down")):
        return False
    label = hname.split("_")[0]
    background = hname.replace(f"{label}_", "")
    region = rename_region(label)
    backgrounds = get_processes(analysis=extract_analysis(category), region=region, type="backgrounds")
    return background in backgrounds
