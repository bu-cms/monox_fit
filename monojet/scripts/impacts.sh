#!/bin/bash

#remove limit on stack size to prevent related segfault
ulimit -s unlimited

do_impacts(){
    YEAR=${1}
    SIGNAL=${2}
    mkdir -p ${YEAR}_${SIGNAL}
    pushd ${YEAR}_${SIGNAL}
    COMMON_OPTS="-t -1 --expectSignal=${SIGNAL} --parallel=4 --rMin=-1 --autoRange 5 --squareDistPoiStep"
    combineTool.py -M Impacts \
                   -d ../../cards/card_monojet_${YEAR}.root \
                   -m 125 \
                   --doInitialFit \
                   --robustFit 1 \
                   ${COMMON_OPTS}
    combineTool.py -M Impacts -d ../../cards/card_monojet_${YEAR}.root \
                   -m 125 \
                   --robustFit 1 \
                   --doFits \
                    ${COMMON_OPTS}
    combineTool.py -M Impacts \
                   -d ../../cards/card_monojet_${YEAR}.root \
                   -m 125 \
                   -o impacts.json \
                    ${COMMON_OPTS}
    popd
    plotImpacts.py -i ${YEAR}_${SIGNAL}/impacts.json -o impacts_monojet_${YEAR}_${SIGNAL}
}
export -f do_impacts
### Impacts
mkdir -p impacts
pushd impacts
for SIGNAL in "0.0"; do
    for YEAR in 2017; do
        nohup bash -c "do_impacts $YEAR $SIGNAL" >  impacts_${YEAR}_${SIGNAL}.log &
    done
done
popd
