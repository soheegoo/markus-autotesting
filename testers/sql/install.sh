#!/usr/bin/env bash

if [ $# -ne 1 ]; then
	echo usage: $0 sql_dir
	exit 1
fi

SQLDIR=$1
SPECS=${SQLDIR}/specs.json
SOLUTIONDIR=${SQLDIR}/solution
DATASETDIR=${SOLUTIONDIR}/datasets
QUERYDIR=${SOLUTIONDIR}/queries
SCHEMAFILE=${SOLUTIONDIR}/schema.ddl

ORACLEUSER=ateserver
ORACLEPWD=x
ORACLEDB=$(jq -r '.oracle_database' ${SPECS})
TESTPWD=$(jq -r '.user_password' ${SPECS})
TESTUSER=$(jq -r '.user_name' ${SPECS})
TESTDB=$(jq -r '.test_database' ${SPECS})

echo "[SQL] Installing system packages"
sudo apt-get install python3 postgresql
echo "[SQL] Creating databases and users"
sudo -u postgres psql <<-EOF
	CREATE ROLE ${ORACLEUSER} LOGIN PASSWORD '${ORACLEPWD}';
	CREATE ROLE ${TESTUSER} LOGIN PASSWORD '${TESTPWD}';
	DROP DATABASE IF EXISTS ${ORACLEDB};
	DROP DATABASE IF EXISTS ${TESTDB};
	CREATE DATABASE ${ORACLEDB} OWNER ${ORACLEUSER};
	CREATE DATABASE ${TESTDB} OWNER ${TESTUSER};
	\connect ${ORACLEDB}
	DROP SCHEMA IF EXISTS public CASCADE;
	\connect ${TESTDB}
	DROP SCHEMA IF EXISTS public CASCADE;
EOF
echo "[SQL] Creating solutions"
schemas=""
chmod go-rwx ${QUERYDIR}
jq -r '.matrix | keys[]' ${SPECS} | while read queryfile; do
	queryname=$(basename -s .sql ${queryfile})
	jq -r --arg q ${queryfile} '.matrix | .[$q] | keys | map(select(. != "extra"))[]' ${SPECS} | while read datafile; do
		schemaname=$(basename -s .sql ${datafile})
		echo "${schemas}"
		if [[ "${schemas}" != *${schemaname}* ]]; then # first time using this dataset, create a schema for it
			echo "[SQL] Creating schema for data '${schemaname}'"
			psql -U ${ORACLEUSER} -d ${ORACLEDB} -h localhost <<-EOF
				DROP SCHEMA IF EXISTS ${schemaname} CASCADE;
				CREATE SCHEMA ${schemaname};
				GRANT USAGE ON SCHEMA ${schemaname} TO ${TESTUSER};
			EOF
			echo "SET search_path TO ${schemaname};" | cat - ${SCHEMAFILE} ${DATASETDIR}/${datafile} >| /tmp/ate.sql
			psql -U ${ORACLEUSER} -d ${ORACLEDB} -h localhost -f /tmp/ate.sql
			schemas="${schemas} ${schemaname}"
		fi
		echo "${schemas}"
		echo "[SQL] Creating solution '${queryname}' for data '${schemaname}'"
		echo "SET search_path TO ${schemaname};" | cat - ${QUERYDIR}/${queryfile} >| /tmp/ate.sql
		psql -U ${ORACLEUSER} -d ${ORACLEDB} -h localhost -f /tmp/ate.sql
		psql -U ${ORACLEUSER} -d ${ORACLEDB} -h localhost <<-EOF
			GRANT SELECT ON ${schemaname}.${queryname} TO ${TESTUSER};
		EOF
	done
done
rm /tmp/ate.sql
echo '[SQL] Updating json specs file'
sed -i -e "s#/path/to/solution#${SOLUTIONDIR}#g" ${SPECS}
