#!/usr/bin/env bash

set -e

install_packages() {
    echo "[JDBC-INSTALL] Installing system packages"
    sudo apt-get install openjdk-8-jdk python3
}

install_sql_tester() {
    if [[ $# -eq 1 ]]; then
        echo "[JDBC-INSTALL] Reusing already installed SQL tester"
    else
        local oracleuser=$2
        local testuser=$3
        echo "[JDBC-INSTALL] Installing SQL tester"
        if [[ $# -eq 4 ]]; then
            local numusers=$4
            ${SQLDIR}/bin/install.sh ${oracleuser} ${testuser} ${numusers}
        else
            ${SQLDIR}/bin/install.sh ${oracleuser} ${testuser}
        fi
    fi
}

update_specs() {
    local oracledb=$(awk "/oracle_database/" ${SQLDIR}/specs/install_settings.json) # copy sql oracle_database line
    local tests=$(awk "/tests/" ${SQLDIR}/specs/install_settings.json) # copy sql tests line
    
    cp ${DEFAULTSPECS} ${SPECS}

    echo "[JDBC-INSTALL] Updating specs"
    sed -i -e "\#oracle_database#c\\${oracledb}" ${SPECS}
    
    #TODO the copy does not work with multiple test users
    sed -i -e "\#tests#c\\${tests}" ${SPECS}
    sed -i -e "s#/path/to/jdbc/jar#${JARPATH}#g" ${SPECS}
}

# script starts here
if [[ $# -lt 1 || $# -gt 4 || $# -eq 2 ]]; then
    echo "Usage: $0 jdbc_jar_path [oracle_user] [test_user] [num_users]"
    exit 1
fi

# vars
THISSCRIPT=$(readlink -f ${BASH_SOURCE})
TESTERDIR=$(dirname $(dirname ${THISSCRIPT}))
SPECSDIR=${TESTERDIR}/specs
DEFAULTSPECS=${SPECSDIR}/default_install_settings.json
SPECS=${SPECSDIR}/install_settings.json
SQLDIR=$(dirname ${TESTERDIR})/sql
JARPATH=$(readlink -f $1)

# main
install_packages
install_sql_tester $@
update_specs
touch ${SPECSDIR}/.installed
