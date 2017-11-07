#!/usr/bin/env bash

# Deploys the autotesting server (run this as a super user, e.g. sudo install.sh)

if [[ $# -lt 3 || $# -gt 4 ]]; then
    echo "Usage: $0 server_user test_user working_dir [num_workers]"
    exit 1
fi

THISSCRIPT=$(readlink -f ${BASH_SOURCE})
THISSCRIPTDIR=$(dirname ${THISSCRIPT})
SERVERUSER=$1
TESTUSER=$2
WORKINGDIR=$(readlink -f $3)
NUMWORKERS=1
if [[ $# -eq 4 ]]; then
    NUMWORKERS=$4
fi
SERVERDIR=${THISSCRIPTDIR}/server
SPECSDIR=${WORKINGDIR}/specs
VENVSDIR=${WORKINGDIR}/venvs
RESULTSDIR=${WORKINGDIR}/results
QUEUE=${TESTUSER}

echo "[AUTOTEST] Installing system packages"
apt-get install ruby bundler redis-server
echo "[AUTOTEST] Creating server user '${SERVERUSER}'"
adduser --disabled-password ${SERVERUSER}
conf=""
for i in $(seq 0 $((NUMWORKERS - 1))); do
    testdir=${WORKINGDIR}/${TESTUSER}${i}
    echo "[AUTOTEST] Creating test user '${TESTUSER}${i}'"
    adduser --disabled-login --no-create-home ${TESTUSER}${i}
    mkdir -p ${testdir}
    chmod ug=rwx,o=,+t ${testdir}
    chown ${TESTUSER}${i}:${SERVERUSER} ${testdir}
    echo "${SERVERUSER} ALL=(${TESTUSER}${i}) NOPASSWD:ALL" | EDITOR="tee -a" visudo
    conf="${conf}{user: '${TESTUSER}${i}', dir: '${testdir}', queue: '${QUEUE}${i}'},"
done
echo "[AUTOTEST] Creating working directories"
mkdir -p ${SPECSDIR}
mkdir -p ${VENVSDIR}
mkdir -p ${RESULTSDIR}
chmod u=rwx,go= ${RESULTSDIR}
chown ${SERVERUSER}:${SERVERUSER} ${SPECSDIR} ${VENVSDIR} ${RESULTSDIR}
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
    ATE_SERVER_TESTS = [${conf}]
" >| markus_conf.rb
echo "[AUTOTEST] (You must add the Markus web server user's public key to '$(~${SERVERUSER})/.ssh/authorized_keys')"
echo "[AUTOTEST] (You may want to add '${SERVERDIR}/start_rescue.sh ${QUEUE} ${NUMWORKERS}' to ${SERVERUSER}'s crontab with a @reboot time)"
echo "[AUTOTEST] (You should install the individual testers you plan to use)"
