#!/bin/bash
set -e

#remove limit on stack size to prevent related segfault
ulimit -s unlimited

mkdir -p cards
# Fill templates
for YEAR in 2017 2018; do
    CARD=cards/card_monojet_${YEAR}.txt
    cp ../../templates/monojet_template.txt ${CARD}
    sed -i "s|@YEAR|${YEAR}|g" ${CARD}

     if [ $YEAR -eq 2017 ]; then
        sed -i "s|@LUMIXY|1.008|g" ${CARD}
        sed -i "s|@LUMILS|1.003|g" ${CARD}
        sed -i "s|@LUMIBBD|1.006|g" ${CARD}
        sed -i "s|@LUMIBCC|1.003|g" ${CARD}
        sed -i "s|@LUMIGS|1.001|g" ${CARD}
        sed -i "s|@LUMI|1.020|g" ${CARD}
     elif [ $YEAR -eq 2018 ]; then
        sed -i "s|@LUMIXY|1.02|g" ${CARD}
        sed -i "s|@LUMILS|1.002|g" ${CARD}
        sed -i "s|@LUMIBBD|1.002|g" ${CARD}
        sed -i "s|@LUMIBCC|1.002|g" ${CARD}
        sed -i "s|@LUMIGS|1.001|g" ${CARD}
        sed -i "s|@LUMI|1.015|g" ${CARD}
        sed -i "/prefiring/d" ${CARD}
     fi
     # affected by mistags in loose region with ratio of -1/20
     sed -i "s|@MISTAGLOOSEW|0.999        |g"    ${CARD}
     sed -i "s|@MISTAGLOOSEZ|0.998        |g"    ${CARD}
     sed -i "s|@MISTAGLOOSEG|0.998        |g"    ${CARD}

    sed -i "s|combined_model.root|../root/combined_model_monojet.root|g" ${CARD}
    sed -i "s|monojet_qcd_ws.root|../root/monojet_qcd_ws.root|g" ${CARD}

    # Remove useless stat uncertainties
    # Uncertainties are removed if they do not have a variation histogram available
    # The criteria for whether a variation histogram is present are defined in
    # make_ws.py
    rootls -1 root/ws_monojet.root:category_monojet_${YEAR} > tmp_histdump
    for NUIS in $(grep shape ${CARD} | awk '{print $1}' | grep stat); do
      if [ $(grep -c ${NUIS}Up tmp_histdump) -eq 0 ]; then
         sed -i "/^${NUIS} .*/d" ${CARD}
         echo "Warning: removing nuisance ${NUIS} from ${CARD}, shape not present in ws_monojet_${WP}.root"
      fi
    done
    rm tmp_histdump

    text2workspace.py ${CARD} --channel-masks
    python3 $CMSSW_BASE/src/HiggsAnalysis/CombinedLimit/test/systematicsAnalyzer.py --all -f html ${CARD} > cards/systematics_${YEAR}.html
done


COMBINED=cards/card_monojet_combined.txt
combineCards.py cards/card_monojet_201*.txt > ${COMBINED}
sed -i 's/ch\(1\|2\)_//g' ${COMBINED}
text2workspace.py ${COMBINED} --channel-masks
