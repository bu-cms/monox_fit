#!/bin/bash
mkdir -p diagnostics
pushd diagnostics

#remove limit on stack size to prevent related segfault
ulimit -s unlimited

#21 implies the combination of 2022, 2023 datasets.
# Individual years
for YEAR in 2021; do
    combine -M FitDiagnostics \
            --saveShapes \
            --saveWithUncertainties \
            --robustFit 1 \
            --robustHesse 1 \
            --setParameters 'rgx{mask_.*_signal}=1' \
            -n _monojet_${YEAR} \
            ../cards/card_monojet_${YEAR}.root \
            --cminDefaultMinimizerStrategy 0 \
            --skipSBFit \
            | tee diag_${YEAR}.log &&

        python3 ${CMSSW_BASE}/src/HiggsAnalysis/CombinedLimit/test/diffNuisances.py \
           fitDiagnostics_monojet_${YEAR}.root \
           -g diffnuisances_monojet_${YEAR}.root \
           --skipFitS &

    combine -M FitDiagnostics \
            --saveShapes \
            --saveWithUncertainties \
            --robustFit 1 \
            --robustHesse 1 \
            -n _monojet_unblind_${YEAR} \
            ../cards/card_monojet_${YEAR}.root \
            --cminDefaultMinimizerStrategy 0 \
            | tee diag_unblind_${YEAR}.log &&

        python3 ${CMSSW_BASE}/src/HiggsAnalysis/CombinedLimit/test/diffNuisances.py \
           fitDiagnostics_monojet_unblind_${YEAR}.root \
           -g diffnuisances_monojet_unblind_${YEAR}.root \
           --skipFitS &
done
popd


