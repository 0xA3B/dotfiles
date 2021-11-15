#!/usr/bin/env zsh


pushd "$ZSH"
git pull
popd

pushd "$HOME/.dotfiles"
git pull
popd

pushd "$ZSH/custom/plugins/zsh-dircolors-solarized"
git pull --force --recurse-submodules
#ln -snf zsh-dircolors-solarized.zsh zsh-dircolors-solarized.plugin.zsh
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
elif [[ $OSTYPE =~ "darwin" ]] ; then
    brew update
    brew upgrade
    brew cleanup
fi

python3 -m pip install --upgrade-strategy eager -U -r $HOME/.dotfiles/python/requirements.txt
python2 -m pip install --upgrade-strategy eager -U -r $HOME/.dotfiles/python/requirements.txt

if [[ ! -z "$HTTP_PROXY" ]] ; then
    gem update --http-proxy $HTTP_PROXY mdl neovim
else
    gem update mdl neovim
fi

#npm install -g npm neovim


vim -c "PlugUpgrade" -c "PlugUpdate" -c "q!" -c "q!"
nvim -c "PlugUpgrade" -c "PlugUpdate" -c "q!" -c "q!"

exit 0
