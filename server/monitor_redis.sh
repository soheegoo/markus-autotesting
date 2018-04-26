#!/bin/bash

HOURS=3
HOURSINSECONDS=$(expr $HOURS \* 3600)
THISHOST=$(hostname)
EMAIL="techsupport@teach.cs.toronto.edu"
AUTOTSTDIR="/data"
THISSCRIPT=$(readlink -f ${BASH_SOURCE})
THISSCRIPTDIR=$(dirname ${THISSCRIPT})
NUMWORKERS=8


# find pid of resque jobs that are hanging ( "Processing" for longer that 10 hours )
HANGING=$(ps -o pid,etimes --no-header -p $(pgrep -f "resque.+Processing") 2> /dev/null | awk -v s=$HOURSINSECONDS '{ if ($2 > s) print $1 }')

if [[ "$HANGING" ]]; then
	# make temporary dir to store info about current state until it can be reviewed
	TMPDIR=$(mktemp -d "$AUTOTSTDIR/autotst/redis_recovery.XXXXXXXXX")
	redis-cli info > "$TMPDIR/redis_info.txt" # get redis info
	ps aux | grep resque > "$TMPDIR/resque_workers.txt" # get which worker is stalled
	CONTENTDIR="$TMPDIR/autotst_content/" 
	mkdir $CONTENTDIR
	cp -r "$AUTOTSTDIR/"autotst[0-7] $CONTENTDIR # get contents of all autotest[0-7] directories

	# kill all workers and restart them so we can clear backed up jobs
	kill -QUIT `pgrep -f resque` # kill workers who aren't stuck nicely
	sleep 10 # wait for these workers to finish up
	kill -KILL `pgrep -f resque` # kill stuck workers not nicely
	sleep 10 # just in case

	# restart workers
	"$THISSCRIPTDIR/"start_resque.sh autotst $NUMWORKERS

	# send warning email
    mail -s "hanging resque workers on $THISHOST" "$EMAIL" <<- EOM
Resque workers with the following PIDs have been running for longer than $HOURS hours on $THISHOST
$HANGING
Info about the current state of all workers can be found on $THISHOST in $TMPDIR
EOM
fi


