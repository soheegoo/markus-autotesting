#!/usr/bin/env bash

if [ $# -ne 2 ]; then
    echo usage: $0 autotest_working_dir specs_dir
    exit 1
fi

THISSCRIPT=$(readlink -f ${BASH_SOURCE})
TESTERDIR=$(dirname ${THISSCRIPT})
WORKINGDIR=$(readlink -f $1)
SPECSDIR=$(readlink -f $2)
SPECS=${SPECSDIR}/specs.json
ORACLEDB=$(jq -r '.oracle_database' ${SPECS})
ORACLEUSER=${ORACLEDB}
TESTDBS=( $(jq -r '.tests[] | .database' ${SPECS}) )
TESTUSERS=( $(jq -r '.tests[] | .user' ${SPECS}) )
TESTPWDS=( $(jq -r '.tests[] | .password' ${SPECS}) )
SOLUTIONDIR=${SPECSDIR}/solution
DATASETDIR=${SOLUTIONDIR}/datasets
QUERYDIR=${SOLUTIONDIR}/queries
SCHEMAFILE=${SOLUTIONDIR}/schema.ddl

echo "[SQL] Creating databases and users (you'll be asked to create a password for the oracle user ${ORACLEUSER})"
sudo -u postgres createuser -P ${ORACLEUSER} # secure, password is not logged
sudo -u postgres psql <<-EOF
	DROP DATABASE IF EXISTS ${ORACLEDB};
	CREATE DATABASE ${ORACLEDB} OWNER ${ORACLEUSER};
	\connect ${ORACLEDB}
	DROP SCHEMA IF EXISTS public CASCADE;
EOF
for i in "${!TESTDBS[@]}"; do
	sudo -u postgres psql <<-EOF
		CREATE ROLE ${TESTUSERS[i]} LOGIN PASSWORD '${TESTPWDS[i]}';
		DROP DATABASE IF EXISTS ${TESTDBS[i]};
		CREATE DATABASE ${TESTDBS[i]} OWNER ${TESTUSERS[i]};
		\connect ${TESTDBS[i]}
		DROP SCHEMA IF EXISTS public CASCADE;
	EOF
done
echo "[SQL] Loading solutions into the oracle database"
cp -a ${WORKINGDIR}/solution ${SPECSDIR}
chmod go-rwx ${QUERYDIR}
schemas=""
queries=( $(jq -r '.matrix | keys[]' ${SPECS}) )
for queryfile in "${queries[@]}"; do
    queryname=$(basename -s .sql ${queryfile})
    datasets=( $(jq -r --arg q ${queryfile} '.matrix | .[$q] | keys | map(select(. != "extra"))[]' ${SPECS}) )
    for datafile in "${datasets[@]}"; do
        schemaname=$(basename -s .sql ${datafile})
        users=$(IFS=,; echo "${TESTUSERS[*]}")
        if [[ "${schemas}" != *" ${schemaname} "* ]]; then # first time using this dataset, create a schema for it
            echo "[SQL] Creating schema for dataset '${schemaname}'"
            echo "
                DROP SCHEMA IF EXISTS ${schemaname} CASCADE;
                CREATE SCHEMA ${schemaname};
                GRANT USAGE ON SCHEMA ${schemaname} TO ${users};
                SET search_path TO ${schemaname};
            " | cat - ${SCHEMAFILE} ${DATASETDIR}/${datafile} >| /tmp/ate.sql
            psql -U ${ORACLEUSER} -d ${ORACLEDB} -h localhost -f /tmp/ate.sql
            schemas="${schemas} ${schemaname} "
        fi
        echo "[SQL] Creating solution table '${queryname}' for dataset '${schemaname}'"
        echo "SET search_path TO ${schemaname};" | cat - ${QUERYDIR}/${queryfile} >| /tmp/ate.sql
        echo "GRANT SELECT ON ${schemaname}.${queryname} TO ${users};" >> /tmp/ate.sql
        psql -U ${ORACLEUSER} -d ${ORACLEDB} -h localhost -f /tmp/ate.sql
    done
done
rm /tmp/ate.sql
echo '[SQL] Updating json specs file'
sed -i -e "s#/path/to/solution#${SOLUTIONDIR}#g" ${SPECS}
