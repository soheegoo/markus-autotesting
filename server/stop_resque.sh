#!/usr/bin/env bash

kill_workers() {
    local workers=$(pgrep -f "resque.*${QUEUE}")

    if [[ ! -z ${workers} ]]; then
        echo "[RESQUE] Killing existing Resque workers on queue '${QUEUE}'"
        kill -QUIT ${workers}
    fi
}

# script starts here
if [[ $# -lt 1 || $# -gt 2 ]]; then
    echo "Usage: $0 queue_name"
    exit 1
fi

# vars
THISSCRIPT=$(readlink -f ${BASH_SOURCE})
THISSCRIPTDIR=$(dirname ${THISSCRIPT})
QUEUE=$1

# main
kill_workers
