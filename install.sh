#!/usr/bin/env bash

install_packages() {
    echo "[AUTOTEST] Installing system packages"
    sudo apt-get install ruby redis-server bundler
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

create_default_tester_dir() {
    local testerdir=${WORKINGDIR}/${QUEUE}

    echo "[AUTOTEST] No dedicated tester user, using '${SERVERUSER2}'"
    sudo mkdir -p ${testerdir}
    sudo chown ${SERVERUSER2}:${SERVERUSER2} ${testerdir}
    sudo chmod ug=rwx,o=,+t ${testerdir}
    CONF="${CONF}{user: nil, dir: '${testerdir}', queue: '${QUEUE}'},"
}

create_tester_user() {
    local testeruser=$1
    local testerdir=${WORKINGDIR}/${testeruser}

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
    CONF="${CONF}{user: '${testeruser}', dir: '${testerdir}', queue: '${testeruser}'},"
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
    sudo chmod u=rwx,go= ${RESULTSDIR}
    sudo chown ${SERVERUSER2}:${SERVERUSER2} ${SPECSDIR} ${VENVSDIR} ${RESULTSDIR}
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
        AUTOTEST_SERVER_TESTS = [${CONF}]
    " >| markus_conf.rb
}

suggest_next_steps() {
    if [[ -n ${SERVERUSER} ]]; then
        echo "[AUTOTEST] (You must add MarkUs web server's public key to ${SERVERUSER}'s '~/.ssh/authorized_keys')"
    fi
    echo "[AUTOTEST] (You may want to add '${SERVERDIR}/start_resque.sh ${QUEUE} ${NUMWORKERS}' to ${SERVERUSER2}'s crontab with a @reboot time)"
    echo "[AUTOTEST] (You should install the individual testers you plan to use)"
}

# There are subtleties about THISUSER (X), SERVERUSER (S) and TESTERUSER (T).
# 1) S and T unspecified:
#      X is used for S and T, tester dir and queue have a default name, NUMWORKERS ignored
#      MarkUs conf: local copy of student files + student code execution as X
# 2) S specified, T unspecified:
#      S is used for S and T, tester dir and queue have a default name, NUMWORKERS ignored
#      MarkUs conf: authenticated scp copy of student files + student code execution as S
# 3) S unspecified, T specified:
#      X is used for S, T is used, tester dir and queue are named T, NUMWORKERS = n changes T to T0..Tn-1
#      MarkUs conf: local copy of student files + student code execution as sudo -u T (from X)
# 4) S and T specified and equals:
#      same as #2;
# 5) S and T specified and different:
#      S and T are used, tester dir and queue are named T, NUMWORKERS = n changes T to T0..Tn-1
#      MarkUs conf: authenticated scp copy of student files + student code execution as sudo -u T (from S)
# NOTE: X can be == S|T, but it is different than leaving S|T unspecified
print_usage() {
    echo "Usage: $0 working_dir [-s|--server <server_user>] [-t|--tester <tester_user>] [-w|--workers <num_workers>] [-h|--help]"
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
QUEUE=tester # default queue, otherwise QUEUE == TESTERUSER
while true; do
    case "$1" in
        -s | --server )
            SERVERUSER=$2
            shift 2
            ;;
        -t | --tester )
            if [[ $2 != ${SERVERUSER} ]]; then
                TESTERUSER=$2
                QUEUE=${TESTERUSER}
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
WORKINGDIR=$(readlink -f $1)
if [[ -n ${SERVERUSER} ]]; then
    SERVERUSER2=${SERVERUSER}
else
    SERVERUSER2=${THISUSER}
fi
SERVERDIR=${THISSCRIPTDIR}/server
SPECSDIR=${WORKINGDIR}/specs
VENVSDIR=${WORKINGDIR}/venvs
RESULTSDIR=${WORKINGDIR}/results
CONF=""

# main
install_packages
create_server_user
create_tester_users
create_working_dirs
install_gems
run_resque
create_markus_conf
suggest_next_steps
