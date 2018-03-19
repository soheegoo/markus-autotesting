#!/bin/bash

HOURS=10
SECONDS=$(expr $HOURS \* 3600)
THISHOST=$(hostname)
EMAIL="techsupport@teach.cs.toronto.edu"

# find pid of resque jobs that are hanging ( "Processing" for longer that 10 hours )
HANGING=$(ps -o pid,etimes --no-header -p $(pgrep -f "resque.+Processing") 2> /dev/null | awk -v s=$SECONDS '{ if ($2 > $s) print $1 }')

if [[ "$HANGING" ]]; then
    mail -s "hanging resque workers on $THISHOST" "$EMAIL" <<- EOM
Resque workers with the following PIDs have been running for longer than $HOURS hours on $THISHOST
$HANGING
EOM
fi
