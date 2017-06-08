#!/usr/bin/env bash

if [ $# -ne 1 ]; then
	echo usage: $0 uam_dir
	exit 1
fi

UAMDIR=$1

echo "[PYTHON] Installing system packages"
sudo apt-get install python3
echo "[PYTHON] Downloading latest version of UAM"
if cd ${UAMDIR}; then
	git pull
	cd ..
else
	git clone https://github.com/ProjectAT/uam.git ${UAMDIR}
fi
echo "[PYTHON] Updating python config file"
echo "PATH_TO_UAM = '""${UAMDIR}""'" >| server/markus_pam_config.py
