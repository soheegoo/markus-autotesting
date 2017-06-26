#!/usr/bin/env bash

if [ $# -ne 2 ]; then
	echo usage: $0 java_tester_dir uam_dir
	exit 1
fi

TESTERDIR=$(readlink -f $1)
UAMDIR=$(readlink -f $2)
UAMLINK=${TESTERDIR}/uam-git
JAMDIR=${UAMLINK}/jam

echo "[JAVA] Installing system packages"
sudo apt-get install python3 openjdk-8-jre
echo "[JAVA] Downloading latest version of UAM"
if pushd ${UAMDIR}; then
	git pull
	popd
else
	git clone https://github.com/ProjectAT/uam.git ${UAMDIR}
fi
if [[ ! -e ${UAMLINK} ]]; then
    ln -s ${UAMDIR} ${UAMLINK}
fi
echo "[JAVA] Compiling JAM"
pushd ${JAMDIR}
./compile_jam.sh
popd
echo '[JAVA] Updating json specs file'
sed -i -e "s#/path/to/uam#${UAMLINK}#g" ${TESTERDIR}/specs.json
