#!/usr/bin/env zsh


pushd "$ZSH"
git pull
popd

pushd "$HOME/.dotfiles"
git pull
popd

pushd "$ZSH/custom/plugins/zsh-dircolors-solarized"
git pull --force --recurse-submodules
ln -snf zsh-dircolors-solarized.zsh zsh-dircolors-solarized.plugin.zsh
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

python3 -m pip install -U pip setuptools wheel virtualenv neovim flake8 dlint yamllint rstcheck
python2 -m pip install -U pip setuptools wheel virtualenv neovim

~/.pyenv/versions/neovim2/bin/python -m pip install -U pip setuptools wheel virtualenv neovim

if [[ ! -z "$HTTP_PROXY" ]] ; then
    gem update --http-proxy $HTTP_PROXY mdl neovim
else
    gem update mdl neovim
fi

npm install -g npm neovim

nvim -c "PlugUpgrade" -c "PlugUpdate" -c "q!" -c "q!"

exit 0
