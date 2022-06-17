
### Asimov limit
mkdir -p limit
pushd limit

# Print out the current version of the limit script
FILEPATH="`dirname $0`/`basename $0`"
cat ${FILEPATH} > "limitScript.sh"

# Limits per year
for YEAR in 2017 2018; do
    combine -M AsymptoticLimits -n _vbf_${YEAR} ../cards/card_vbf_${YEAR}.root | tee log_limits_${YEAR}.txt
    
    combine -M AsymptoticLimits -n _vbf_nodilepton_${YEAR} \
        --setParameters mask_vbf_${YEAR}_dielec=1,mask_vbf_${YEAR}_dimuon=1 \
        ../cards/card_vbf_${YEAR}.root | tee log_limits_nodilepton_${YEAR}.txt
    
    combine -M AsymptoticLimits -t -1 -n _vbf_${YEAR} ../cards/card_vbf_${YEAR}.root | tee log_asimov_${YEAR}.txt
    
    combine -M AsymptoticLimits -t -1 -n _vbf_nodilepton_${YEAR} \
        --setParameters mask_vbf_${YEAR}_dielec=1,mask_vbf_${YEAR}_dimuon=1 \
        ../cards/card_vbf_${YEAR}.root | tee log_asimov_nodilepton_${YEAR}.txt
done

# combine -M AsymptoticLimits -n _vbf_combined ../cards/card_vbf_combined.root | tee log_limits_combined.txt

# combine -M AsymptoticLimits -n _vbf_nodilepton_combined \
#     --setParameters mask_vbf_2017_dimuon=1,mask_vbf_2017_dielec=1,mask_vbf_2018_dimuon=1,mask_vbf_2018_dielec=1 \
#     ../cards/card_vbf_combined.root | tee log_limits_nodilepton_combined.txt

# combine -M AsymptoticLimits -t -1 -n _vbf_combined ../cards/card_vbf_combined.root | tee log_asimov_combined.txt

# combine -M AsymptoticLimits -t -1 -n _vbf_nodilepton_combined \
#     --setParameters mask_vbf_2017_dimuon=1,mask_vbf_2017_dielec=1,mask_vbf_2018_dimuon=1,mask_vbf_2018_dielec=1 \
#     ../cards/card_vbf_combined.root | tee log_asimov_nodilepton_combined.txt

popd
