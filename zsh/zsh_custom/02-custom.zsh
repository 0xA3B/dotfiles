##################
# Custom Options #
##################


export GEM_HOME="$HOME/.gems"
addToPath "$GEM_HOME/bin" before

if [[ $OSTYPE =~ "linux" ]] ; then
    if [[ -f "/home/linuxbrew/.linuxbrew/bin/brew" ]] ; then
        eval $(/home/linuxbrew/.linuxbrew/bin/brew shellenv)
    fi

elif [[ $OSTYPE =~ "darwin" ]] ; then
    if [[ -f "/usr/local/bin/brew" ]] ; then
        eval $(/usr/local/bin/brew shellenv)
    fi
fi

set editing-mode vi

export HOMEBREW_NO_ANALYTICS=1

#source <(kompose completion zsh)

#export IPADDR=`ifconfig -a | grep inet | grep -v '127.0.0.1' | awk '{print $2}' | grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b"`
