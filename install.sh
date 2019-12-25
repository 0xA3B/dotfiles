#!/usr/bin/env bash


git clone https://github.com/alexebaker/dotfiles.git $HOME/.dotfiles
git clone --recursive https://github.com/joel-porquet/zsh-dircolors-solarized.git $ZSH_CUSTOM/plugins/zsh-dircolors-solarized
git clone https://github.com/bhilburn/powerlevel9k.git $ZSH_CUSTOM/themes/powerlevel9k
git clone --depth=1 https://github.com/powerline/fonts.git $HOME/.fonts

cd ~/
rm .vimrc
ln -s ~/.dotfiles/vim/vimrc .vimrc
rm .zshrc
ln -s ~/.dotfiles/zsh/zshrc .zshrc
rm -r .zsh_custom
ln -s ~/.dotfiles/zsh/zsh_custom .zsh_custom

brew tap oclint/formulae
brew install flake8 cppcheck oclint yamllint jsonlint
pip install rstcheck

if [[ ! -z "$http_proxy" ]] ; then
    sudo gem install --http-proxy $http_proxy mdl puppet-lint
else
    sudo gem install mdl puppet-lint
fi

cd ~/.fonts
./install.sh
cd ~/

exit 0
