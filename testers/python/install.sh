#!/usr/bin/env bash

install_packages() {
    echo "[PYTHON] Installing system packages"
    sudo apt-get install python3
}

# script starts here
if [ $# -ne 1 ]; then
	echo "Usage: $0 uam_dir"
	exit 1
fi

# vars

# main
install_packages
