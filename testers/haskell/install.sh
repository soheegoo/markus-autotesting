#!/usr/bin/env bash

install_packages() {
    echo "[HASKELL] Installing system packages"
	sudo apt-get install ghc cabal-install
}

install_haskell_packages() {
	mkdir -p ${PKG_DIR}
	cabal update
	# The order that these packages are installed matters. Could cause a dependency conflict 
	# Crucially it looks like tasty-stats needs to be installed before tasty-quickcheck 
	cabal install tasty-stats --prefix=${PKG_DIR}/packages
	cabal install tasty-discover --prefix=${PKG_DIR}/packages
	cabal install tasty-quickcheck --prefix=${PKG_DIR}/packages

	# install additional haskell packages (passed as arguments to this script)
	for package in "$@"; do
		cabal install $package --prefix=${PKG_DIR}/packages
	done
	mv ${HOME}/.ghc/*/package.conf.d ${PKG_DIR}
}

if [[ " $@ " =~ " -h " || " $@ " =~ " --help " ]]; then
        echo "Usage: $0 [cabal_packages_to_install ... ]"
        exit 0
fi

THISSCRIPT=$(readlink -f ${BASH_SOURCE})
THISSCRIPTDIR=$(dirname ${THISSCRIPT})
PKG_DIR=${THISSCRIPTDIR}/server/markus_cabal

# main
install_packages
install_haskell_packages
