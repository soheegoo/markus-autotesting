#!/usr/bin/env bash

if [ $# -ne 0 ]; then
	echo usage: $0
	exit 1
fi

echo "[SQL] Installing system packages"
sudo apt-get install python3 postgresql jq
