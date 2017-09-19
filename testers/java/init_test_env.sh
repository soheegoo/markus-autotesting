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
SOLUTIONDIRSRC=${WORKINGDIR}/solution
TESTSDIRSRC=${SOLUTIONDIRSRC}/tests
SOLUTIONDIRTGT=${SPECSDIR}/solution
TESTSDIRTGT=${SOLUTIONDIRTGT}/tests

echo "[JAVA] Copying and compiling solution"
cp -a ${SOLUTIONDIRSRC} ${SPECSDIR}
pushd ${JAMDIR} > /dev/null
./compile_tests.sh ${TESTSDIRTGT} ${SOLUTIONDIRTGT}
popd > /dev/null
rm -f ${SOLUTIONDIRTGT}/*.java ${TESTSDIRTGT}/*.java
echo "[JAVA] Updating json specs file"
sed -i -e "s#/path/to/tests#${TESTSDIRTGT}#g" ${SPECSDIR}/specs.json
