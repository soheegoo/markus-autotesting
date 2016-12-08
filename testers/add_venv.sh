#!/usr/bin/env bash

if [ $# -ne 3 ]; then
    echo usage: $0 tester_name venv_name python_version
    exit 1
fi

TESTERNAME=$1
VENVNAME=$2
PYVERSION=$3
VENVSNAME=venvs
PATHNAME=server

if cd ${TESTERNAME}; then
	VENVDIR=../../${VENVSNAME}/${VENVNAME}
	pyvenv-${PYVERSION} ${VENVDIR}
	source ${VENVDIR}/bin/activate
	pip install wheel
	if [ -f requirements.txt ]; then
		pip install -r requirements.txt
	fi
	echo "$(pwd)/${PATHNAME}" > ${VENVDIR}/lib/python${PYVERSION}/site-packages/markus_${TESTERNAME}.pth
	cd ..
	echo "$(pwd)" > ${VENVDIR}/lib/python${PYVERSION}/site-packages/markus.pth
else
    echo "The tester ${TESTERNAME} does not exist"
fi
