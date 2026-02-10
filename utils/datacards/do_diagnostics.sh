#!/bin/bash
source "$(dirname "$0")/colors.sh"

# Fit diagnostics script

CHANNEL="$1"
YEAR="$2"
FOLDER="diagnostics"

mkdir -p ${FOLDER}
pushd ${FOLDER} > /dev/null

TAG="${CHANNEL}_${YEAR}"
CARD="../cards/card_${TAG}.txt"
WS="../cards/card_${TAG}.root"
LOGFILE="log_diag_${YEAR}.txt"
FITDIAGFILE="fitDiagnostics_${TAG}.root"
SHAPESFILE="prefit_postfit_shapes_${TAG}.root"
DIFFROOT="diffnuisances_${TAG}.root"

# Uncomment the options you want to use
EXTRA_OPTS=()
EXTRA_OPTS+=(--saveShapes)
EXTRA_OPTS+=(--saveWithUncertainties)
EXTRA_OPTS+=(--cminDefaultMinimizerStrategy 0)
EXTRA_OPTS+=(--robustHesse 1)
EXTRA_OPTS+=(--rMin -5 --rMax 5)
# EXTRA_OPTS+=(--skipSBFit)

METHOD="FitDiagnostics"
cecho blue ">> Running ${METHOD} for ${TAG}"
CMD="combine -M ${METHOD} ${WS} -n \"_${TAG}\" ${EXTRA_OPTS[*]}"
run_with_log "$CMD" "$LOGFILE"

cecho blue ">> Extracting postfit shapes for ${TAG}"
PostFitShapesFromWorkspace --workspace ${WS} --datacard ${CARD} --output ${SHAPESFILE} \
     --fitresult "${FITDIAGFILE}:fit_b" --postfit --covariance --print

cecho blue ">> Running diffNuisances for ${FITDIAGFILE}"
python3 "${CMSSW_BASE}/src/HiggsAnalysis/CombinedLimit/test/diffNuisances.py" ${FITDIAGFILE} -g ${DIFFROOT} --all

popd > /dev/null