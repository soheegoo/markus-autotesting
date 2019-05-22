#!/usr/bin/env bash

set -e 

create_venv() {
    rm -rf ${VENV_DIR} # clean up existing venv if any
    python${PY_VERSION} -m venv ${VENV_DIR}
    source ${VENV_DIR}/bin/activate
    pip install wheel
    pip install -r <(echo ${PIP_REQUIREMENTS})
    local pth_file=${VENV_DIR}/lib/python${PY_VERSION}/site-packages/lib.pth
    echo ${TESTERS_DIR} >> ${pth_file}
}

move_files() {
    rm -rf ${SOLUTION_DIR}
    mv ${FILES_DIR} ${SOLUTION_DIR}
}

get_all_test_users() {
    echo ${SETTINGS_JSON} | jq --raw-output '.install_data | .tests | .[] | .user' | head -c -1 | tr '\n' ','
}

create_schema_sql() {
    local schema_name=$1
    local data_file=${SOLUTION_DIR}/$2
    local schema_file="${SOLUTION_DIR}/$(echo ${SETTINGS_JSON} | jq --raw-output .env_data.schema_file_path)"
    local all_test_users=$(get_all_test_users)
    echo "
        DROP SCHEMA IF EXISTS ${schema_name} CASCADE;
        CREATE SCHEMA ${schema_name};
        GRANT USAGE ON SCHEMA ${schema_name} TO ${all_test_users};
        SET search_path TO ${schema_name};
    " | cat - ${schema_file} ${data_file}
}

create_solution_sql() {
    local schema_name=$1
    local query_file=${SOLUTION_DIR}/$2
    local query_name=$(basename -s .sql ${query_file})
    local all_test_users=$(get_all_test_users)
    echo "
        SET search_path TO ${schema_name};
    " | cat - ${query_file} <(echo "GRANT SELECT ON ${schema_name}.${query_name} TO ${all_test_users};")
}

create_sql() {
    local schemas=""
    local tester_name=$(basename ${ENV_DIR})
    local files_json=$(echo ${SETTINGS_JSON} | jq --compact-output '.test_data | .[] | .query_files | .[] |
                                                                    {query_file: .query_file, data_files: .data_files}')
    for entry_json in ${files_json}; do
        local query_file=$(echo ${entry_json} | jq --raw-output .query_file)
        local data_files=$(echo ${entry_json} | jq --raw-output '.data_files | .[]')
        for data_file in ${data_files}; do
            local schema_name="${tester_name}_$(basename -s .sql ${data_file})"
            local schema_sql=""
            if [[ "${schemas}" != *" ${schema_name} "* ]]; then # first time using this dataset, create a schema for it
                schema_sql=$(create_schema_sql ${schema_name} ${data_file})
                schemas="${schemas} ${schema_name} "
            fi
            local solution_sql=$(create_solution_sql ${schema_name} ${query_file})
            echo "${schema_sql} ${solution_sql}"
        done
    done
}

load_solution() {
    local oracle_db=$(echo ${SETTINGS_JSON} | jq --raw-output .install_data.oracle_database)
    local oracle_user=$(whoami)
    local temp_log=/tmp/tmp.sql
    echo $(create_sql) >| ${temp_log}
    psql -U ${oracle_user} -d ${oracle_db} -h localhost -f ${temp_log}
}

clean_files() {
    local query_files=$(echo ${SETTINGS_JSON} | jq --raw-output '.test_data | .[] | .query_files | .[] | .query_file')
    for query_file in ${query_files}; do
        rm -f "${SOLUTION_DIR}/${query_file}"
    done
}

# script starts here
if [[ $# -lt 2 ]]; then
    echo "Usage: $0 settings_json files_dir"
    exit 1
fi

# vars
SETTINGS_JSON=$1
FILES_DIR=$(readlink -f $2)

ENV_DIR=$(echo ${SETTINGS_JSON} | jq --raw-output .env_loc)
VENV_DIR=${ENV_DIR}/venv
SOLUTION_DIR=${ENV_DIR}/solution
PY_VERSION=3.7
PIP_REQUIREMENTS='psycopg2-binary'

THIS_SCRIPT=$(readlink -f ${BASH_SOURCE})
THIS_DIR=$(dirname ${THIS_SCRIPT})
TESTERS_DIR=$(readlink -f ${THIS_DIR}/../../../)

# main
create_venv
move_files
load_solution
clean_files
