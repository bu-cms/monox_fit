#!/bin/bash

#remove limit on stack size to prevent related segfault
ulimit -s unlimited

### Fit diagnostics
mkdir -p diagnostics
pushd diagnostics
for YEAR in 2017; do
    combine -M FitDiagnostics --saveShapes --saveWithUncertainties --setParameters mask_monojet_signal=1 -n _monojet_${YEAR} ../cards/card_monojet_${YEAR}.root
    python3 ${CMSSW_BASE}/src/HiggsAnalysis/CombinedLimit/test/diffNuisances.py fitDiagnostics_monojet_${YEAR}.root  -g diffnuisances_monojet_${YEAR}.root
done
popd



### Asimov limit
mkdir -p limit
pushd limit
for YEAR in 2017; do
    combine -M AsymptoticLimits -t -1 -n _monojet_${YEAR} ../cards/card_monojet_${YEAR}.root | tee log_${YEAR}.txt
done
popd

### Impacts
SIGNAL="0.5"
mkdir -p impacts
pushd impacts
for YEAR in 2017; do
    mkdir ${YEAR}
    pushd ${YEAR}
    combineTool.py -M Impacts -d ../../cards/card_monojet_${YEAR}.root -m 125 --doInitialFit --robustFit 1 -t -1 --expectSignal=${SIGNAL} --parallel=4
    combineTool.py -M Impacts -d ../../cards/card_monojet_${YEAR}.root -m 125 --robustFit 1 --doFits --parallel 4 -t -1 --expectSignal=${SIGNAL} --parallel=4
    combineTool.py -M Impacts -d ../../cards/card_monojet_${YEAR}.root -m 125 -o impacts.json -t -1 --expectSignal=${SIGNAL}  --parallel=4
    popd
    plotImpacts.py -i ${YEAR}/impacts.json -o impacts_monojet_${YEAR}
done
popd
