
### Asimov limit
mkdir -p limit
pushd limit

# Print out the current version of the limit script
FILEPATH="`dirname $0`/`basename $0`"
cat ${FILEPATH} > "limitScript.sh"

# Limits per year
for YEAR in 2017 2018; do
    combine -M AsymptoticLimits -n _vbf_${YEAR} ../cards/card_vbf_${YEAR}.root | tee log_limits_${YEAR}.txt
done

combine -M AsymptoticLimits -n _vbf_combined ../cards/card_vbf_combined.root | tee log_limits_combined.txt

popd
