#!/usr/bin/env bash

install_packages() {
    echo "[HASKELL] Installing system packages"
    sudo apt-get install ghc cabal-install
}

install_haskell_packages() {
    cabal update
    # The order that these packages are installed matters. Could cause a dependency conflict 
    # Crucially it looks like tasty-stats needs to be installed before tasty-quickcheck 
    sudo cabal install tasty-stats --global
    sudo cabal install tasty-discover --global
    sudo cabal install tasty-quickcheck --global

    # install additional haskell packages (passed as arguments to this script)
    for package in "$@"; do
        sudo cabal install $package --global
    done
}

if [[ " $@ " =~ " -h " || " $@ " =~ " --help " ]]; then
        echo "Usage: $0 [cabal_packages_to_install ... ]"
        exit 0
fi

# main
install_packages
install_haskell_packages
