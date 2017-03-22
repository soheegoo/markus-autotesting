#!/usr/bin/env bash

if [ $# -ne 1 ]; then
	echo usage: $0 xquery_dir
	exit 1
fi

XQDIR=$1

echo "[XQUERY] Installing system packages"
sudo apt-get install python3 galax libxml2-utils
# TODO Should write settings to the config file
#echo "[XQUERY] Updating python config file"
