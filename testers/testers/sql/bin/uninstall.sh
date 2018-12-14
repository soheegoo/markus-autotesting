#!/usr/bin/env bash

reset_specs() {
    echo "[SQL-UNINSTALL] Resetting specs"
    rm -f ${SPECSDIR}/install_settings.json

}

get_test_users() {
python3 - <<EOPY
import sys, json
with open('${INSTALLSETTINGS}') as f:
	settings = json.load(f)
tests = settings['tests']
for test in tests:
	print(test['user'])
EOPY
}

drop_oracle() {
    sudo -u postgres psql <<-EOF

		DROP DATABASE IF EXISTS ${ORACLEDB};
		DROP ROLE IF EXISTS ${ORACLEUSER};
	EOF
}

drop_tests() {
    for tester in $(get_test_users); do
        sudo -u postgres psql <<-EOF
			DROP DATABASE IF EXISTS ${tester};
			DROP ROLE IF EXISTS ${tester};
		EOF
    done
}

get_install_setting() {
    cat ${INSTALLSETTINGS} | python3 -c "import sys, json; print(json.load(sys.stdin)['$1'])"
}

# script starts here
if [[ $# -ne 0 ]]; then
    echo "Usage: $0"
    exit 1
fi

# vars

THISSCRIPT=$(readlink -f ${BASH_SOURCE})
TESTERDIR=$(dirname $(dirname ${THISSCRIPT}))
SPECSDIR=${TESTERDIR}/specs
INSTALLSETTINGS=${SPECSDIR}/install_settings.json
ORACLEDB=$(get_install_setting oracle_database)
TESTUSER=$2
ORACLEUSER=${ORACLEDB}

# main
drop_oracle
drop_tests
reset_specs
echo "[SQL-UNINSTALL] The following system packages have not been uninstalled: python3 postgresql. You may uninstall them if you wish."
rm -f ${SPECSDIR}/.installed

