#!/bin/bash
source "$(dirname "$0")/colors.sh"

# Limit script

CHANNEL="$1"
YEAR="$2"
FOLDER="limit"
FOLDER="limit_blind"

mkdir -p ${FOLDER}
pushd ${FOLDER} > /dev/null

TAG="${CHANNEL}_${YEAR}"
CARD="../cards/card_${TAG}.root"
LOGFILE="log_limit_${YEAR}.txt"
METHOD="-M AsymptoticLimits"

# Uncomment the options you want to use
EXTRA_OPTS=()
EXTRA_OPTS+=(--rMin -100 --rMax 100)
EXTRA_OPTS+=(--run blind)

cecho blue "Running AsymptoticLimits for ${TAG}"
CMD="combine ${METHOD} ${CARD} -n \"_${TAG}\" ${EXTRA_OPTS[*]}"
run_with_log "$CMD" "$LOGFILE"

popd > /dev/null
