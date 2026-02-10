source /cvmfs/cms.cern.ch/cmsset_default.sh
cmsenv

alias python="python3"

export FIT_FRAMEWORK_PATH="$(pwd -P)"
export PYTHONPATH="${FIT_FRAMEWORK_PATH}:${PYTHONPATH}"