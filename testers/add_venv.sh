#!/usr/bin/env bash

if [ $# -ne 4 ]; then
    echo usage: $0 autotest_working_dir tester_name venv_name python_version
    exit 1
fi

WORKINGDIR=$1
TESTERNAME=$2
VENVNAME=$3
PYVERSION=$4
VENVSDIR=$1/venvs
VENVDIR=${VENVSDIR}/${VENVNAME}

if cd ${TESTERNAME}; then
	pyvenv-${PYVERSION} ${VENVDIR}
	source ${VENVDIR}/bin/activate
	pip install wheel
	if [ -f requirements.txt ]; then
		pip install -r requirements.txt
	fi
	echo "$(pwd)/server" > ${VENVDIR}/lib/python${PYVERSION}/site-packages/markus_${TESTERNAME}.pth
	cd ..
	echo "$(pwd)" > ${VENVSDIR}/${VENVNAME}/lib/python${PYVERSION}/site-packages/markus.pth
else
    echo "The tester ${TESTERNAME} does not exist"
fi
