#!/usr/bin/env bash

if [[ $# -lt 1 || $# -gt 4 || $# -eq 2 ]]; then
	echo "Usage: $0 jdbc_jar_path [oracle_user] [test_user] [num_users]"
	exit 1
fi

JARPATH=$(readlink -f $1)
if [[ $# -eq 1 ]]; then
    echo "[JDBC] Reusing already installed SQL tester"
else
    THISSCRIPT=$(readlink -f ${BASH_SOURCE})
    TESTERDIR=$(dirname ${THISSCRIPT})
    ORACLEUSER=$1
    TESTUSER=$2
    echo "[JDBC] Installing SQL tester"
    if [[ $# -eq 4 ]]; then
        NUMUSERS=$3
        ${TESTERDIR}/../sql/install.sh ${ORACLEUSER} ${TESTUSER} ${NUMUSERS}
    else
        ${TESTERDIR}/../sql/install.sh ${ORACLEUSER} ${TESTUSER}
    fi
fi

echo "[JDBC] Installing system packages"
sudo apt-get install python3 openjdk-9-jre
echo "[JDBC] Updating json specs file"
ORACLEDB=$(awk "/oracle_database" ${TESTERDIR}/../sql/specs.json)
sed -i -e "s#oracle_database#c\\${ORACLEDB}" ${TESTERDIR}/specs.json
TESTS=$(awk "/tests" ${TESTERDIR}/../sql/specs.json)
sed -i -e "s#tests#c\\${TESTS}" ${TESTERDIR}/specs.json
sed -i -e "s#/path/to/jdbc/jar#${JARPATH}#g" ${TESTERDIR}/specs.json
