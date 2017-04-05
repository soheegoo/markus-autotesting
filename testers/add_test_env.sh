#!/usr/bin/env bash

if [ $# -ne 5 ]; then
    echo usage: $0 autotest_working_dir tester_name python_version course_name env_name
    exit 1
fi

WORKINGDIR=$1
TESTERNAME=$2
PYVERSION=$3
COURSENAME=$4
ENVNAME=$5
SPECSDIR=${WORKINGDIR}/specs/${COURSENAME}/${ENVNAME}
VENVDIR=${WORKINGDIR}/venvs/${COURSENAME}/${ENVNAME}

if cd ${TESTERNAME}; then
	echo "Creating specs directory ${SPECSDIR} (remember to add the specs.json file)"
	mkdir -p ${SPECSDIR}
	echo "Creating virtualenv ${VENVDIR}"
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
	echo "The tester ${TESTERNAME} does not exist"
fi
