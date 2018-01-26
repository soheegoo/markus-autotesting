#!/usr/bin/env bash

compile_solution() {
    local jamdir=${TESTERDIR}/uam-git/jam

    echo "[JAVA] Compiling solution"
    cp -a ${WORKINGDIR}/solution ${SPECSDIR}
    pushd ${jamdir} > /dev/null
    ./compile_tests.sh ${TESTSDIR} ${SOLUTIONDIR}
    popd > /dev/null
    rm -f ${SOLUTIONDIR}/*.java ${TESTSDIR}/*.java
}

update_specs() {
    echo "[JAVA] Updating json specs file"
    sed -i -e "s#/path/to/tests#${TESTSDIR}#g" ${SPECSDIR}/specs.json
}

# script starts here
if [ $# -ne 2 ]; then
	echo usage: $0 autotest_working_dir specs_dir
	exit 1
fi

# vars
THISSCRIPT=$(readlink -f ${BASH_SOURCE})
TESTERDIR=$(dirname ${THISSCRIPT})
WORKINGDIR=$(readlink -f $1)
SPECSDIR=$(readlink -f $2)
SOLUTIONDIR=${SPECSDIR}/solution
TESTSDIR=${SOLUTIONDIR}/tests

# main
compile_solution
update_specs
