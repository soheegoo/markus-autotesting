#!/usr/bin/env bash

if [ $# -ne 2 ]; then
    echo usage: $0 autotest_working_dir specs_dir
    exit 1
fi

THISSCRIPT=$(readlink -f ${BASH_SOURCE})
TESTERDIR=$(dirname ${THISSCRIPT})
WORKINGDIR=$(readlink -f $1)
SPECSDIR=$(readlink -f $2)
SPECS=${TESTERDIR}/specs.json
ORACLEDB=$(jq -r '.oracle_database' ${SPECS})
ORACLEUSER=${ORACLEDB}
TESTDB=$(jq -r '.test_database' ${SPECS})
TESTUSER=$(jq -r '.user_name' ${SPECS})
TESTPWD=$(jq -r '.user_password' ${SPECS})
SOLUTIONDIR=${SPECSDIR}/solution
DATASETDIR=${SOLUTIONDIR}/datasets
QUERYDIR=${SOLUTIONDIR}/queries
SCHEMAFILE=${SOLUTIONDIR}/schema.ddl

echo "[SQL] Creating databases and users (you'll be asked to create a password for the oracle user ${ORACLEUSER})"
sudo -u postgres createuser -P ${ORACLEUSER}
sudo -u postgres psql <<-EOF
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
echo "[SQL] Loading solutions into the oracle database"
cp -a ${WORKINGDIR}/solution ${SPECSDIR}
schemas=""
chmod go-rwx ${QUERYDIR}
while read queryfile; do
    queryname=$(basename -s .sql ${queryfile})
    while read datafile; do
        schemaname=$(basename -s .sql ${datafile})
        if [[ "${schemas}" != *" ${schemaname} "* ]]; then # first time using this dataset, create a schema for it
            echo "[SQL] Creating schema for dataset '${schemaname}'"
            echo "
                DROP SCHEMA IF EXISTS ${schemaname} CASCADE;
                CREATE SCHEMA ${schemaname};
                GRANT USAGE ON SCHEMA ${schemaname} TO ${TESTUSER};
                SET search_path TO ${schemaname};
            " | cat - ${SCHEMAFILE} ${DATASETDIR}/${datafile} >| /tmp/ate.sql
            psql -U ${ORACLEUSER} -d ${ORACLEDB} -h localhost -f /tmp/ate.sql
            schemas="${schemas} ${schemaname} "
        fi
        echo "[SQL] Creating solution table '${queryname}' for dataset '${schemaname}'"
        echo "SET search_path TO ${schemaname};" | cat - ${QUERYDIR}/${queryfile} >| /tmp/ate.sql
        echo "GRANT SELECT ON ${schemaname}.${queryname} TO ${TESTUSER};" >> /tmp/ate.sql
        psql -U ${ORACLEUSER} -d ${ORACLEDB} -h localhost -f /tmp/ate.sql
    done <<< $(jq -r --arg q ${queryfile} '.matrix | .[$q] | keys | map(select(. != "extra"))[]' ${SPECS})
done <<< $(jq -r '.matrix | keys[]' ${SPECS})
rm /tmp/ate.sql
echo '[SQL] Updating json specs file'
sed -i -e "s#/path/to/solution#${SOLUTIONDIR}#g" ${SPECS}
