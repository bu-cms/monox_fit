#!/bin/bash
do_impacts(){
    YEAR=${1}
    SIGNAL=${2}
    CARD=${3}
    mkdir -p ${YEAR}_${SIGNAL}
    pushd ${YEAR}_${SIGNAL}
    TAG=task
    COMMON_OPTS="-t -1 --expectSignal=${SIGNAL} --parallel=4 --rMin=-1 --autoRange 5 --squareDistPoiStep --setParameters LUMISCALE=1 --freezeParameters LUMISCALE --cminDefaultMinimizerStrategy 0 --robustFit 1 --robustHesse 1"
    combineTool.py -M Impacts \
                   -d ${CARD} \
                   -m 125 \
                   --doInitialFit \
                   ${COMMON_OPTS}

    # Submit the hard work to condor
    combineTool.py -M Impacts -d ${CARD} \
                   -m 125 \
                   --doFits \
                   --job-mode condor \
                   --task-name ${TAG} \
                   --sub-opts '+MaxRuntime=72000' \
                    ${COMMON_OPTS}

    # Wait for condor jobs to return
    date
    for i in $(seq 1 1 10); do
        condor_wait -debug -status ${TAG}*.log && break;
        sleep $((i*120))
    done
    date
    sleep 60

    combineTool.py -M Impacts \
                   -d ${CARD} \
                   -m 125 \
                   -o impacts.json \
                    ${COMMON_OPTS}
    popd
    plotImpacts.py -i ${YEAR}_${SIGNAL}/impacts.json -o impacts_combine_vj_${YEAR}_${SIGNAL}
}

export -f do_impacts
### Impacts
mkdir -p impacts
pushd impacts
for SIGNAL in "0.0"; do
    for YEAR in combined; do
        nohup bash -c "do_impacts $YEAR  $SIGNAL $(readlink -e ../cards/card_monojet_monov_nominal_${YEAR}.root)" >  impacts_${YEAR}_${SIGNAL}.log &
    done
done
popd