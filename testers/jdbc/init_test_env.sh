#!/usr/bin/env bash

if [ $# -ne 2 ]; then
    echo "Usage: $0 autotest_working_dir specs_dir"
    exit 1
fi

THISSCRIPT=$(readlink -f ${BASH_SOURCE})
TESTERDIR=$(dirname ${THISSCRIPT})
WORKINGDIR=$(readlink -f $1)
SPECSDIR=$(readlink -f $2)
SPECS=${SPECSDIR}/specs.json
JARPATH=$(jq -r '.path_to_jdbc_jar' ${SPECS})
ORACLEDB=$(jq -r '.oracle_database' ${SPECS})
ORACLEUSER=${ORACLEDB}
TESTUSERS=( $(jq -r '.tests[] | .user' ${SPECS}) )
SOLUTIONDIR=${SPECSDIR}/solution
DATASETDIR=${SOLUTIONDIR}/datasets
SCHEMAFILE=${SOLUTIONDIR}/schema.ddl

echo "[JDBC] Compiling solutions"
cp -a ${WORKINGDIR}/solution ${SPECSDIR}
#TODO cp ${TESTERDIR}/server/MarkusJDBCTest.java ${SOLUTIONDIR} when getInputs is in the specs
javac -cp ${SOLUTIONDIR}:${JARPATH} ${SOLUTIONDIR}/*.java
chmod go-rwx ${SOLUTIONDIR}/*.java
echo "[JDBC] Loading solutions into the oracle database"
ALLTESTUSERS=$(IFS=,; echo "${TESTUSERS[*]}")
schemas=""
funcnames=( $(jq -r '.matrix | keys | map(select(. != "connection"))[]' ${SPECS}) )
for funcname in "${funcnames[@]}"; do
    datasets=( $(jq -r --arg q ${funcname} '.matrix | .[$q] | keys | map(select(. != "extra"))[]' ${SPECS}) )
    for datafile in "${datasets[@]}"; do
        schemaname=$(basename -s .sql ${datafile})
        if [[ "${schemas}" != *" ${schemaname} "* ]]; then # first time using this dataset, create a schema for it
            echo "[JDBC] Creating schema for dataset '${schemaname}'"
            echo "
                DROP SCHEMA IF EXISTS ${schemaname} CASCADE;
                CREATE SCHEMA ${schemaname};
                GRANT USAGE ON SCHEMA ${schemaname} TO ${ALLTESTUSERS};
                SET search_path TO ${schemaname};
            " | cat - ${SCHEMAFILE} ${DATASETDIR}/${datafile} >| /tmp/ate.sql
            psql -U ${ORACLEUSER} -d ${ORACLEDB} -h localhost -f /tmp/ate.sql
            schemas="${schemas} ${schemaname} "
        fi
        echo "[JDBC] Creating solution table '${funcname}' for dataset '${schemaname}'"
        echo "
            CREATE TABLE ${schemaname}.${funcname} (
                id serial PRIMARY KEY,
                java_output bytea
            );
            GRANT SELECT ON ${schemaname}.${funcname} TO ${ALLTESTUSERS};
        " >| /tmp/ate.sql
        psql -U ${ORACLEUSER} -d ${ORACLEDB} -h localhost -f /tmp/ate.sql
        java -cp ${SOLUTIONDIR}:${JARPATH} MarkusJDBCTest ${ORACLEDB} ${ORACLEUSER} placeholder ${funcname} ${schemaname}
    done
done
rm /tmp/ate.sql
echo '[JDB] Updating json specs file'
sed -i -e "s#/path/to/solution#${SOLUTIONDIR}#g" ${SPECS}
