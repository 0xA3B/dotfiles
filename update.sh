#!/usr/bin/env zsh

cd ~/.oh-my-zsh
git pull origin master

cd $ZSH_CUSTOM/plugins/zsh-dircolors-solarized
git pull origin master

cd $ZSH_CUSTOM/themes/powerlevel9k
git pull origin master

brew update
brew upgrade

pip install -U pip setuptools wheel virtualenv rstcheck

gem update mdl puppet-lint

vim -c "PlugUpgrade" -c "PlugUpdate" -c "q\!" -c "q\!"
