#!/bin/bash
set -e

INDIR=${1}
TAG="${2}"
INDIR="$(readlink -e $INDIR)"

OUTDIR="../monojet/$(basename $INDIR)/${TAG}/root"
mkdir -p ${OUTDIR}
OUTDIR="$(readlink -e ${OUTDIR})"

# Save some information so we can trace inputs
INFOFILE=${OUTDIR}/INFO.txt
echo "Input directory: ${INDIR}" > ${INFOFILE}
echo "--- INPUT ---" > ${INFOFILE}

INFILE=${INDIR}/legacy_limit_monojet.root
WSFILE=${OUTDIR}/ws_monojet.root

# Save the check sum for the input
md5sum ${INFILE} >> ${INFOFILE}

# Save repo information to the info file
echo "--- REPO INFO ---" >> ${INFOFILE}
echo "Commit hash: $(git rev-parse HEAD)" >> ${INFOFILE}
echo "Branch name: $(git rev-parse --abbrev-ref HEAD)" >> ${INFOFILE}
git diff >> ${INFOFILE}

./make_ws.py ${INFILE} \
             --out ${WSFILE} \
             --categories monojet_2017

./runModel.py ${WSFILE} --categories monojet_2017 \
                        --out ${OUTDIR}/combined_model_monojet.root

cp sys/monojet_qcd_ws.root ${OUTDIR}

# Save the check sums for the output
echo "--- OUTPUT ---" >> ${INFOFILE}
md5sum ${OUTDIR}/*root >> ${INFOFILE}

ln -fs $(readlink -e ../monojet/templates/Makefile) ${OUTDIR}/../Makefile

pushd ${OUTDIR}/..
make cards
popd

echo $(readlink -e ../monojet/$(basename $INDIR)/${TAG})
