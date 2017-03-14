#!/usr/bin/env bash

if [ $# -ne 1 ]; then
	echo usage: $0 jdbc_dir sql_dir
	exit 1
fi

JDBCDIR=$1
SQLDIR=$2
SOLUTIONDIR=${JDBCDIR}/solution
DATASETDIR=${SOLUTIONDIR}/datasets
PATHTOJAR=/path/to/jar

echo "[JDBC] Installing system packages"
sudo apt-get install openjdk-8-jre
echo "[JDBC] Installing SQL tester"
cd ${SQLDIR}
./install.sh ${SQLDIR}
echo "[JDBC] Creating solution"
cd ${SOLUTIONDIR}
javac -cp .:${PATHTOJAR} *.java
chmod go-rwx *.java
for datafile in ${DATASETDIR}/*; do
	schemaname=$(basename -s .sql ${datafile})
	# TODO Repeat the variables or import them somehow
	java -cp .:${PATHTOJAR} SubmissionOracle ${SERVERDB} ${SERVERUSER} ${SERVERPWD} ${schemaname}
	psql -U ${SERVERUSER} -d ${SERVERDB} -h localhost <<-EOF
		GRANT SELECT ON ALL TABLES IN SCHEMA ${schemaname} TO ${TESTUSER};
	EOF
done
# TODO Think about the oracle/solution java files and how to connect them to MarkusJDBCTester.java
echo "[JDBC] Updating python config file"
echo "PATH_TO_JDBC_JAR = '""${PATHTOJAR}""'" >| ${JDBCDIR}/server/markus_jdbc_config.py
