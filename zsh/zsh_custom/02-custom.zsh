##################
# Custom Options #
##################


set editing-mode vi

export IP_ADDR=`ifconfig -a | grep inet | grep -v '127.0.0.1' | awk '{print $2}' | grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b"`

