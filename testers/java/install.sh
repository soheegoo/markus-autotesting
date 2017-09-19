#!/usr/bin/env bash

if [ $# -ne 1 ]; then
	echo usage: $0 uam_dir
	exit 1
fi

THISSCRIPT=$(readlink -f ${BASH_SOURCE})
TESTERDIR=$(dirname ${THISSCRIPT})
UAMDIR=$(readlink -f $1)
UAMLINK=${TESTERDIR}/uam-git
JAMDIR=${UAMLINK}/jam

echo "[JAVA] Installing system packages"
sudo apt-get install python3 openjdk-8-jre
echo "[JAVA] Downloading latest version of UAM"
if pushd ${UAMDIR} > /dev/null; then
	git pull
	popd > /dev/null
else
	git clone https://github.com/ProjectAT/uam.git ${UAMDIR}
fi
if [[ ! -e ${UAMLINK} ]]; then
    ln -s ${UAMDIR} ${UAMLINK}
fi
echo "[JAVA] Compiling JAM"
pushd ${JAMDIR} > /dev/null
./compile_jam.sh
popd > /dev/null
echo "[JAVA] Updating json specs file"
sed -i -e "s#/path/to/uam#${UAMLINK}#g" ${TESTERDIR}/specs.json
