#!/usr/bin/env bash

install_packages() {
    echo "[AUTOTEST] Installing system packages"
    sudo apt-get install ruby redis-server bundler
}

create_server_user() {
    if [[ -z ${SERVERUSER} ]]; then
        echo "[AUTOTEST] Not creating any server user"
        mkdir -p ${WORKINGDIR}
    else
        if id ${SERVERUSER} &> /dev/null; then
            echo "[AUTOTEST] Reusing existing server user '${SERVERUSER}'"
        else
            echo "[AUTOTEST] Creating server user '${SERVERUSER}'"
            sudo adduser --disabled-password ${SERVERUSER}
        fi
        sudo mkdir -p ${WORKINGDIR}
        sudo chown ${SERVERUSER}:${SERVERUSER} ${WORKINGDIR}
    fi
}

create_default_test_dir() {
    local testdir=${WORKINGDIR}/${QUEUE}
    local user=$(whoami)

    echo "[AUTOTEST] Not creating any test user"
    sudo mkdir ${testdir}
    sudo chown ${user}:${user} ${testdir}
    sudo chmod ug=rwx,o=,+t ${testdir}
    CONF="${CONF}{user: nil, dir: '${testdir}', queue: '${QUEUE}'},"
}

create_test_user() {
    local testuser=$1
    local queue=$2
    local testdir=${WORKINGDIR}/${testuser}

    if id ${testuser} &> /dev/null; then
        echo "[AUTOTEST] Reusing existing test user '${testuser}'"
    else
        echo "[AUTOTEST] Creating test user '${testuser}'"
        sudo adduser --disabled-login --no-create-home ${testuser}
    fi
    sudo mkdir ${testdir}
    sudo chown ${SERVERUSER}:${testuser} ${testdir}
    sudo chmod ug=rwx,o=,+t ${testdir}
    echo "${SERVERUSER} ALL=(${testuser}) NOPASSWD:ALL" | sudo EDITOR="tee -a" visudo
    CONF="${CONF}{user: '${testuser}', dir: '${testdir}', queue: '${queue}'},"
}

create_test_users() {
    if [[ -z ${TESTUSER} ]]; then
        create_default_test_dir
    else
        if [[ -z ${NUMWORKERS} ]]; then
            create_test_user ${TESTUSER} ${QUEUE}
        else
            for i in $(seq 0 $((NUMWORKERS - 1))); do
                create_test_user ${TESTUSER}${i} ${QUEUE}${i}
            done
        fi
    fi
}

create_working_dirs() {
    local user=${SERVERUSER}

    echo "[AUTOTEST] Creating working directories"
    if [[ -z ${user} ]]; then
        user=$(whoami)
    fi
    sudo mkdir ${SPECSDIR}
    sudo mkdir ${VENVSDIR}
    sudo mkdir ${RESULTSDIR}
    sudo chmod u=rwx,go= ${RESULTSDIR}
    sudo chown ${user}:${user} ${SPECSDIR} ${VENVSDIR} ${RESULTSDIR}
}

install_gems() {
    echo "[AUTOTEST] Installing gems"
    pushd ${SERVERDIR} > /dev/null
    bundle install --deployment
    popd > /dev/null
}

run_resque() {
    local cmd="${SERVERDIR}/start_resque.sh ${QUEUE} ${NUMWORKERS}"

    if [[ -n ${SERVERUSER} ]]; then
        cmd="sudo -u ${SERVERUSER} -- ${cmd}"
    fi
    ${cmd}
}

create_markus_conf() {
    local user=""

    echo "[AUTOTEST] Creating Markus web server config snippet in 'markus_conf.rb'"
    if [[ -z ${SERVERUSER} ]]; then
        user=nil
    else
        user="'${SERVERUSER}'"
    fi
    echo "
        AUTOTEST_ON = true
        AUTOTEST_STUDENT_TESTS_ON = false
        AUTOTEST_STUDENT_TESTS_BUFFER_TIME = 1.hour
        AUTOTEST_CLIENT_DIR = 'TODO_web_server_dir'
        AUTOTEST_RUN_QUEUE = 'TODO_web_server_queue'
        AUTOTEST_SERVER_HOST = '$(hostname).$(dnsdomainname)'
        AUTOTEST_SERVER_FILES_USERNAME = ${user}
        AUTOTEST_SERVER_FILES_DIR = '${WORKINGDIR}'
        AUTOTEST_SERVER_RESULTS_DIR = '${RESULTSDIR}'
        AUTOTEST_SERVER_TESTS = [${CONF}]
    " >| markus_conf.rb
}

suggest_next_steps() {
    local user=${SERVERUSER}

    if [[ -z ${user} ]]; then
        user=$(whoami)
    else
        echo "[AUTOTEST] (You must add the Markus web server public key to ${SERVERUSER}'s '~/.ssh/authorized_keys')"
    fi
    echo "[AUTOTEST] (You may want to add '${SERVERDIR}/start_resque.sh ${QUEUE} ${NUMWORKERS}' to ${user}'s crontab with a @reboot time)"
    echo "[AUTOTEST] (You should install the individual testers you plan to use)"
}

# script starts here
if [[ $# -lt 1 || $# -gt 4 ]]; then
    echo "Usage: $0 working_dir [server_user] [test_user] [num_workers]"
    exit 1
fi

# vars
THISSCRIPT=$(readlink -f ${BASH_SOURCE})
THISSCRIPTDIR=$(dirname ${THISSCRIPT})
QUEUE=tester # default queue used with no test user, otherwise QUEUE == TESTUSER
WORKINGDIR=$(readlink -f $1)
if [[ $# -eq 1 ]]; then
    SERVERUSER=""
    TESTUSER=""
    NUMWORKERS=""
elif [[ $# -eq 2 ]]; then
    SERVERUSER=$2
    TESTUSER=""
    NUMWORKERS=""
elif [[ $# -eq 3 ]]; then
    SERVERUSER=$2
    TESTUSER=$3
    NUMWORKERS=""
    QUEUE=${TESTUSER}
else
    SERVERUSER=$2
    TESTUSER=$3
    NUMWORKERS=$4
    QUEUE=${TESTUSER}
fi
SERVERDIR=${THISSCRIPTDIR}/server
SPECSDIR=${WORKINGDIR}/specs
VENVSDIR=${WORKINGDIR}/venvs
RESULTSDIR=${WORKINGDIR}/results
CONF=""

#TODO handle default test user with server user
#TODO allow test user but not server user
# main
install_packages
create_server_user
create_test_users
create_working_dirs
install_gems
run_resque
create_markus_conf
suggest_next_steps
