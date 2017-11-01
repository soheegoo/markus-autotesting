#!/usr/bin/env bash

if [[ $# -lt 1 || $# -gt 2 ]]; then
    echo "Usage: $0 queue_name [num_workers]"
    exit 1
fi

THISSCRIPT=$(readlink -f ${BASH_SOURCE})
THISSCRIPTDIR=$(dirname ${THISSCRIPT})
QUEUE=$1
NUMWORKERS=1
if [[ $# -eq 3 ]]; then
    NUMWORKERS=$2
fi

echo "[RESQUE] Killing existing Resque workers"
kill -QUIT `pgrep -f resque`
echo "[RESQUE] Starting new Resque workers"
pushd ${THISSCRIPTDIR} > /dev/null
for i in $(seq 0 $((NUMWORKERS - 1))); do
    TERM_CHILD=1 BACKGROUND=yes QUEUES=${QUEUE}${i} bundle exec rake resque:work
    echo "[RESQUE] Resque worker listening on queue '${QUEUE}${i}'"
done
popd > /dev/null
