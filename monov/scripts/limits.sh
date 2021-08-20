#!/bin/bash

#remove limit on stack size to prevent related segfault
ulimit -s unlimited

### Asimov limit
mkdir -p limit
pushd limit
for file in ../cards/*.root; do
    TAG=$(basename $file | sed 's/card_//g;s/.root//g');
    nohup combine -M AsymptoticLimits $file -t -1 -n asimov_$TAG --setParameters LUMISCALE=1 --freezeParameters LUMISCALE --cminDefaultMinimizerStrategy 0  &> log_asimov_$TAG.txt &
    nohup combine -M AsymptoticLimits $file -n ${TAG} --setParameters LUMISCALE=1 --freezeParameters LUMISCALE --cminDefaultMinimizerStrategy 0  &> log_$TAG.txt &
done
popd
