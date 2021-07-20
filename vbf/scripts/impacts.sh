#!/bin/bash

### Impacts
mkdir -p impacts_nocondor
pushd impacts_nocondor

# Print out the current version of the limit script
FILEPATH="`dirname $0`/`basename $0`"
cat ${FILEPATH} > "impactScript.sh"

for YEAR in 2017 2018; do
    mkdir ${YEAR}
    pushd ${YEAR}
    combineTool.py -M Impacts -t -1 -d ../../cards/card_vbf_${YEAR}.root -m 125 --doInitialFit --robustFit 1 --parallel=4 --rMin=-1
    combineTool.py -M Impacts -t -1 -d ../../cards/card_vbf_${YEAR}.root -m 125 --robustFit 1 --doFits --parallel 4 --parallel=4 --rMin=-1
    combineTool.py -M Impacts -t -1 -d ../../cards/card_vbf_${YEAR}.root -m 125 -o impacts.json  --parallel=4 --rMin=-1
    popd
    plotImpacts.py -i ${YEAR}/impacts.json -o impacts_${YEAR} --blind

    # mkdir ${YEAR}_nophoton
    # pushd ${YEAR}_nophoton
    # combineTool.py -M Impacts -d ../../cards/card_vbf_${YEAR}.root -m 125 --doInitialFit --robustFit 1 -t -1 --expectSignal=${SIGNAL} --parallel=4 --setParameters mask_vbf_photon=1 --rMin=-1
    # combineTool.py -M Impacts -d ../../cards/card_vbf_${YEAR}.root -m 125 --robustFit 1 --doFits --parallel 4 -t -1 --expectSignal=${SIGNAL} --parallel=4  --setParameters mask_vbf_photon=1 --rMin=-1
    # combineTool.py -M Impacts -d ../../cards/card_vbf_${YEAR}.root -m 125 -o impacts.json -t -1 --expectSignal=${SIGNAL}  --parallel=4  --setParameters mask_vbf_photon=1 --rMin=-1
    # popd
    # plotImpacts.py -i ${YEAR}_nophoton/impacts.json -o impacts_${YEAR}_nophoton
done