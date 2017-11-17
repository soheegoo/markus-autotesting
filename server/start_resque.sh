#!/usr/bin/env bash

run_worker() {
    local queue=$1

    TERM_CHILD=1 BACKGROUND=yes QUEUES=${queue} bundle exec rake resque:work
    echo "[RESQUE] Resque worker listening on queue '${queue}'"
}
if [[ $# -lt 1 || $# -gt 2 ]]; then
    echo "Usage: $0 queue_name [num_workers]"
    exit 1
fi

THISSCRIPT=$(readlink -f ${BASH_SOURCE})
THISSCRIPTDIR=$(dirname ${THISSCRIPT})
QUEUE=$1

echo "[RESQUE] Killing existing Resque workers"
kill -QUIT `pgrep -f resque`
echo "[RESQUE] Starting new Resque workers"
pushd ${THISSCRIPTDIR} > /dev/null
if [[ $# -eq 2 ]]; then
    NUMWORKERS=$2
    for i in $(seq 0 $((NUMWORKERS - 1))); do
        run_worker ${QUEUE}${i}
    done
else
    run_worker ${QUEUE}
fi
popd > /dev/null
