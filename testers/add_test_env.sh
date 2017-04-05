#!/usr/bin/env bash

if [ $# -ne 4 ]; then
    echo usage: $0 autotest_working_dir tester_name python_version name
    exit 1
fi

WORKINGDIR=$1
TESTERNAME=$2
PYVERSION=$3
NAME=$4
SPECSDIR=${WORKINGDIR}/specs/${NAME}
VENVDIR=${WORKINGDIR}/venvs/${NAME}

if cd ${TESTERNAME}; then
	echo "[${NAME}] Creating specs directory ${SPECSDIR} (remember to add the specs.json file)"
	mkdir -p ${SPECSDIR}
	echo "[${NAME}] Creating virtualenv ${VENVDIR}"
	pyvenv-${PYVERSION} ${VENVDIR}
	source ${VENVDIR}/bin/activate
	pip install wheel
	if [ -f requirements.txt ]; then
		pip install -r requirements.txt
	fi
	echo "$(pwd)/server" > ${VENVDIR}/lib/python${PYVERSION}/site-packages/markus_${TESTERNAME}.pth
	cd ..
	echo "$(pwd)" > ${VENVDIR}/lib/python${PYVERSION}/site-packages/markus.pth
else
	echo "[${NAME}] The tester ${TESTERNAME} does not exist"
fi
