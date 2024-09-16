#!/bin/bash

## Upload plots to LXPlus EOS WWW area

VERSIONTAG=${1}

TOPDIR="/eos/user/a/aakpinar/www/ul/fit"
TARGETDIR_CRONLYFIT="${TOPDIR}/${VERSIONTAG}/CROnlyFit"
TARGETDIR_SRCRFIT="${TOPDIR}/${VERSIONTAG}/SRCRFit"

# Log on to LXPlus and set up the directory structure
ssh -XY aakpinar@lxplus.cern.ch << EOF
cd ${TOPDIR}

mkdir -p "${TARGETDIR_CRONLYFIT}/2017"
mkdir -p "${TARGETDIR_CRONLYFIT}/2018"
mkdir -p "${TARGETDIR_SRCRFIT}/2017"
mkdir -p "${TARGETDIR_SRCRFIT}/2018"

# Copy index.php to all directories
cp index.php "${TOPDIR}/${VERSIONTAG}"

cp index.php ${TARGETDIR_CRONLYFIT}
cp index.php ${TARGETDIR_SRCRFIT}

cp index.php "${TARGETDIR_CRONLYFIT}/2017"
cp index.php "${TARGETDIR_CRONLYFIT}/2018"
cp index.php "${TARGETDIR_SRCRFIT}/2017"
cp index.php "${TARGETDIR_SRCRFIT}/2018"
EOF

# Back to LPC
for YEAR in 2017 2018; do
    # CR-only fit plots
    pushd "plotsCROnlyFit/${YEAR}"
    scp *pdf *png aakpinar@lxplus.cern.ch:${TARGETDIR_CRONLYFIT}/${YEAR}
    popd
    
    # SR+CR fit plots
    pushd "plotsSRAndCRFit/${YEAR}"
    scp *pdf *png aakpinar@lxplus.cern.ch:${TARGETDIR_SRCRFIT}/${YEAR}
    popd
done