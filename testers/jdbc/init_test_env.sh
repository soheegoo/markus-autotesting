#!/usr/bin/env bash

if [ $# -ne 2 ]; then
    echo "Usage: $0 autotest_working_dir specs_dir"
    exit 1
fi

WORKINGDIR=$(readlink -f $1)
SPECSDIR=$(readlink -f $2)
SPECS=${SPECSDIR}/specs.json

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
