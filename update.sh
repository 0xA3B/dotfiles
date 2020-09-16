#!/bin/bash


pushd "$ZSH"
git pull
popd

pushd "$HOME/.dotfiles"
git pull
popd

pushd "$ZSH/custom/plugins/zsh-dircolors-solarized"
git pull
popd

pushd "$ZSH/custom/themes/powerlevel10k"
git pull
popd

if [[ $OSTYPE =~ "linux" ]] ; then
    sudo apt-get update
    sudo apt-get -f install
    sudo apt-get -y dist-upgrade
    sudo apt-get -y autoremove
    sudo apt-get autoclean
fi

brew update
brew upgrade
brew cleanup

pip install -U pip setuptools wheel virtualenv flake8 dlint yamllint rstcheck

if [[ ! -z "$HTTP_PROXY" ]] ; then
    gem update --http-proxy $HTTP_PROXY mdl
else
    gem update mdl
fi

vim -c "PlugUpgrade" -c "PlugUpdate" -c "q!" -c "q!"

exit 0
