#!/usr/bin/env bash

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

if [[ $# -lt 3 || $# -gt 4 ]]; then
    echo "Usage: $0 server_user test_user working_dir [num_workers]"
    exit 1
fi

THISSCRIPT=$(readlink -f ${BASH_SOURCE})
THISSCRIPTDIR=$(dirname ${THISSCRIPT})
SERVERUSER=$1
TESTUSER=$2
WORKINGDIR=$(readlink -f $3)
SERVERDIR=${THISSCRIPTDIR}/server
SPECSDIR=${WORKINGDIR}/specs
VENVSDIR=${WORKINGDIR}/venvs
RESULTSDIR=${WORKINGDIR}/results
QUEUE=${TESTUSER}

echo "[AUTOTEST] Installing system packages"
sudo apt-get install ruby redis-server
sudo gem install bundler
if id ${SERVERUSER} > /dev/null 2>&1; then
    echo "[AUTOTEST] Reusing existing server user '${SERVERUSER}'"
else
    echo "[AUTOTEST] Creating server user '${SERVERUSER}'"
    sudo adduser --disabled-password ${SERVERUSER}
fi
sudo mkdir -p ${WORKINGDIR}
sudo chown ${SERVERUSER}:${SERVERUSER} ${WORKINGDIR}
CONF=""
if [[ $# -eq 4 ]]; then
    NUMWORKERS=$4
    for i in $(seq 0 $((NUMWORKERS - 1))); do
        create_test_user ${TESTUSER}${i} ${QUEUE}${i}
    done
else
    NUMWORKERS=""
    create_test_user ${TESTUSER} ${QUEUE}
fi
echo "[AUTOTEST] Creating working directories"
sudo mkdir ${SPECSDIR}
sudo mkdir ${VENVSDIR}
sudo mkdir ${RESULTSDIR}
sudo chown ${SERVERUSER}:${SERVERUSER} ${SPECSDIR} ${VENVSDIR} ${RESULTSDIR}
sudo chmod u=rwx,go= ${RESULTSDIR}
echo "[AUTOTEST] Installing gems"
pushd ${SERVERDIR} > /dev/null
bundle install --deployment
sudo -u ${SERVERUSER} -- ./start_resque.sh ${QUEUE} ${NUMWORKERS}
popd > /dev/null
echo "[AUTOTEST] Creating Markus web server config snippet in 'markus_conf.rb'"
echo "
    AUTOMATED_TESTING_ENGINE_ON = true
    ATE_EXPERIMENTAL_STUDENT_TESTS_ON = false
    ATE_EXPERIMENTAL_STUDENT_TESTS_BUFFER_TIME = 2.hours
    ATE_CLIENT_DIR = 'TODO_web_server_dir'
    ATE_FILES_QUEUE_NAME = 'TODO_web_server_queue'
    ATE_SERVER_HOST = '$(hostname).$(dnsdomainname)'
    ATE_SERVER_FILES_USERNAME = '${SERVERUSER}'
    ATE_SERVER_FILES_DIR = '${WORKINGDIR}'
    ATE_SERVER_RESULTS_DIR = '${RESULTSDIR}'
    ATE_SERVER_TESTS = [${CONF}]
" >| markus_conf.rb
echo "[AUTOTEST] (You must add the Markus web server public key to ${SERVERUSER}'s '~/.ssh/authorized_keys')"
echo "[AUTOTEST] (You may want to add '${SERVERDIR}/start_resque.sh ${QUEUE} ${NUMWORKERS}' to ${SERVERUSER}'s crontab with a @reboot time)"
echo "[AUTOTEST] (You should install the individual testers you plan to use)"
