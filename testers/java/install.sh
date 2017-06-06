#!/usr/bin/env bash

if [ $# -ne 1 ]; then
	echo usage: $0 uam_dir
	exit 1
fi

UAMDIR=$1
GITDIR=${UAMDIR}/uam-git

echo "[JAVA] Installing system packages"
sudo apt-get install python3 openjdk-8-jre
echo "[JAVA] Downloading latest version of UAM"
if cd ${GITDIR}; then
	git pull
	cd ..
else
	git clone https://github.com/ProjectAT/uam.git ${GITDIR}
fi
echo "[JAVA] Updating python config file"
echo "PATH_TO_UAM = '""${GITDIR}""'" >| server/markus_jam_config.py
