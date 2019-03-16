##################
# Custom Options #
##################


if [[ -f /etc/os-release ]] ; then
    eval $(/home/linuxbrew/.linuxbrew/bin/brew shellenv)
else
    # Add brew directories to path
    addToPath /usr/local/sbin before
    addToPath /usr/local/bin before
    addToPath /usr/local/opt/tcl-tk/bin before
fi

set editing-mode vi

export HOMEBREW_NO_ANALYTICS=1

if [[ ! -f /etc/os-release ]] ; then
    export IP_ADDR=`ifconfig -a | grep inet | grep -v '127.0.0.1' | awk '{print $2}' | grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b"`
fi
