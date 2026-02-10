# monox_fit

This repository contains the recipe for the **Run 3 mono-X fit code**.  
For the **Run 2 legacy code**, please check the tag `legacy_run2`.

---

## Setup combine

Start by setting up [Combine v10 in CMSSW 14](http://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/latest/#combine-v10-recommended-version),  
and also install [CombineHarvester](http://cms-analysis.github.io/CombineHarvester/index.html):

```bash
source /cvmfs/cms.cern.ch/cmsset_default.sh
export SCRAM_ARCH=el9_amd64_gcc12

cmsrel CMSSW_14_1_0_pre4
cd CMSSW_14_1_0_pre4/src
cmsenv

# clone and build Combine
git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git
cd $CMSSW_BASE/src/HiggsAnalysis/CombinedLimit
git fetch origin
git checkout v10.0.1
scram b clean; scram b -j4 # clean build is recommended

# clone and build CombineHarvester
cd $CMSSW_BASE/src
git clone https://github.com/cms-analysis/CombineHarvester.git CombineHarvester
scram b -j4
```

---

## Create the workspace

Before running anything, set up the local environment:

```bash
source setup_env.sh
```

The script [`build_workspace.py`](build_workspace.py) is the main entry point. It:

1. Generates a RooWorkspace from histograms in a ROOT file.
2. Builds a combined model compatible with CMS Combine.
3. Creates an `INFO.txt` file with input/output checksums and Git metadata.
4. Symlinks a `Makefile` into the output folder for producing datacards.

To run it, execute
```bash
python3 build_workspace.py \
  -d <input_dir> \
  -a <analysis> \
  -y <year> \
  -v <variable> \
  [-f <root_folder>] \
  [-t <tag>]
```

The script takes these optional arguments:

| Argument           | Description                                       | Default       |
|--------------------|---------------------------------------------------|---------------|
| `-d`, `--dir`      | Path to directory containing the input ROOT file   | *(required)*  |
| `-a`, `--analysis` | Analysis name: `vbf`, `monojet`, `monov`, …        | `"vbf"`       |
| `-y`, `--year`     | Dataset year: `2017`, `2018`, or `Run3`            | `"2017"`      |
| `-v`, `--variable` | Observable: `mjj`, `recoil`, etc.                  | `"mjj"`       |
| `-f`, `--folder`   | Folder inside the ROOT file to look for histograms | auto-detected |
| `-t`, `--tag`      | Custom output tag (used in output folder name)     | today’s date  |

Example:

```bash
python3 build_workspace.py \
  -d /path/to/inputs \
  -a monojet \
  -y Run3 \
  -v recoil \
  -t 2025_08_28
```

This will:

- read `inputs/histograms/recoil/monojet_Run3/histograms_monojet.root` nominal histograms
- read `inputs/sys/recoil/monojet_Run3/*root` systematic variations
- create a workspace and model for category `monojet_Run3`
- output the files into:  
  `$FIT_FRAMEWORK_PATH/monojet/Run3/2025_08_28/root/`

### Output structure

```
monojet/
└── Run3/
    └── 2025_08_28/
        │── Makefile                # Symlink for Combine datacards
        ├── root/
        │   ├── ws_vbf.root             # The RooWorkspace
        │   ├── combined_model_vbf.root # The Combine-ready model
        │   ├── INFO.txt                # Checksums + Git info
```

---

## Running datacards and fits

Move into the relevant output directory and use the provided Makefile.  
Available commands include:

```bash
make help          # show help message
make list          # list all available targets
make cards         # create datacards/workspace
make diagnostics   # run fit diagnostics
make diag          # alias for diagnostics
make plots         # produce standard plots
make impacts       # run impact analysis
make limits        # extract limits
make nll           # run NLL scans
make gof           # run goodness-of-fit tests
```

---
