#!/usr/bin/env bash

set -e

get_query_files() {
python3 - <<EOPY
import json
with open('${ENVSETTINGS}') as f:
	settings = json.load(f)
solution_group = settings['solution_group']
files = set()
for group in solution_group:
	solution_file = group['solution_file_path']
	if solution_file not in files:
		print(solution_file)
	files.add(solution_file)
EOPY
}

get_datasets_from_query_file() {
python3 - <<EOPY
import json
with open('${ENVSETTINGS}') as f:
	settings = json.load(f)
solution_group = settings['solution_group']
for group in solution_group:
	if group['solution_file_path'] == '$1':
		print(group['dataset_file_path'])
EOPY
}

remove_schema_string() {
	echo "$(get_query_files)" | while read -r queryfile; do
		echo "$(get_datasets_from_query_file ${queryfile})" | while read -r datafile; do
    		local schemaname="${TESTERNAME}_$(basename -s .sql ${datafile})"
    		echo "DROP SCHEMA IF EXISTS ${schemaname} CASCADE;"
    	done
	done
}

remove_schemas() {
	local oracledb=$(get_install_setting oracle_database)
	local oracleuser=${oracledb}
	psql -U ${oracleuser} -d ${oracledb} -h localhost -f <(echo $(remove_schema_string))
}

get_setting() {
    cat ${ENVSETTINGS} | python3 -c "import sys, json; print(json.load(sys.stdin)['$1'])"
}

get_install_setting() {
	cat ${INSTALLSETTINGS} | python3 -c "import sys, json; print(json.load(sys.stdin)['$1'])"
}

# script starts here
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 environment_dir"
    exit 1
fi

ENVDIR=$(readlink -f $1)
TESTERNAME=$(basename ${ENVDIR})
ENVSETTINGS=${ENVDIR}/environment_settings.json

THISSCRIPT=$(readlink -f ${BASH_SOURCE})
BINDIR=$(dirname ${THISSCRIPT})
SPECSDIR=$(dirname ${BINDIR})/specs
INSTALLSETTINGS=${SPECSDIR}/install_settings.json

remove_schemas
