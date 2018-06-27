#!/usr/bin/env bash

install_packages() {
    echo "[HASKELL] Installing system packages"
	sudo apt-get install ghc cabal-install
}

install_haskell_packages() {
	# TODO: don't install globally, install in venv instead
	# 		and get venv to add to and export GHC_PACKAGE_PATH
	cabal update
	sudo cabal install --global tasty-quickcheck
	sudo cabal install --global tasty-discover
	sudo cabal install --global tasty-stats
}

# script starts here
if [ $# -ne 0 ]; then
	echo "Usage: $0"
	exit 1
fi

# main
install_packages
install_haskell_packages
