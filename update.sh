#!/usr/bin/env bash


cd ~/.oh-my-zsh
git pull origin master

cd ~/.zsh_custom/plugins/zsh-dircolors-solarized
git pull origin master

cd ~/.zsh_custom/themes/powerlevel9k
git pull origin master

if [[ -f /etc/os-release ]] ; then
    sudo apt-get update
    sudo apt-get -f install
    sudo apt-get -y dist-upgrade
    sudo apt-get -y autoremove
    sudo apt-get autoclean
fi

brew update
brew upgrade
brew cleanup

pip install -U pip setuptools wheel virtualenv rstcheck

if [[ ! -z "$http_proxy" ]] ; then
    sudo gem update --http-proxy $http_proxy mdl puppet-lint
else
    sudo gem update mdl puppet-lint
fi

vim -c "PlugUpgrade" -c "PlugUpdate" -c "q!" -c "q!"

exit 0
