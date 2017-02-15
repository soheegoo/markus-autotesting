#!/usr/bin/env bash

if [ $# -ne 1 ]; then
	echo usage: $0 uam_dir
	exit 1
fi

UAMDIR=$1
GITDIR=${UAMDIR}/uam-git

echo "[UAM] Installing system packages"
sudo apt-get install python3
echo "[UAM] Downloading latest version of UAM"
if cd ${GITDIR}; then
	git pull
	cd ..
else
	git clone https://github.com/ProjectAT/uam.git ${GITDIR}
fi
echo "PATH_TO_UAM = '""${GITDIR}""'" >| server/markus_pam_config.py
