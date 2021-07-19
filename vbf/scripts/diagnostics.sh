#!/bin/bash

### Fit diagnostics

# CR-only fit or SR+CR combined fit, read as a command line argument
ARGS=("$@")
CR_ONLY_FIT=$(echo $ARGS | cut -f2 -d=)   

if [ $CR_ONLY_FIT -eq 1 ]
then
    OUTDIR="diagnosticsCROnlyFit"
    MASK_SIGNAL=1
    echo "INFO: Running CR only fit."
else
    OUTDIR="diagnosticsSRAndCRFit"
    MASK_SIGNAL=0
    echo "INFO: Running SR+CR combined fit."
fi

mkdir -p ${OUTDIR}
pushd ${OUTDIR}
for YEAR in 2017 2018; do
    combine -M FitDiagnostics \
            --saveShapes \
            --saveWithUncertainties \
            --setParameters mask_vbf_${YEAR}_signal=${MASK_SIGNAL} \
            --robustFit 1 \
            -n _vbf_${YEAR} \
            ../cards/card_vbf_${YEAR}.root
    python ${CMSSW_BASE}/src/HiggsAnalysis/CombinedLimit/test/diffNuisances.py \
           fitDiagnostics_vbf_${YEAR}.root\
           -g diffnuisances_vbf_${YEAR}.root
done


# Combined
combine -M FitDiagnostics \
        --saveShapes \
        --saveWithUncertainties \
        --robustFit 1 \
        --setParameters mask_vbf_2017_signal=${MASK_SIGNAL},mask_vbf_2018_signal=${MASK_SIGNAL} \
        -n _vbf_combined \
        ../cards/card_vbf_combined.root

python ${CMSSW_BASE}/src/HiggsAnalysis/CombinedLimit/test/diffNuisances.py \
        fitDiagnostics_vbf_combined.root \
        -g diffnuisances_vbf_combined.root
popd