#!/usr/bin/env bash

if [[ $# -lt 2 || $# -gt 3 ]]; then
	echo "Usage: $0 autotest_server_dir queue_name [num_workers]"
	exit 1
fi

SERVERDIR=$(readlink -f $1)
QUEUE=$2

echo "[RESQUE] Killing existing Resque workers"
kill -QUIT `pgrep -f resque`
echo "[RESQUE] Starting new Resque workers"
pushd ${SERVERDIR} > /dev/null
if [ $# -eq 3 ]; then
	NUMWORKERS=$3
	for i in $(seq 0 $((NUMWORKERS - 1))); do
		TERM_CHILD=1 BACKGROUND=yes QUEUES=${QUEUE}${i} bundle exec rake resque:work
		echo "[RESQUE] Resque worker listening on queue '${QUEUE}${i}'"
	done
else
	TERM_CHILD=1 BACKGROUND=yes QUEUES=${QUEUE} bundle exec rake resque:work
	echo "[RESQUE] Resque worker listening on queue '${QUEUE}'"
fi
popd > /dev/null
