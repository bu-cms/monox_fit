#!/bin/bash
mkdir -p diagnostics
pushd diagnostics

#remove limit on stack size to prevent related segfault
ulimit -s unlimited

# # Year by year
# for YEAR in 2017 2018; do
#     for TAGGER in nominal; do
#         for WP in loose tight; do
#             # SR masked
#             LOG="log_diag_${TAGGER}_monov${WP}_${YEAR}.txt"
#             combine -M FitDiagnostics \
#             --saveShapes \
#             --saveWithUncertainties \
#             --setParameters 'rgx{mask_.*_signal}'=1 \
#             -n _${TAGGER}_monov${WP}_${YEAR} \
#             --cminDefaultMinimizerStrategy 0 \
#             ../cards/card_${TAGGER}_monov${WP}_${YEAR}.root \
#             -v2 \
#             > diag_${YEAR}.log &&
#             python ${CMSSW_BASE}/src/HiggsAnalysis/CombinedLimit/test/diffNuisances.py \
#                     fitDiagnostics_${TAGGER}_monov${WP}_${YEAR}.root \
#                     -g diffnuisances_${TAGGER}_monov${WP}_${YEAR}.root \
#                     --skipFitS >> ${LOG}

#             # SR unmasked
#             LOG="log_diag_${TAGGER}_monov${WP}_unblind_${YEAR}.txt"
#             combine -M FitDiagnostics \
#             --saveShapes \
#             --saveWithUncertainties \
#             --setParameters 'rgx{mask_.*_signal}'=0 \
#             -n _${TAGGER}_monov${WP}_unblind_${YEAR} \
#             --cminDefaultMinimizerStrategy 0 \
#             ../cards/card_${TAGGER}_monov${WP}_${YEAR}.root \
#             -v2 \
#             > diag_unblind_${YEAR}.log &&
#             python ${CMSSW_BASE}/src/HiggsAnalysis/CombinedLimit/test/diffNuisances.py \
#                     fitDiagnostics_${TAGGER}_monov${WP}_unblind_${YEAR}.root \
#                     -g diffnuisances_${TAGGER}_monov${WP}_unblind_${YEAR}.root \
#                     --skipFitS >> ${LOG}
#         done
#     done
# done


# Years combined
for TAGGER in nominal; do
    for WP in tight loose; do
        # # SR masked
        # LOG="log_diag_${TAGGER}_monov${WP}_combined"
        # combine -M FitDiagnostics \
        #         --saveShapes \
        #         --saveWithUncertainties \
        #         --setParameters 'rgx{mask_.*_signal}'=1 \
        #         -n _${TAGGER}_monov${WP}_combined \
        #         ../cards/card_${TAGGER}_monov${WP}_combined.root \
        #         -v2 \
        #         > ${LOG} &&
        # python ${CMSSW_BASE}/src/HiggsAnalysis/CombinedLimit/test/diffNuisances.py \
        #         fitDiagnostics_${TAGGER}_monov${WP}_combined.root \
        #         -g diffnuisances_${TAGGER}_monov${WP}_combined.root \
        #         --skipFitS >> ${LOG} &

        # SR unmasked
        LOG="log_diag_${TAGGER}_monov${WP}_unblind_combined"
        combine -M FitDiagnostics \
                --saveShapes \
                --saveWithUncertainties \
                --setParameters 'rgx{mask_.*_signal}'=0 \
                -n _${TAGGER}_monov${WP}_unblind_combined \
                ../cards/card_${TAGGER}_monov${WP}_combined.root \
                -v2  2>&1 > ${LOG} &&
        python ${CMSSW_BASE}/src/HiggsAnalysis/CombinedLimit/test/diffNuisances.py \
                fitDiagnostics_${TAGGER}_monov${WP}_unblind_combined.root \
                -g diffnuisances_${TAGGER}_monov${WP}_unblind_combined.root 2>&1 >> ${LOG} &
    done
done

# # Channels combined
# for TAGGER in nominal; do
#     for YEAR in 2017 2018 combined; do

#         # SR masked
#         LOG="log_diag_${TAGGER}_monov_${YEAR}.txt"
#         combine -M FitDiagnostics \
#                         --saveShapes \
#                         --saveWithUncertainties \
#                         --setParameters 'rgx{mask_.*_signal}'=1 \
#                         -n _${TAGGER}_monov_${YEAR} \
#                         ../cards/card_${TAGGER}_monov_${YEAR}.root \
#                         -v2 \
#                         > ${LOG} &&
#         python ${CMSSW_BASE}/src/HiggsAnalysis/CombinedLimit/test/diffNuisances.py \
#                fitDiagnostics_${TAGGER}_monov_${YEAR}.root \
#                -g diffnuisances_${TAGGER}_monov_${YEAR}.root \
#                --skipFitS |
#                >> ${LOG}

#         # SR unmasked
#         LOG="log_diag_${TAGGER}_monov_unblind_${YEAR}.txt"
#         combine -M FitDiagnostics \
#                         --saveShapes \
#                         --saveWithUncertainties \
#                         --setParameters 'rgx{mask_.*_signal}'=0 \
#                         -n _${TAGGER}_monov_unblind_${YEAR} \
#                         ../cards/card_${TAGGER}_monov_unblind_${YEAR}.root \
#                         -v2 \
#                         > ${LOG} &&
#         python ${CMSSW_BASE}/src/HiggsAnalysis/CombinedLimit/test/diffNuisances.py \
#                fitDiagnostics_${TAGGER}_monov_unblind_${YEAR}.root \
#                -g diffnuisances_${TAGGER}_monov_unblind_${YEAR}.root >> ${LOG}
#         done
# done
# popd
