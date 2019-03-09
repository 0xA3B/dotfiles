##################
# Custom Options #
##################


eval $(/home/linuxbrew/.linuxbrew/bin/brew shellenv)

set editing-mode vi

export HOMEBREW_NO_ANALYTICS=1

set editing-mode vi

export IP_ADDR=`ifconfig -a | grep inet | grep -v '127.0.0.1' | awk '{print $2}' | grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b"`
