#!/usr/bin/env bash

if [ $# -ne 2 ]; then
	echo usage: $0 python_tester_dir uam_dir
	exit 1
fi

TESTERDIR=$(readlink -f $1)
UAMDIR=$(readlink -f $2)
UAMLINK=${TESTERDIR}/uam-git

echo "[PYTHON] Installing system packages"
sudo apt-get install python3
echo "[PYTHON] Downloading latest version of UAM"
if pushd ${UAMDIR}; then
	git pull
	popd
else
	git clone https://github.com/ProjectAT/uam.git ${UAMDIR}
fi
if [[ ! -e ${UAMLINK} ]]; then
    ln -s ${UAMDIR} ${UAMLINK}
fi
echo '[PYTHON] Updating json specs file'
sed -i -e "s#/path/to/uam#${UAMLINK}#g" ${TESTERDIR}/specs.json
