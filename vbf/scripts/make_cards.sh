#!/bin/bash
set -e

mkdir -p cards
# Fill templates
for YEAR in 2017 2018; do
    CARD=cards/card_vbf_${YEAR}.txt
    cp ../../templates/vbf_template_pretty_withphotons.txt ${CARD}
    sed -i "s|@YEAR|${YEAR}|g" ${CARD}

    if [ $YEAR -eq 2017 ]; then
        sed -i "s|@LUMIXY|1.008|g" ${CARD}
        sed -i "s|@LUMILS|1.003|g" ${CARD}
        sed -i "s|@LUMIBBD|1.004|g" ${CARD}
        sed -i "s|@LUMIDB|1.005|g" ${CARD}
        sed -i "s|@LUMIBCC|1.003|g" ${CARD}
        sed -i "s|@LUMIGS|1.001|g" ${CARD}
        sed -i "s|@LUMI|1.020|g" ${CARD}
    elif [ $YEAR -eq 2018 ]; then
        sed -i "s|@LUMIXY|1.02|g" ${CARD}
        sed -i "s|@LUMILS|1.002|g" ${CARD}
        sed -i "s|@LUMIBBD|1.0|g" ${CARD}
        sed -i "s|@LUMIDB|1.0|g" ${CARD}
        sed -i "s|@LUMIBCC|1.02|g" ${CARD}
        sed -i "s|@LUMIGS|1.00|g" ${CARD}
        sed -i "s|@LUMI|1.015|g" ${CARD}
        sed -i "/prefir/d" ${CARD}
    fi
    sed -i "s|combined_model.root|../root/combined_model_vbf.root|g" ${CARD}
    sed -i "s|vbf_hf_estimate_ws_${YEAR}.root|../root/vbf_hf_estimate_ws_${YEAR}.root|g" ${CARD}
    text2workspace.py ${CARD} --channel-masks
    python $CMSSW_BASE/src/HiggsAnalysis/CombinedLimit/test/systematicsAnalyzer.py --all -f html ${CARD} > cards/systematics_${YEAR}.html
done


COMBINED=cards/card_vbf_combined.txt
combineCards.py cards/card_vbf_201*.txt > ${COMBINED}
sed -i 's/ch\(1\|2\)_//g' ${COMBINED}
text2workspace.py ${COMBINED} --channel-masks


# Cards for IC
for YEAR in 2017 2018; do
    CARDIN=cards/card_vbf_${YEAR}.txt
    CARD=cards/card_vbf_photons_${YEAR}.txt

    combineCards.py ${CARDIN} --ic=vbf_${YEAR}_photon > ${CARD}
    sed -i '/lnN[ -]*$/d' ${CARD}
    sed -i 's/ch\(1\|2\)_//g' ${CARD}
    sed -i "s|../root/combined_model_vbf.root|../root/combined_model_vbf_forIC_${YEAR}.root|g" ${CARD}
done