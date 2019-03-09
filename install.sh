#! /bin/bash


git clone https://github.com/alexebaker/dotfiles.git ~/.dotfiles
git clone --recursive https://github.com/joel-porquet/zsh-dircolors-solarized.git $ZSH_CUSTOM/plugins/zsh-dircolors-solarized

cd ~/
rm .vimrc
ln -s ~/.dotfiles/vim/vimrc .vimrc
rm .zshrc
ln -s ~/.dotfiles/zsh/zshrc .zshrc
rm -r .zsh_custom
ln -s ~/.dotfiles/zsh/zsh_custom .zsh_custom

brew tap oclint/formulae
brew install flake8 cppcheck oclint yamllint jsonlint
gem install mdl puppet-lint
pip install rstcheck
