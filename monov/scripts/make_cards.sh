#!/bin/bash
set -e

#remove limit on stack size to prevent related segfault
ulimit -s unlimited

mkdir -p cards

for YEAR in 2017 2018; do
    ### INDIVIDUAL CARDS FOR DEEPAK8 WPS
    for WP in loose tight; do
        for TAGGER in nominal; do
            CARD=$PWD/cards/card_${TAGGER}_monov${WP}_${YEAR}.txt
            cp ../../templates/card_template.txt ${CARD}
            sed -i "s/@WP/${WP}/g" ${CARD}
            sed -i "s|@YEAR|${YEAR}|g" ${CARD}


            if [ $YEAR -eq 2017 ]; then
                sed -i "s|@LUMI_CORR_ALL|1.009         |g" ${CARD}
                sed -i "s|@LUMI_CORR_1718|1.006          |g" ${CARD}
                sed -i "s|@LUMI|1.020|g" ${CARD}
            elif [ $YEAR -eq 2018 ]; then
                sed -i "s|@LUMI_CORR_ALL|1.02          |g" ${CARD}
                sed -i "s|@LUMI_CORR_1718|1.002          |g" ${CARD}
                sed -i "s|@LUMI|1.015|g" ${CARD}
                sed -i "/prefiring/d" ${CARD}
            fi
            if [ "$WP" == loose ]; then
                sed -i "s|@VTAGLOOSE|1.10      |g"    ${CARD} 
                sed -i "s|@VTAGTIGHT|0.94      |g"    ${CARD} 
                sed -i "s|@MISTAGLOOSEW|1.02         |g"    ${CARD} 
                sed -i "s|@MISTAGLOOSEZ|1.04         |g"    ${CARD} 
                sed -i "s|@MISTAGLOOSEG|1.03         |g"    ${CARD} 
                sed -i "s|@MISTAGTIGHTW|0.997        |g"    ${CARD} 
                sed -i "s|@MISTAGTIGHTZ|0.994        |g"    ${CARD} 
                sed -i "s|@MISTAGTIGHTG|0.996        |g"    ${CARD} 
                sed -i "s|@MISTAGLOOSETOPZ|-               |g" ${CARD} 
                sed -i "s|@MISTAGLOOSETOPW|1.004           |g" ${CARD} 
                sed -i "s|@MISTAGLOOSEVVZ|1.001            |g"  ${CARD} 
                sed -i "s|@MISTAGLOOSEVVW|1.003          |g"  ${CARD} 
                sed -i "s|@MISTAGTIGHTTOPZ|0.999           |g" ${CARD} 
                sed -i "s|@MISTAGTIGHTTOPW|0.985           |g" ${CARD} 
                sed -i "s|@MISTAGTIGHTVVZ|0.995          |g"  ${CARD} 
                sed -i "s|@MISTAGTIGHTVVW|0.990          |g"  ${CARD} 
                sed -i "s|@MISTAGTIGHTVG|0.999         |g"   ${CARD} 
            elif [ "$WP" == tight ]; then
                sed -i "s|@VTAGLOOSE|-         |g"    ${CARD} 
                sed -i "s|@VTAGTIGHT|1.10      |g"    ${CARD} 
                sed -i "s|@MISTAGLOOSEW|-            |g"    ${CARD} 
                sed -i "s|@MISTAGLOOSEZ|-            |g"    ${CARD} 
                sed -i "s|@MISTAGLOOSEG|-            |g"    ${CARD} 
                sed -i "s|@MISTAGTIGHTW|1.03         |g"    ${CARD} 
                sed -i "s|@MISTAGTIGHTZ|1.06         |g"    ${CARD} 
                sed -i "s|@MISTAGTIGHTG|1.04         |g"    ${CARD} 
                sed -i "s|@MISTAGLOOSETOPZ|-               |g" ${CARD} 
                sed -i "s|@MISTAGLOOSETOPW|-               |g" ${CARD} 
                sed -i "s|@MISTAGLOOSEVVZ|-              |g"  ${CARD} 
                sed -i "s|@MISTAGLOOSEVVW|-              |g"  ${CARD} 
                sed -i "s|@MISTAGTIGHTTOPZ|1.01            |g" ${CARD} 
                sed -i "s|@MISTAGTIGHTTOPW|1.15            |g" ${CARD} 
                sed -i "s|@MISTAGTIGHTVVZ|1.05           |g"  ${CARD} 
                sed -i "s|@MISTAGTIGHTVVW|1.10           |g"  ${CARD} 
                sed -i "s|@MISTAGTIGHTVG|1.01          |g"   ${CARD} 

                sed -i '/CMS.*mistag.*stat.*loose.*shape.*/d' ${CARD}
            fi

            sed -i "s|combined_model.root|../root/combined_model_monov_${TAGGER}_${WP}.root|g" ${CARD}
            # only for the nominal tagger we apply the data-driven qcd, otherwise use the old qcd prediction
            if [ "$TAGGER" == nominal ]; then
                sed -i "s|monov${WP}_qcd_ws.root|../root/monov${WP}_qcd_ws.root|g" ${CARD}
            else
                sed -i "/qcd_ws/d" ${CARD}
                sed -i "/qcdclosure/d" ${CARD}
            fi

            # Remove useless stat uncertainties
            # Uncertainties are removed if they do not have a variation histogram available
            # The criteria for whether a variation histogram is present are defined in
            # make_ws.py
            rootls -1 root/ws_monov_nominal_${WP}.root:category_monov${WP}_${YEAR} > tmp_histdump
            for NUIS in $(grep shape ${CARD} | awk '{print $1}' | grep stat); do
              if [ $(grep -c ${NUIS}Up tmp_histdump) -eq 0 ]; then
                 sed -i "/^${NUIS} .*/d" ${CARD}
                 echo "Warning: removing nuisance ${NUIS} from ${CARD}, shape not present in ws_monov_nominal_${WP}.root"
              fi
            done
            rm tmp_histdump

            pushd cards
            text2workspace.py ${CARD} --channel-masks
            python $CMSSW_BASE/src/HiggsAnalysis/CombinedLimit/test/systematicsAnalyzer.py --all -f html ${CARD} > systematics_${TAGGER}_monov${WP}_${YEAR}.html
            popd
        done
    done

    pushd cards
    ### COMBINED TAGGER CARDS
    for TAGGER in nominal; do
        COMBINED=card_${TAGGER}_monov_${YEAR}.txt
        combineCards.py  card_${TAGGER}_monovloose_${YEAR}.txt \
                        card_${TAGGER}_monovtight_${YEAR}.txt \
                        > ${COMBINED}
        sed -i 's/ch\(1\|2\)_//g' ${COMBINED}
        text2workspace.py ${COMBINED} --channel-masks
        python $CMSSW_BASE/src/HiggsAnalysis/CombinedLimit/test/systematicsAnalyzer.py --all -f html ${COMBINED} > systematics_${TAGGER}_monov_${YEAR}.html
    done

    # ### TAU21 CARDS
    # CARD=card_tau21_monov_${YEAR}.txt
    # cp ../../../templates/card_template.txt ${CARD}
    # sed -i "s/@WP//g" ${CARD}
    # sed -i "s|@YEAR|${YEAR}|g" ${CARD}
    # sed -i "s|combined_model.root|../root/combined_model_monov_tau21.root|g" ${CARD}
    # sed -i "/qcd_ws/d" ${CARD}
    # sed -i "/qcdfit/d" ${CARD}
    # sed -i '/.*vmistag.*stat.*/d' ${CARD}
    # if [ $YEAR -eq 2017 ]; then
    #     sed -i "s|@LUMIXY|1.008|g" ${CARD}
    #     sed -i "s|@LUMILS|1.003|g" ${CARD}
    #     sed -i "s|@LUMIBBD|1.004|g" ${CARD}
    #     sed -i "s|@LUMIDB|1.005|g" ${CARD}
    #     sed -i "s|@LUMIBCC|1.003|g" ${CARD}
    #     sed -i "s|@LUMIGS|1.001|g" ${CARD}
    #     sed -i "s|@LUMI|1.020|g" ${CARD}
    # elif [ $YEAR -eq 2018 ]; then
    #     sed -i "s|@LUMIXY|1.02|g" ${CARD}
    #     sed -i "s|@LUMILS|1.002|g" ${CARD}
    #     sed -i "s|@LUMIBBD|1.0|g" ${CARD}
    #     sed -i "s|@LUMIDB|1.0|g" ${CARD}
    #     sed -i "s|@LUMIBCC|1.02|g" ${CARD}
    #     sed -i "s|@LUMIGS|1.00|g" ${CARD}
    #     sed -i "s|@LUMI|1.015|g" ${CARD}
    #     sed -i "/prefiring/d" ${CARD}
    # fi
    # sed -i "s|@VTAGLOOSE|-         |g"    ${CARD} 
    # sed -i "s|@VTAGTIGHT|-         |g"    ${CARD} 
    # sed -i "s|@MISTAGLOOSEW|-            |g"    ${CARD} 
    # sed -i "s|@MISTAGLOOSEZ|-            |g"    ${CARD} 
    # sed -i "s|@MISTAGLOOSEG|-            |g"    ${CARD} 
    # sed -i "s|@MISTAGTIGHTW|-            |g"    ${CARD} 
    # sed -i "s|@MISTAGTIGHTZ|-            |g"    ${CARD} 
    # sed -i "s|@MISTAGTIGHTG|-            |g"    ${CARD} 
    # sed -i "s|@MISTAGLOOSETOPZ|-               |g" ${CARD} 
    # sed -i "s|@MISTAGLOOSETOPW|-               |g" ${CARD} 
    # sed -i "s|@MISTAGLOOSEVVZ|-                |g"  ${CARD} 
    # sed -i "s|@MISTAGLOOSEVVW|-              |g"  ${CARD} 
    # sed -i "s|@MISTAGTIGHTTOPZ|-               |g" ${CARD} 
    # sed -i "s|@MISTAGTIGHTTOPW|-               |g" ${CARD} 
    # sed -i "s|@MISTAGTIGHTVVZ|-              |g"  ${CARD} 
    # sed -i "s|@MISTAGTIGHTVVW|-              |g"  ${CARD} 
    # sed -i "s|@MISTAGTIGHTVG|-             |g"   ${CARD} 
    # text2workspace.py ${CARD} --channel-masks
    # python $CMSSW_BASE/src/HiggsAnalysis/CombinedLimit/test/systematicsAnalyzer.py --all -f html ${CARD} > systematics_tau21_monov_${YEAR}.html

    popd
done


pushd cards
# Combine across years
for TAGGER in nominal; do
    COMBINED=card_${TAGGER}_monov_combined.txt
    combineCards.py card_${TAGGER}_monov_201*.txt > ${COMBINED}
    sed -i 's/ch\(1\|2\)_//g' ${COMBINED}
    text2workspace.py ${COMBINED} --channel-masks
    python $CMSSW_BASE/src/HiggsAnalysis/CombinedLimit/test/systematicsAnalyzer.py --all -f html ${COMBINED} > systematics_${TAGGER}_monov_combined.html

    for WP in loose tight; do
        COMBINED=card_${TAGGER}_monov${WP}_combined.txt
        combineCards.py card_${TAGGER}_monov${WP}_201*.txt > ${COMBINED}
        sed -i 's/ch\(1\|2\)_//g' ${COMBINED}
        text2workspace.py ${COMBINED} --channel-masks
        python $CMSSW_BASE/src/HiggsAnalysis/CombinedLimit/test/systematicsAnalyzer.py --all -f html ${COMBINED} > systematics_${TAGGER}_monov${WP}_combined.html
    done

    # COMBINED=card_tau21_monov_combined.txt
    # combineCards.py card_tau21_monov_201*.txt > ${COMBINED}
    # sed -i 's/ch\(1\|2\)_//g' ${COMBINED}
    # text2workspace.py ${COMBINED} --channel-masks
    # python $CMSSW_BASE/src/HiggsAnalysis/CombinedLimit/test/systematicsAnalyzer.py --all -f html ${COMBINED} > systematics_tau21_monov_combined.html
done
popd
