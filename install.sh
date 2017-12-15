#!/usr/bin/env bash

install_packages() {
    echo "[AUTOTEST] Installing system packages"
    sudo apt-get install ruby redis-server
    sudo gem install bundler
}

create_server_user() {
    echo
    if id ${SERVERUSER} > /dev/null 2>&1; then
        echo "[AUTOTEST] Reusing existing server user '${SERVERUSER}'"
    else
        echo "[AUTOTEST] Creating server user '${SERVERUSER}'"
        sudo adduser --disabled-password ${SERVERUSER}
    fi
    sudo mkdir -p ${WORKINGDIR}
    sudo chown ${SERVERUSER}:${SERVERUSER} ${WORKINGDIR}
}

create_test_user() {
    local testuser=$1
    local queue=$2
    local testdir=${WORKINGDIR}/${testuser}

    if id ${testuser} > /dev/null 2>&1; then
        echo "[AUTOTEST] Reusing existing test user '${testuser}'"
    else
        echo "[AUTOTEST] Creating test user '${testuser}'"
        sudo adduser --disabled-login --no-create-home ${testuser}
    fi
    sudo mkdir ${testdir}
    sudo chown ${testuser}:${SERVERUSER} ${testdir}
    sudo chmod ug=rwx,o=,+t ${testdir}
    echo "${SERVERUSER} ALL=(${testuser}) NOPASSWD:ALL" | EDITOR="tee -a" sudo visudo
    CONF="${CONF}{user: '${testuser}', dir: '${testdir}', queue: '${queue}'},"
}

create_test_users() {
    if [[ -z ${NUMWORKERS} ]]; then
        create_test_user ${TESTUSER} ${QUEUE}
    else
        for i in $(seq 0 $((NUMWORKERS - 1))); do
            create_test_user ${TESTUSER}${i} ${QUEUE}${i}
        done
    fi
}

create_working_dirs() {
    echo "[AUTOTEST] Creating working directories"
    sudo mkdir -p ${SPECSDIR}
    sudo mkdir -p ${VENVSDIR}
    sudo mkdir -p ${RESULTSDIR}
    sudo chown ${SERVERUSER}:${SERVERUSER} ${SPECSDIR} ${VENVSDIR} ${RESULTSDIR}
    sudo chmod u=rwx,go= ${RESULTSDIR}
}

install_gems() {
    echo "[AUTOTEST] Installing gems"
    pushd ${SERVERDIR} > /dev/null
    bundle install --deployment
    popd > /dev/null
}

run_resque() {
    sudo -u ${SERVERUSER} -- ${SERVERDIR}/start_resque.sh ${QUEUE} ${NUMWORKERS}
}

create_markus_conf() {
    echo "[AUTOTEST] Creating Markus web server config snippet in 'markus_conf.rb'"
    echo "
        AUTOMATED_TESTING_ENGINE_ON = true
        ATE_STUDENT_TESTS_ON = false
        ATE_STUDENT_TESTS_BUFFER_TIME = 1.hour
        ATE_CLIENT_DIR = 'TODO_web_server_dir'
        ATE_FILES_QUEUE_NAME = 'TODO_web_server_queue'
        ATE_SERVER_HOST = '$(hostname).$(dnsdomainname)'
        ATE_SERVER_FILES_USERNAME = '${SERVERUSER}'
        ATE_SERVER_FILES_DIR = '${WORKINGDIR}'
        ATE_SERVER_RESULTS_DIR = '${RESULTSDIR}'
        ATE_SERVER_TESTS = [${CONF}]
    " >| markus_conf.rb
}

suggest_next_steps() {
    echo "[AUTOTEST] (You must add the Markus web server public key to ${SERVERUSER}'s '~/.ssh/authorized_keys')"
    echo "[AUTOTEST] (You may want to add '${SERVERDIR}/start_resque.sh ${QUEUE} ${NUMWORKERS}' to ${SERVERUSER}'s crontab with a @reboot time)"
    echo "[AUTOTEST] (You should install the individual testers you plan to use)"
}

# script starts here
if [[ $# -lt 3 || $# -gt 4 ]]; then
    echo "Usage: $0 server_user test_user working_dir [num_workers]"
    exit 1
fi

# vars
THISSCRIPT=$(readlink -f ${BASH_SOURCE})
THISSCRIPTDIR=$(dirname ${THISSCRIPT})
SERVERUSER=$1
TESTUSER=$2
WORKINGDIR=$(readlink -f $3)
if [[ $# -eq 4 ]]; then
    NUMWORKERS=$4
else
    NUMWORKERS=""
fi
SERVERDIR=${THISSCRIPTDIR}/server
SPECSDIR=${WORKINGDIR}/specs
VENVSDIR=${WORKINGDIR}/venvs
RESULTSDIR=${WORKINGDIR}/results
QUEUE=${TESTUSER}
CONF=""

# main
install_packages
create_server_user
create_test_users
create_working_dirs
install_gems
run_resque
create_markus_conf
suggest_next_steps
