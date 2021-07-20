
### Asimov limit
mkdir -p limit
pushd limit

# Print out the current version of the limit script
FILEPATH="`dirname $0`/`basename $0`"
cat ${FILEPATH} > "limitScript.sh"

for YEAR in 2017 2018; do
    combine -M AsymptoticLimits -t -1 -n _vbf_${YEAR} ../cards/card_vbf_${YEAR}.root | tee log_limits_${YEAR}.txt
    combine -M AsymptoticLimits -t -1 -n _vbf_nophoton_${YEAR} --setParameters mask_vbf_${YEAR}_photon=1 ../cards/card_vbf_${YEAR}.root | tee log_limits_nophoton_${YEAR}.txt
done

combine -M AsymptoticLimits -t -1 -n _vbf_combined ../cards/card_vbf_combined.root | tee log_limits_combined.txt
combine -M AsymptoticLimits -t -1 -n _vbf_nophoton_combined --setParameters mask_vbf_2017_photon,mask_vbf_2018_photon=1 ../cards/card_vbf_combined.root | tee log_limits_nophoton_combined.txt
popd
