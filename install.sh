#!/usr/bin/env bash

install_packages() {
    echo "[AUTOTEST] Installing system packages"
    sudo add-apt-repository ppa:deadsnakes/ppa
    sudo apt-get update
    sudo apt-get install python3.6 python3.6-venv redis-server
}

create_server_user() {
    if [[ -z ${SERVERUSER} ]]; then 
        echo "[AUTOTEST] No dedicated server user, using '${THISUSER}'"
        mkdir -p ${WORKSPACEDIR}
    else
        if id ${SERVERUSER} &> /dev/null; then
            echo "[AUTOTEST] Using existing server user '${SERVERUSER}'"
        else
            echo "[AUTOTEST] Creating server user '${SERVERUSER}'"
            sudo adduser --disabled-password ${SERVERUSER}
        fi
        sudo mkdir -p ${WORKSPACEDIR}
        sudo chown ${SERVERUSER}:${SERVERUSER} ${WORKSPACEDIR}
    fi
}

create_worker_dir() {
    local workeruser=$1
    local workerdir=${WORKERSSDIR}/${workeruser}

    sudo mkdir -p ${workerdir}
    sudo chown ${SERVERUSEREFFECTIVE}:${workeruser} ${workerdir}
    sudo chmod ug=rwx,o=,+t ${workerdir}
    redis-cli RPUSH ${REDISWORKERS} "{\"username\":\"${workeruser}\",\"worker_dir\":\"${workerdir}\"}" > /dev/null
}

create_user() {
    local username=$1
    local groupname=$2
    local usertype=$3
    if id ${username} &> /dev/null; then
        echo "[AUTOTEST] Reusing existing ${usertype} user '${username}'"
    else
        echo "[AUTOTEST] Creating ${usertype} user '${username}'"
        sudo adduser --disabled-login --no-create-home ${username}
    fi
    if [[ $(id -gn ${username}) != ${groupname} ]]; then
        echo "[AUTOTEST] Changing primary group for '${username}' to '${groupname}'"
        sudo usermod -g ${groupname} ${username}
    else
        echo "[AUTOTEST] Primary group of '${username}' is '${groupname}'"
    fi
    echo "${SERVERUSEREFFECTIVE} ALL=(${username}) NOPASSWD:ALL" | sudo EDITOR="tee -a" visudo
}

create_worker_user() {
    create_user $1 $1 'worker'
}

create_reaper_user() {
    if [[ -n ${REAPERPREFIX} ]]; then
        local testeruser=$1
        local reaperuser="${REAPERPREFIX}${testeruser}"
        create_user ${reaperuser} ${testeruser} 'reaper'
    fi
}

create_worker_and_reaper_users() {
    redis-cli DEL ${REDISWORKERS} > /dev/null
    if [[ -z ${WORKERUSERS} ]]; then
        echo "[AUTOTEST] No dedicated worker user, using '${SERVERUSEREFFECTIVE}'"
        create_worker_dir ${SERVERUSEREFFECTIVE}
    else
        for workeruser in ${WORKERUSERS}; do
            create_worker_user ${workeruser}
            create_reaper_user ${workeruser}
            create_worker_dir ${workeruser}
        done
    fi
}

create_workspace_dirs() {
    echo "[AUTOTEST] Creating workspace directories"
    sudo mkdir -p ${SPECSDIR}
    sudo mkdir -p ${VENVSDIR}
    sudo mkdir -p ${RESULTSDIR}
    sudo mkdir -p ${SCRIPTSDIR}
    sudo mkdir -p ${WORKERSSDIR}
    sudo chmod u=rwx,go= ${RESULTSDIR} ${SCRIPTSDIR}
    sudo chown ${SERVERUSEREFFECTIVE}:${SERVERUSEREFFECTIVE} ${SPECSDIR} ${VENVSDIR} ${RESULTSDIR} ${SCRIPTSDIR} ${WORKERSSDIR}
}

install_venv() {
    local servervenv=${SERVERDIR}/venv

    echo "[AUTOTEST] Installing server virtual environment in '${servervenv}'"
    rm -rf ${servervenv}
    python3.6 -m venv ${servervenv}
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

compile_reaper_script() {
    if [[ ! -f "${SERVERDIR}/kill_worker_procs" ]]; then
        echo "[AUTOTEST] Compiling reaper script"
        gcc "${SERVERDIR}/kill_worker_procs.c" -o "${SERVERDIR}/kill_worker_procs"
    fi
    chmod 444 "${SERVERDIR}/kill_worker_procs"
}

create_enqueuer_wrapper() {
    local enqueuer=/usr/local/bin/autotest_enqueuer

    # this heredoc requires actual tabs
    cat <<-EOF | sudo tee ${enqueuer} > /dev/null
		#!/usr/bin/env bash

		source ${SERVERDIR}/venv/bin/activate
		${SERVERDIR}/autotest_enqueuer.py "\$@"
	EOF
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

    echo "[AUTOTEST] Creating Markus web server config snippet in 'markus_config.rb'"
    echo "
        AUTOTEST_ON = true
        AUTOTEST_STUDENT_TESTS_ON = false
        AUTOTEST_STUDENT_TESTS_BUFFER_TIME = 1.hour
        AUTOTEST_CLIENT_DIR = 'TODO_markus_dir'
        AUTOTEST_SERVER_HOST = '$(hostname).$(dnsdomainname)'
        AUTOTEST_SERVER_USERNAME = ${serverconf}
        AUTOTEST_SERVER_DIR = '${WORKSPACEDIR}'
        AUTOTEST_SERVER_COMMAND = 'autotest_enqueuer'
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
WORKERUSERS=$(get_config_param WORKER_USERS)
WORKSPACEDIR=$(get_config_param WORKSPACE_DIR)
SPECSDIR=${WORKSPACEDIR}/$(get_config_param SPECS_DIR_NAME)
VENVSDIR=${WORKSPACEDIR}/$(get_config_param VENVS_DIR_NAME)
RESULTSDIR=${WORKSPACEDIR}/$(get_config_param RESULTS_DIR_NAME)
SCRIPTSDIR=${WORKSPACEDIR}/$(get_config_param SCRIPTS_DIR_NAME)
WORKERSSDIR=${WORKSPACEDIR}/$(get_config_param WORKERS_DIR_NAME)
REDISPREFIX=$(get_config_param REDIS_PREFIX)
REDISWORKERS=${REDISPREFIX}:$(get_config_param REDIS_WORKERS_LIST)
REAPERPREFIX=$(get_config_param REAPER_USER_PREFIX)

# main
install_packages
create_server_user
create_worker_and_reaper_users
create_workspace_dirs
install_venv
start_queues
compile_reaper_script
create_enqueuer_wrapper
create_markus_config
suggest_next_steps
