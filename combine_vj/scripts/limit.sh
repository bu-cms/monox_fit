
mkdir -p limit
pushd limit

#remove limit on stack size to prevent related segfault
ulimit -s unlimited

for YEAR in combined; do
    nohup combine -M AsymptoticLimits \
                   -t -1 \
                   -n monojet_monov_nominal_asimov_${YEAR} \
                   ../cards/card_monojet_monov_nominal_${YEAR}.root \
                   --setParameters LUMISCALE=1 \
                   --freezeParameters LUMISCALE \
                   --cminDefaultMinimizerStrategy 0 \
                   &> log_asimov_${YEAR}.txt &
    nohup combine -M AsymptoticLimits \
                  -n monojet_monov_nominal_${YEAR} \
                  ../cards/card_monojet_monov_nominal_${YEAR}.root \
                  --setParameters LUMISCALE=1 \
                  --freezeParameters LUMISCALE \
                  --cminDefaultMinimizerStrategy 0 \
                  &> log_${YEAR}.txt &
done
popd
