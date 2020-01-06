#!/bin/bash


pushd "$ZSH"
git pull
popd

pushd "$HOME/.dotfiles"
git pull
popd

pushd "$ZSH_CUSTOM/plugins/zsh-dircolors-solarized"
git pull
popd

pushd "$ZSH_CUSTOM/themes/powerlevel9k"
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

pip3 install -U pip setuptools wheel virtualenv rstcheck dlint

if [[ ! -z "$HTTP_PROXY" ]] ; then
    gem update --http-proxy $HTTP_PROXY mdl
else
    gem update mdl
fi

vim -c "PlugUpgrade" -c "PlugUpdate" -c "q!" -c "q!"

exit 0
