#!/usr/bin/env bash

if [ $# -ne 1 ]; then
	echo usage: $0 sql_dir
	exit 1
fi

SQLDIR=$1
SOLUTIONDIR=${SQLDIR}/solution
DATASETDIR=${SOLUTIONDIR}/datasets
QUERYDIR=${SOLUTIONDIR}/queries
SCHEMAFILE=${SOLUTIONDIR}/schema.ddl
SERVERDB=ate_oracle
SERVERUSER=ateserver
SERVERPWD=YOUR_SERVER_PASSWORD
TESTDB=ate_tests
TESTUSER=atetest
TESTPWD=YOUR_TEST_PASSWORD

echo "[SQL] Installing system packages"
sudo apt-get install python3 postgresql
echo "[SQL] Populating database with solutions"
chmod go-rwx ${QUERYDIR}
sudo -u postgres psql <<-EOF
	CREATE ROLE ${SERVERUSER} LOGIN PASSWORD '${SERVERPWD}';
	CREATE ROLE ${TESTUSER} LOGIN PASSWORD '${TESTPWD}';
	DROP DATABASE IF EXISTS ${SERVERDB};
	DROP DATABASE IF EXISTS ${TESTDB};
	CREATE DATABASE ${SERVERDB} OWNER ${SERVERUSER};
	CREATE DATABASE ${TESTDB} OWNER ${TESTUSER};
	\connect ${SERVERDB}
	DROP SCHEMA IF EXISTS public CASCADE;
	\connect ${TESTDB}
	DROP SCHEMA IF EXISTS public CASCADE;
EOF
for datafile in ${DATASETDIR}/*; do
	schemaname=$(basename -s .sql ${datafile})
	psql -U ${SERVERUSER} -d ${SERVERDB} -h localhost <<-EOF
		DROP SCHEMA IF EXISTS ${schemaname} CASCADE;
		CREATE SCHEMA ${schemaname};
		GRANT USAGE ON SCHEMA ${schemaname} TO ${TESTUSER};
	EOF
	echo "SET search_path TO ${schemaname};" | cat - ${SCHEMAFILE} >| /tmp/ate.sql
	psql -U ${SERVERUSER} -d ${SERVERDB} -h localhost -f /tmp/ate.sql
	echo "SET search_path TO ${schemaname};" | cat - ${datafile} >| /tmp/ate.sql
	psql -U ${SERVERUSER} -d ${SERVERDB} -h localhost -f /tmp/ate.sql
	for queryfile in ${QUERYDIR}/*; do
		queryname=$(basename -s .sql ${queryfile})
		if [[ ${schemaname} == ${queryname}* ]] || [[ ${schemaname} == all* ]]; then
			echo "SET search_path TO ${schemaname};" | cat - ${queryfile} >| /tmp/ate.sql
			psql -U ${SERVERUSER} -d ${SERVERDB} -h localhost -f /tmp/ate.sql
		fi
	done
	psql -U ${SERVERUSER} -d ${SERVERDB} -h localhost <<-EOF
		GRANT SELECT ON ALL TABLES IN SCHEMA ${schemaname} TO ${TESTUSER};
	EOF
done
rm /tmp/ate.sql
# TODO Should write settings to the config file
#echo "[SQL] Updating python config file"
