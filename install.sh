#! /bin/bash


git clone git@github.com:alexebaker/dotfiles.git ~/.dotfiles


cd ~/
rm .vimrc
ln -s ~/.dotfiles/vim/vimrc .vimrc
rm .zshrc
ln -s ~/.dotfiles/zsh/zshrc .zshrc
rm -r .zsh_custom
ln -s ~/.dotfiles/zsh/zsh_custom .zsh_custom

