#!/usr/bin/env bash

install_packages() {
    echo "[AUTOTEST] Installing system packages"
    sudo apt-get install redis-server python3 python3-venv
}

run_as_serveruser() {
    local cmd=$1
    if [[ -n ${SERVERUSER} ]]; then
        cmd="sudo -u ${SERVERUSER} --set-home -- ${cmd}"
    fi
    ${cmd}
}

write_markus_profile() {
    local serverhome=$(eval echo ~${SERVERUSER2})
    local profile=${THISSCRIPTDIR}/.markus_profile
    sudo echo "source $serverhome/autotstenv/bin/activate" > $profile
    sudo echo '[[ ":$PATH:" != *"'${SERVERDIR}':"* ]] && export PATH="'${SERVERDIR}':${PATH}"' >> $profile
    sudo echo "supervisord -c ${THISSCRIPTDIR}/supervisord.conf" >> $profile
    sudo echo "source $profile &> /dev/null" >> $serverhome/.bashrc 
    sudo echo "source $profile &> /dev/null" >> $serverhome/.bash_profile
}

install_venv() {
    local serverhome=$(eval echo ~${SERVERUSER2})
    echo "[AUTOTEST] Installing python3 virtual environment in $serverhome/autotstenv"
    python3 -m venv $serverhome/autotstenv
    echo "[AUTOTEST] Installing pip packages"
    source $serverhome/autotstenv/bin/activate
    pip install redis rq requests
    pip install git+https://github.com/Supervisor/supervisor@master
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

add_user_info_to_redis() {
    local json=$(printf '{"username":"%s","working_dir":"%s"}' $1 $2)
    local userlist=$(get_config_param USER_LIST)
    redis-cli RPUSH $userlist $json > /dev/null
}

create_default_tester_dir() {
    local testerdir=${WORKINGDIR}/workspaces/${SERVERUSER2}

    echo "[AUTOTEST] No dedicated tester user, using '${SERVERUSER2}'"
    sudo mkdir -p ${testerdir}
    sudo chown ${SERVERUSER2}:${SERVERUSER2} ${testerdir}
    sudo chmod ug=rwx,o=,+t ${testerdir}
    add_user_info_to_redis ${SERVERUSER2} ${testerdir}
}

create_tester_user() {
    local testeruser=$1
    local testerdir=${WORKINGDIR}/workspaces/${testeruser}

    if id ${testeruser} &> /dev/null; then
        echo "[AUTOTEST] Reusing existing tester user '${testeruser}'"
    else
        echo "[AUTOTEST] Creating tester user '${testeruser}'"
        sudo adduser --disabled-login --no-create-home ${testeruser}
    fi
    sudo mkdir -p ${testerdir}
    sudo chown ${SERVERUSER2}:${testeruser} ${testerdir}
    sudo chmod ug=rwx,o=,+t ${testerdir}
    echo "${SERVERUSER2} ALL=(${testeruser}) NOPASSWD:ALL" | sudo EDITOR="tee -a" visudo
    add_user_info_to_redis ${testeruser} ${testerdir}
}

create_tester_users() {
    if [[ -z ${TESTERUSER} ]]; then
        create_default_tester_dir
    else
        if [[ -z ${NUMWORKERS} ]]; then
            create_tester_user ${TESTERUSER}
        else
            for i in $(seq 0 $((NUMWORKERS - 1))); do
                create_tester_user ${TESTERUSER}${i}
            done
        fi
    fi
}

create_working_dirs() {
    echo "[AUTOTEST] Creating working directories"
    sudo mkdir -p ${SPECSDIR}
    sudo mkdir -p ${VENVSDIR}
    sudo mkdir -p ${RESULTSDIR}
    sudo mkdir -p ${SCRIPTSDIR}
    sudo chmod u=rwx,go= ${RESULTSDIR}
    sudo chown ${SERVERUSER2}:${SERVERUSER2} ${SPECSDIR} ${VENVSDIR} ${RESULTSDIR} ${SCRIPTSDIR}
}

start_queues() {
    echo "[AUTOTEST] Generating generate_supervisord.conf file in ${THISSCRIPTDIR}"
    run_as_serveruser "python ${SERVERDIR}/generate_supervisord.conf.py ${THISSCRIPTDIR}/supervisord.conf" 
    echo "[AUTOTEST] Starting rq workers using supervisor"
    supervisord -c ${THISSCRIPTDIR}/supervisord.conf
}

create_markus_conf() {
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
        AUTOTEST_CLIENT_DIR = 'TODO_web_server_dir'
        AUTOTEST_RUN_QUEUE = 'TODO_web_server_queue'
        AUTOTEST_SERVER_HOST = '$(hostname).$(dnsdomainname)'
        AUTOTEST_SERVER_FILES_USERNAME = ${serverconf}
        AUTOTEST_SERVER_FILES_DIR = '${WORKINGDIR}'
        AUTOTEST_SERVER_RESULTS_DIR = '${RESULTSDIR}'
    " >| markus_conf.rb
}

suggest_next_steps() {
    if [[ -n ${SERVERUSER} ]]; then
        echo "[AUTOTEST] (You must add MarkUs web server's public key to ${SERVERUSER}'s '~/.ssh/authorized_keys')"
    fi
    echo "[AUTOTEST] (You may want to add 'source ${THISSCRIPTDIR}/.markus_profile' to ${SERVERUSER2}'s crontab with a @reboot time)"
    echo "[AUTOTEST] (You should install the individual testers you plan to use)"
}

print_usage() {
    echo "Usage: $0 config_file [-s|--server <server_user>] [-t|--tester <tester_user>] [-w|--workers <num_workers>] [-h|--help]"
}

get_config_param() {
    grep -Po "^$1\s*=\s*([\'\"])\K.*(?=\1)" ${CONFIGFILE}
}

# script starts here
SHORT=s:t:w:h
LONG=server:,tester:,workers:,help
PARSED=$(getopt -o ${SHORT} -l ${LONG} -n "$0" -- "$@")
if [[ $? -ne 0 ]]; then
    print_usage
    exit 1
fi
eval set -- "${PARSED}"

# vars
THISSCRIPT=$(readlink -f ${BASH_SOURCE})
THISSCRIPTDIR=$(dirname ${THISSCRIPT})
THISUSER=$(whoami)
NUMWORKERS=""
SERVERUSER=""
TESTERUSER=""
CONFIGFILE=""
while true; do
    case "$1" in
        -s | --server )
            SERVERUSER=$2
            shift 2
            ;;
        -t | --tester )
            if [[ $2 != ${SERVERUSER} ]]; then
                TESTERUSER=$2
            fi
            shift 2
            ;;
        -w | --workers )
            if [[ -n ${TESTERUSER} ]]; then
                NUMWORKERS=$2 # option valid only together with -t|--tester
            fi
            shift 2
            ;;
        -h | --help )
            print_usage
            exit
            ;;
        -- )
            shift
            break
            ;;
        * )
            print_usage
            exit 1
    esac
done
if [[ $# -ne 1 ]]; then
    print_usage
    exit 1
fi

CONFIGFILE=$(readlink -f $1)

if [[ -n ${SERVERUSER} ]]; then
    SERVERUSER2=${SERVERUSER}
else
    SERVERUSER2=${THISUSER}
fi

WORKINGDIR=$(get_config_param WORKING_DIR)
SERVERDIR=${THISSCRIPTDIR}/server
SPECSDIR=${WORKINGDIR}/$(get_config_param SPECS_DIR_NAME)
VENVSDIR=${WORKINGDIR}/$(get_config_param VENVS_DIR_NAME)
RESULTSDIR=${WORKINGDIR}/$(get_config_param TEST_RESULT_DIR_NAME)
SCRIPTSDIR=${WORKINGDIR}/$(get_config_param TEST_SCRIPT_DIR_NAME)

# main
install_packages
create_server_user
create_tester_users
install_venv
create_working_dirs
start_queues
create_markus_conf
write_markus_profile
suggest_next_steps
