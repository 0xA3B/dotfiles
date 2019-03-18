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
