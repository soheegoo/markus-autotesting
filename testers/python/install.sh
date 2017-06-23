#!/usr/bin/env bash

if [ $# -ne 2 ]; then
	echo usage: $0 python_dir uam_dir
	exit 1
fi

PYDIR=$1
UAMDIR=$2
SPECS=${PYDIR}/specs.json

echo "[PYTHON] Installing system packages"
sudo apt-get install python3
echo "[PYTHON] Downloading latest version of UAM"
if cd ${UAMDIR}; then
	git pull
else
	git clone https://github.com/ProjectAT/uam.git ${UAMDIR}
fi
echo '[JAVA] Updating json specs file'
# TODO copy default specs file to another location, the sed (maybe separate install.sh into additional env_setup.sh)
sed -i -e "s#/path/to/uam#${UAMDIR}#g" ${SPECS}
