#!/usr/bin/env bash

set -e

remove_schema_sql() {
    local tester_name=$(basename ${ENV_DIR})
    local files_json=$(echo ${SETTINGS_JSON} | jq --compact-output '.test_data | .[] | .query_files | .[] |
                                                                    {query_file: .query_file, data_files: .data_files}')
    for entry_json in ${files_json}; do
        local data_files=$(echo ${entry_json} | jq --raw-output '.data_files | .[]')
        for data_file in ${data_files}; do
            local schema_name="${tester_name}_$(basename -s .sql ${data_file})"
            echo "DROP SCHEMA IF EXISTS ${schema_name} CASCADE;"
        done
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

# vars
SETTINGS_JSON=$1
ENV_DIR=$(echo ${SETTINGS_JSON} | jq --raw-output .env_loc)

# main
remove_solution
