from __future__ import division

import matplotlib

matplotlib.use("Agg")
import sys
import uproot
import re
import os
import numpy as np
from matplotlib import pyplot as plt

pjoin = os.path.join


def plot(toys, obs, directory):
    tag = os.path.basename(directory)
    values = digest(toys, obs)
    plt.clf()
    fig = plt.gcf()
    ax = plt.gca()

    xmin = min(np.min(toys), obs)
    xmax = max(np.max(toys), obs)

    bins = np.linspace(0.9 * xmin, 1.1 * xmax, 100)

    hist, _ = np.histogram(toys, bins)
    centers = bins[:-1] + np.diff(bins) * 0.5
    plt.step(bins[:-1], hist, where="post", label=f"Toys (N={len(toys)})")

    plt.plot([obs, obs], [0, 1.2 * max(hist)], ls="-", color="r", label="Observed, p-value {p}".format(**values))

    plt.legend()
    ax.set_xlabel("Test statistic")
    ax.set_ylabel("Toys")
    ax.set_title(tag)
    fig.savefig(pjoin(directory, f"gof_{tag}.pdf"))

    printout(values)


def printout(values):
    print("Processed {t_n} toys".format(**values))
    print("Test stat range: {t_min:.0f} - {t_max:.0f}".format(**values))
    print("Mean, std: {t_mean:.0f}, {t_std:.0f}".format(**values))
    print("Observed: {obs:.0f}".format(**values))
    print("p_value: {p}".format(**values))


def get_values(file):
    f = uproot.open(file)
    return f["limit"]["limit"].array()


def get_obs(directory):
    for file in os.listdir(directory):
        if re.match("higgsCombine_CRonly_obs_.*.GoodnessOfFit.mH.*.root", file):
            break
    return get_values(os.path.join(directory, file))[0]


def get_toys(directory):
    arrays = []
    for file in os.listdir(directory):
        if not re.match("higgsCombine_CRonly_toys_.*_.*.GoodnessOfFit.mH125.*.root", file):
            continue
        try:
            arrays.append(get_values(os.path.join(directory, file)))
        except ValueError:
            continue
    return np.concatenate(arrays)


def digest(toys, obs):

    p_value = np.sum(toys > obs) / len(toys)
    if p_value == 0:
        p_value = f"< {1./len(toys):.2e}"
    else:
        p_value = f"{p_value:.2e}"
    values = {"obs": obs, "t_n": len(toys), "t_std": np.std(toys), "t_mean": np.mean(toys), "t_min": np.min(toys), "t_max": np.max(toys), "p": p_value}

    return values


directory = os.path.abspath(sys.argv[1])

obs = get_obs(directory)

toys = get_toys(directory)


plot(toys, obs, directory)
