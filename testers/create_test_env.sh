#!/usr/bin/env bash

if [[ $# -lt 4 || $# -gt 5 ]]; then
    echo usage: $0 autotest_working_dir tester_name python_version course_name env_name
    exit 1
fi

THISSCRIPT=$(readlink -f ${BASH_SOURCE})
THISSCRIPTDIR=$(dirname ${THISSCRIPT})
WORKINGDIR=$1
TESTERNAME=$2
PYVERSION=$3
COURSENAME=$4
SPECSDIR=${WORKINGDIR}/specs/${COURSENAME}
VENVDIR=${WORKINGDIR}/venvs/${COURSENAME}
if [ $# -eq 5 ]; then
    ENVNAME=$5
    SPECSDIR=${SPECSDIR}/${ENVNAME}
    VENVDIR=${VENVDIR}/${ENVNAME}
fi
TESTERDIR=${THISSCRIPTDIR}/${TESTERNAME}

if pushd ${TESTERDIR}; then
    echo "Creating specs directory ${SPECSDIR}"
    mkdir -p ${SPECSDIR}
    if [[ -e init_test_env.sh ]]; then
        ./init_test_env.sh ${TESTERDIR} ${SPECSDIR}
    fi
    echo "Creating virtualenv ${VENVDIR}"
    python${PYVERSION} -m venv ${VENVDIR}
    source ${VENVDIR}/bin/activate
    pip install wheel
    if [ -e requirements.txt ]; then
        pip install -r requirements.txt
    fi
    echo "$(pwd)/server" > ${VENVDIR}/lib/python${PYVERSION}/site-packages/markus_${TESTERNAME}.pth
    cd ..
    echo "$(pwd)" > ${VENVDIR}/lib/python${PYVERSION}/site-packages/markus.pth
    popd
else
    echo "The tester ${TESTERNAME} does not exist"
fi
