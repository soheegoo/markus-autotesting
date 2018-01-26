#!/usr/bin/env bash

install_packages() {
    echo "[JAVA] Installing system packages"
    sudo apt-get install python3 openjdk-8-jre
}

download_uam() {
    echo "[JAVA] Downloading latest version of UAM"
    if pushd ${UAMDIR} &> /dev/null; then
        git pull
        popd > /dev/null
    else
        git clone https://github.com/ProjectAT/uam.git ${UAMDIR}
    fi
    if [[ ! -e ${UAMLINK} ]]; then
        ln -s ${UAMDIR} ${UAMLINK}
    fi
}

compile_jam() {
    local jamdir=${UAMLINK}/jam

    echo "[JAVA] Compiling JAM"
    pushd ${jamdir} > /dev/null
    ./compile_jam.sh
    popd > /dev/null
}

update_specs() {
    echo "[JAVA] Updating json specs file"
    sed -i -e "s#/path/to/uam#${UAMLINK}#g" ${TESTERDIR}/specs.json
}

# script starts here
if [ $# -ne 1 ]; then
	echo "Usage: $0 uam_dir"
	exit 1
fi

# vars
THISSCRIPT=$(readlink -f ${BASH_SOURCE})
TESTERDIR=$(dirname ${THISSCRIPT})
UAMDIR=$(readlink -f $1)
UAMLINK=${TESTERDIR}/uam-git

# main
install_packages
download_uam
compile_jam
update_specs
