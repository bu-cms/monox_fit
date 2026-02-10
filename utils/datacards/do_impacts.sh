#!/bin/bash
source "$(dirname "$0")/colors.sh"

# Impacts script

# ========== Toggle debug ==========
DEBUG=0
# DEBUG=1 # Only print commands (no execution)

# ========== Inputs / folders ==========
CHANNEL="$1"
YEAR="$2"
FOLDER="impacts_folder"
FOLDER="impacts_folder_asimov"

mkdir -p "${FOLDER}"
pushd "${FOLDER}" > /dev/null

TAG="${CHANNEL}_${YEAR}"
WS="../../cards/card_${TAG}.root"

# ========== Common options ==========
# (Un)Comment the options you want to use
EXTRA_OPTS=()
EXTRA_OPTS+=(-m 125)
EXTRA_OPTS+=(--cminPreScan)
EXTRA_OPTS+=(--cminPoiOnlyFit)
EXTRA_OPTS+=(--cminDefaultMinimizerStrategy 0) # speed
# EXTRA_OPTS+=(--cminDefaultMinimizerStrategy 2) # robust
EXTRA_OPTS+=(--cminDefaultMinimizerTolerance 0.01)
EXTRA_OPTS+=(--robustFit 1)
EXTRA_OPTS+=(--rMin -5 --rMax 5)
EXTRA_OPTS+=(--autoRange 5)
EXTRA_OPTS+=(--squareDistPoiStep)
EXTRA_OPTS+=(-t -1)  # Asimov toys

PLOT_OPTS=()
# PLOT_OPTS+=(--blind)
PLOT_OPTS+=(--summary)

PARALLEL=50

# ========== Condor toggle ==========
# Leave empty for local runs:
CONDOR_OPTS=()
# Uncomment to submit to Condor:
CONDOR_OPTS=(--job-mode condor)
# CONDOR_OPTS+=(--sub-opts '+JobFlavour="espresso"')
# CONDOR_OPTS+=(--dry-run)

# ========== Signal / task ==========
INJECTED_SIG="" # leave empty to skip --expectSignal
# INJECTED_SIG="0.5"

if [[ -n "${INJECTED_SIG}" ]]; then
  TAG_SIG="${TAG}_sig${INJECTED_SIG}"
  JOB_OPTS=("${EXTRA_OPTS[@]}" "--expectSignal=${INJECTED_SIG}")
else
  TAG_SIG="${TAG}_nominal"
  JOB_OPTS=("${EXTRA_OPTS[@]}")
fi


mkdir -p "${TAG_SIG}"
pushd "${TAG_SIG}" > /dev/null

# Local uses --parallel, Condor drops it (combineTool will splits jobs)
if ((${#CONDOR_OPTS[@]})); then
    TASK_NAME="IMPACTS_${TAG_SIG}"
    FIT_OPTS=("${JOB_OPTS[@]}" --task-name "${TASK_NAME}")
else
    FIT_OPTS=("${JOB_OPTS[@]}" --parallel "${PARALLEL}")
fi

# ========== Helper: run-or-echo ==========
run_or_echo() {
  if (( DEBUG )); then
    cecho green "Would run: ${cmd[@]}"
  else
    "${cmd[@]}"
  fi
}

# ========== Initial fit ==========
cecho blue ">> [${TAG_SIG}] Initial fit"
cmd=(combineTool.py -M Impacts -d "${WS}" "${JOB_OPTS[@]}" --doInitialFit)
run_or_echo | tee "log_impact_initial_${TAG_SIG}.txt"

# ========== Fits (local or Condor) ==========
cecho blue ">> [${TAG_SIG}] Performing fits"
cmd=(combineTool.py -M Impacts -d "${WS}" "${FIT_OPTS[@]}" "${CONDOR_OPTS[@]}" --doFits)
run_or_echo | tee "log_impact_fits_${TAG_SIG}.txt"

# ========== Inline wait for Condor jobs (only if not a dry-run and not DEBUG) ==========
if ((${#CONDOR_OPTS[@]})) && [[ " ${CONDOR_OPTS[*]} " != *" --dry-run "* ]] && (( DEBUG == 0 )); then
    cecho blue ">> [${TAG_SIG}] Waiting for Condor jobs to finish"
    # Count total jobs from stdout files
    logs_glob="${TASK_NAME}*.out"
    LOGFILE=(${TASK_NAME}*.log)  # Single task logfile produced by combineTool
    cecho cyan "[wait] Condor jobs monitoring: log=${LOGFILE} out=${logs_glob}"
    sleep 30

    for i in $(seq 1 500); do
        # Done = number of termination markers in the single task log
        total=$(ls -1 ${logs_glob} 2>/dev/null | wc -l)
        done_jobs=$(grep -E -c '^Job terminated\.|Normal termination' "${LOGFILE}" 2>/dev/null || echo 0)
        if [ "${total}" -gt 0 ]; then
            pct=$(awk -v d="${done_jobs}" -v t="${total}" 'BEGIN{printf "%.1f", (t>0?100*d/t:0)}')
            cecho cyan "\r[wait] ${TASK_NAME}: "${done_jobs}"/"${total}" ("${pct}"%) done"
        else
            cecho cyan "\r[wait] ${TASK_NAME}: discovering jobs..."
        fi

        # Exit when complete
        if [ "${total}" -gt 0 ] && [ "${done_jobs}" -eq "${total}" ]; then
            echo
            break
        fi
        sleep 60
    done
    sleep 60
fi

# ========== Collect impacts ==========
cecho blue ">> [${TAG_SIG}] Collecting impacts to JSON"
cmd=(combineTool.py -M Impacts -d "${WS}" "${JOB_OPTS[@]}" -o impacts.json)
run_or_echo | tee "log_impact_json_${TAG_SIG}.txt"

# ========== Plot ==========
cecho blue ">> [${TAG_SIG}] Plotting impacts"
cmd=(plotImpacts.py -i "impacts.json" -o "impacts_${TAG_SIG}" "${PLOT_OPTS[@]}")
run_or_echo | tee "log_impact_pdf_${TAG_SIG}.txt"

# echo ${TASK_NAME}
# ========== Cleaning ==========
mkdir -p job_out combine_output
mv ${TASK_NAME}* condor_* job_out
mv higgsCombine*.root combine_output

popd > /dev/null
popd > /dev/null
cecho green "All impacts jobs finished."
