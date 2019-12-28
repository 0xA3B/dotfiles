#!/bin/bash


cd ~/.oh-my-zsh
git pull origin master

cd ~/.zsh_custom/plugins/zsh-dircolors-solarized
git pull origin master

cd ~/.zsh_custom/themes/powerlevel9k
git pull origin master

if [[ $OSTYPE == "linux-gnu" ]] ; then
    sudo apt-get update
    sudo apt-get -f install
    sudo apt-get -y dist-upgrade
    sudo apt-get -y autoremove
    sudo apt-get autoclean
fi

brew update
brew upgrade
brew cleanup

pip3 install -U pip setuptools wheel virtualenv rstcheck flake8 dlint

if [[ ! -z "$http_proxy" ]] ; then
    gem update --http-proxy $http_proxy mdl
else
    gem update mdl
fi

vim -c "PlugUpgrade" -c "PlugUpdate" -c "q!" -c "q!"

exit 0
