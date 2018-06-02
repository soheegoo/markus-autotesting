#!/usr/bin/env bash

install_packages() {
    echo "[AUTOTEST] Installing system packages"
    sudo apt-get install redis-server python3 python3-venv
}

create_server_user() {
    if [[ -z ${SERVERUSER} ]]; then
        echo "[AUTOTEST] No dedicated server user, using '${THISUSER}'"
        mkdir -p ${WORKINGDIR}
    else
        if id ${SERVERUSER} &> /dev/null; then
            echo "[AUTOTEST] Using existing server user '${SERVERUSER}'"
        else
            echo "[AUTOTEST] Creating server user '${SERVERUSER}'"
            sudo adduser --disabled-password ${SERVERUSER}
        fi
        sudo mkdir -p ${WORKINGDIR}
        sudo chown ${SERVERUSER}:${SERVERUSER} ${WORKINGDIR}
    fi
}

create_tester_dir() {
    local testeruser=$1
    local testerdir=${WORKSPACESDIR}/${testeruser}

    sudo mkdir -p ${testerdir}
    sudo chown ${SERVERUSEREFFECTIVE}:${testeruser} ${testerdir}
    sudo chmod ug=rwx,o=,+t ${testerdir}
    redis-cli RPUSH ${REDISTESTERS} "{\"username\":\"${testeruser}\",\"workspace_dir\":\"${testerdir}\"}" > /dev/null
}

create_tester_user() {
    local testeruser=$1

    if id ${testeruser} &> /dev/null; then
        echo "[AUTOTEST] Reusing existing tester user '${testeruser}'"
    else
        echo "[AUTOTEST] Creating tester user '${testeruser}'"
        sudo adduser --disabled-login --no-create-home ${testeruser}
    fi
    create_tester_dir ${testeruser}
    echo "${SERVERUSEREFFECTIVE} ALL=(${testeruser}) NOPASSWD:ALL" | sudo EDITOR="tee -a" visudo
}

create_tester_users() {
    if [[ -z ${TESTERUSERS} ]]; then
        echo "[AUTOTEST] No dedicated tester user, using '${SERVERUSEREFFECTIVE}'"
        create_tester_dir ${SERVERUSEREFFECTIVE}
    else
        for testeruser in ${TESTERUSERS}; do
            create_tester_user ${testeruser}
        done
    fi
}

create_working_dirs() {
    echo "[AUTOTEST] Creating working directories"
    sudo mkdir -p ${SPECSDIR}
    sudo mkdir -p ${VENVSDIR}
    sudo mkdir -p ${RESULTSDIR}
    sudo mkdir -p ${SCRIPTSDIR}
    sudo mkdir -p ${WORKSPACESDIR}
    sudo chmod u=rwx,go= ${RESULTSDIR} ${SCRIPTSDIR}
    sudo chown ${SERVERUSEREFFECTIVE}:${SERVERUSEREFFECTIVE} ${SPECSDIR} ${VENVSDIR} ${RESULTSDIR} ${SCRIPTSDIR} ${WORKSPACESDIR}
}

install_venv() {
    local servervenv=${SERVERDIR}/venv

    echo "[AUTOTEST] Installing server virtual environment in '${servervenv}'"
    rm -rf ${servervenv}
    python3 -m venv ${servervenv}
    echo "[AUTOTEST] Installing pip packages"
    source ${servervenv}/bin/activate
    pip install -r ${SERVERDIR}/requirements.txt
}

start_queues() {
    local supervisorconf=${SERVERDIR}/supervisord.conf
    local supervisorcmd="supervisord -c ${supervisorconf}"
    if [[ -n ${SERVERUSER} ]]; then
        supervisorcmd="sudo -u ${SERVERUSER} --set-home -- ${supervisorcmd}"
    fi

    echo "[AUTOTEST] Generating supervisor config file in '${supervisorconf}'"
    ${SERVERDIR}/generate_supervisord_conf.py ${supervisorconf}
    echo "[AUTOTEST] Starting rq workers using supervisor"
    pushd ${SERVERDIR} > /dev/null
    ${supervisorcmd}
    popd > /dev/null
    deactivate
}

create_enqueuer_wrapper() {
    local enqueuer=/usr/local/bin/autotest_enqueuer.py

    echo "
        source ${SERVERDIR}/venv/bin/activate
        ${SERVERDIR}/autotest_enqueuer.py \"\$@\"
    " | sudo tee ${enqueuer} > /dev/null
    sudo chown ${SERVERUSEREFFECTIVE}:${SERVERUSEREFFECTIVE} ${enqueuer}
    sudo chmod u+x ${enqueuer}
}

create_markus_config() {
    local serverconf=""
    if [[ -n ${SERVERUSER} ]]; then
        serverconf="'${SERVERUSER}'"
    else
        serverconf="nil"
    fi

    echo "[AUTOTEST] Creating Markus web server config snippet in 'markus_conf.rb'"
    echo "
        AUTOTEST_ON = true
        AUTOTEST_STUDENT_TESTS_ON = false
        AUTOTEST_STUDENT_TESTS_BUFFER_TIME = 1.hour
        AUTOTEST_CLIENT_DIR = 'TODO_markus_dir'
        AUTOTEST_SERVER_HOST = '$(hostname).$(dnsdomainname)'
        AUTOTEST_SERVER_USERNAME = ${serverconf}
        AUTOTEST_SERVER_DIR = '${WORKINGDIR}'
        AUTOTEST_SERVER_COMMAND = 'autotest_enqueuer.py'
        AUTOTEST_RUN_QUEUE = 'TODO_markus_run_queue'
        AUTOTEST_CANCEL_QUEUE = 'TODO_markus_cancel_queue'
        AUTOTEST_SCRIPTS_QUEUE = 'TODO_markus_scripts_queue'
    " >| markus_config.rb
}

suggest_next_steps() {
    if [[ -n ${SERVERUSER} ]]; then
        echo "[AUTOTEST] (You must add MarkUs web server's public key to ${SERVERUSER}'s '~/.ssh/authorized_keys')"
    fi
    echo "[AUTOTEST] (You may want to add 'source ${SERVERDIR}/venv/bin/activate && supervisord -c ${SERVERDIR}/supervisord.conf' to ${SERVERUSEREFFECTIVE}'s crontab with a @reboot time)"
    echo "[AUTOTEST] (You should install the individual testers you plan to use)"
}

get_config_param() {
    grep -Po "^$1\s*=\s*([\'\"])\K.*(?=\1)" ${CONFIGFILE}
}

# script starts here
if [ $# -gt 0 ]; then
	echo "Usage: $0"
	exit 1
fi

# vars
THISSCRIPT=$(readlink -f ${BASH_SOURCE})
THISSCRIPTDIR=$(dirname ${THISSCRIPT})
SERVERDIR=${THISSCRIPTDIR}/server
CONFIGFILE=${THISSCRIPTDIR}/server/config.py
THISUSER=$(whoami)
SERVERUSER=$(get_config_param SERVER_USER)
if [[ -n ${SERVERUSER} ]]; then
    SERVERUSEREFFECTIVE=${SERVERUSER}
else
    SERVERUSEREFFECTIVE=${THISUSER}
fi
TESTERUSERS=$(get_config_param TESTER_USERS)
WORKINGDIR=$(get_config_param WORKING_DIR)
SPECSDIR=${WORKINGDIR}/$(get_config_param SPECS_DIR_NAME)
VENVSDIR=${WORKINGDIR}/$(get_config_param VENVS_DIR_NAME)
RESULTSDIR=${WORKINGDIR}/$(get_config_param TEST_RESULTS_DIR_NAME)
SCRIPTSDIR=${WORKINGDIR}/$(get_config_param TEST_SCRIPTS_DIR_NAME)
WORKSPACESDIR=${WORKINGDIR}/$(get_config_param WORKSPACES_DIR_NAME)
REDISTESTERS=$(get_config_param REDIS_TESTERS_LIST)

# main
install_packages
create_server_user
create_tester_users
create_working_dirs
install_venv
start_queues
create_enqueuer_wrapper
create_markus_config
suggest_next_steps
