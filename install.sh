#!/bin/bash


# Install oh-my-zsh
sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# Install homebrew
if [[ $OSTYPE =~ "darwin" ]]
then
    /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
else
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/Linuxbrew/install/master/install.sh)"
fi

brew install gcc glibc python ruby git
if [[ $OSTYPE =~ "darwin" ]]
then
    brew install macvim --with-override-system-vim
else
    brew install vim
fi

pip3 install -U pip setuptools wheel virtualenv

if [[ -d "$HOME/.dotfiles" ]]
then
    pushd "$HOME/.dotfiles"
    git pull
    popd
else
    git clone https://github.com/alexebaker/dotfiles.git "$HOME/.dotfiles"
fi

if [[ -d "$ZSH_CUSTOM/plugins/zsh-dircolors-solarized" ]]
then
    pushd "$ZSH_CUSTOM/plugins/zsh-dircolors-solarized"
    git pull
    popd
else
    git clone --recursive https://github.com/joel-porquet/zsh-dircolors-solarized.git "$ZSH_CUSTOM/plugins/zsh-dircolors-solarized"
fi

if [[ -d "$ZSH_CUSTOM/themes/powerlevel9k" ]]
then
    pushd "$ZSH_CUSTOM/themes/powerlevel9k"
    git pull
    popd
else
    git clone https://github.com/bhilburn/powerlevel9k.git "$ZSH_CUSTOM/themes/powerlevel9k"
    source "$HOME/.fonts/install.sh"
fi

if [[ -d "$HOME/.fonts" ]]
then
    pushd "$HOME/.fonts"
    git pull
    popd
else
    git clone --depth=1 https://github.com/powerline/fonts.git "$HOME/.fonts"
fi

curl -fLo "$HOME/.vim/autoload/plug.vim" --create-dirs https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim

ln -snf "$HOME/.dotfiles/vim/vimrc" "$HOME/.vimrc"
ln -snf "$HOME/.dotfiles/zsh/zshrc" "$HOME/.zshrc"
ln -snf "$HOME/.dotfiles/zsh/zsh_custom" "$HOME/.zsh_custom"

brew tap oclint/formulae
brew install flake8 cppcheck oclint yamllint jsonlint
pip3 install -U pip setuptools wheel virtualenv rstcheck dlint

if [[ ! -z "$http_proxy" ]]
then
    gem install --http-proxy $http_proxy mdl
else
    gem install mdl
fi

vim -c "PlugInstall" -c "q!" -c "q!"

exit 0
