#!/usr/bin/env bash

set -e

remove_schema_sql() {
    local tester_name=$(basename ${ENV_DIR})
    local data_files=$(echo ${SETTINGS_JSON} | jq --raw-output '[.test_data[] | .class_files[] | .class_methods[]? |
                                                                .data_files[]? | .data_file] | unique[]')
    for data_file in ${data_files}; do
        local schema_name="${tester_name}_$(basename -s .sql ${data_file})"
        echo "DROP SCHEMA IF EXISTS ${schema_name} CASCADE; "        
    done
}

remove_solution() {
    local oracle_db=$(echo ${SETTINGS_JSON} | jq --raw-output .install_data.oracle_database)
    local oracle_user=${oracle_db}
    psql -U ${oracle_user} -d ${oracle_db} -h localhost -f <(remove_schema_sql)
}

# script starts here
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 settings_json"
    exit 1
fi

#vars
SETTINGS_JSON=$1
ENV_DIR=$(echo ${SETTINGS_JSON} | jq --raw-output .env_loc)

#main
remove_solution
