# text2workspace.py card_combined.txt --channel-masks

WDIR=diagnostics_cr
mkdir -p ${WDIR}
pushd ${WDIR}

#remove limit on stack size to prevent related segfault
ulimit -s unlimited

for YEAR in combined; do
        combine -M FitDiagnostics \
                --saveShapes \
                --saveWithUncertainties \
                --robustFit 1 \
                --robustHesse 1 \
                --setParameters 'rgx{mask_.*_signal}'=1 \
                -n _monojet_monov_${YEAR} \
                --cminDefaultMinimizerStrategy 0 \
                ../cards/card_monojet_monov_nominal_${YEAR}.root \
                | tee diag_${YEAR}.log && \
        python ${CMSSW_BASE}/src/HiggsAnalysis/CombinedLimit/test/diffNuisances.py \
                fitDiagnostics_monojet_monov_${YEAR}.root \
                -g diffnuisances_monojet_monov_combined_${YEAR}.root \
                --skipFitS | tee diffnuis_${YEAR}.log &

        # nohup combine -M FitDiagnostics \
        #         --saveShapes \
        #         --saveWithUncertainties \
        #         --robustFit 1 \
        #         --setParameters 'rgx{mask_.*_signal}=0,LUMISCALE=1' \
        #         --freezeParameters LUMISCALE \
        #         -n _unblind_monojet_monov_${YEAR} \
        #         ../cards/card_monojet_monov_nominal_${YEAR}.root \
        #         --cminDefaultMinimizerStrategy 0 \
        #         --robustHesse 1 \
        #         &> diag_unblind_${YEAR}.log && \
        # python ${CMSSW_BASE}/src/HiggsAnalysis/CombinedLimit/test/diffNuisances.py \
        #         fitDiagnostics_unblind_monojet_monov_${YEAR}.root \
        #         -g diffnuisances_unblind__monojet_monov_combined_${YEAR}.root \
        #         &> diffnuis_unblind_${YEAR}.log &
done
popd
