#!/usr/bin/env bash

if [ $# -ne 2 ]; then
	echo usage: $0 autotest_working_dir specs_dir
	exit 1
fi

THISSCRIPT=$(readlink -f ${BASH_SOURCE})
TESTERDIR=$(dirname ${THISSCRIPT})
WORKINGDIR=$(readlink -f $1)
SPECSDIR=$(readlink -f $2)
JAMDIR=${TESTERDIR}/uam-git/jam
SOLUTIONDIR=${SPECSDIR}/solution
TESTSDIR=${SOLUTIONDIR}/tests

echo "[JAVA] Compiling solution"
cp -a ${WORKINGDIR}/solution ${SPECSDIR}
pushd ${JAMDIR} > /dev/null
./compile_tests.sh ${TESTSDIR} ${SOLUTIONDIR}
popd > /dev/null
rm -f ${SOLUTIONDIR}/*.java ${TESTSDIR}/*.java
echo "[JAVA] Updating json specs file"
sed -i -e "s#/path/to/tests#${TESTSDIR}#g" ${SPECSDIR}/specs.json
