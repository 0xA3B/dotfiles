###########
# Aliases #
###########

# GNU ls options
LS_OPTIONS='-lhF --color=auto'
alias ls="ls $LS_OPTIONS"
alias la="ls $LS_OPTIONS -a"

alias c='clear'
alias e='exit'

alias zshrc="$EDITOR ~/.zshrc"
alias vimrc="$EDITOR ~/.vimrc"

alias activate="source .venv/bin/activate"

alias python="python3"
alias pip="pip3"

alias ghci="docker run --rm -it haskell"
#alias gcc="docker run --rm -v "$PWD":/usr/src -w /usr/src gcc:latest make"

### Vulnerable Containers ###
alias bricks="docker run --rm -d -p 8081:80 --name=bricks citizenstig/owaspbricks"
alias bwapp="docker run --rm -d -p 8082:80 --name=bwapp raesene/bwapp && echo 'Go to /install.php to configure'"
alias dvwa="docker run --rm -d -p 8083:80 --name=dvwa citizenstig/dvwa"
alias gruyere="docker run -d -p 8084:8008 karthequian/gruyere"
alias juice-shop="docker run --rm -d -p 8085:3000 --name=juice bkimminich/juice-shop"
alias nowasp="docker run --rm -d -p 8086:80 -p 3306:3306 -e MYSQL_PASS="Chang3ME!" --name=mutillidae citizenstig/nowasp"
alias vulnwp="docker run --rm -d -p 8087:80 -p 3306:3306 --name=vulnwp wpscanteam/vulnerablewordpress"
alias shellshock="docker run -d -p 8088:80 hmlio/vaas-cve-2014-6271"
alias webgoat7="docker run --rm -d -p 8089:8080 --name=webgoat7 webgoat/webgoat-7.1"
alias webgoat8="docker run --rm -d -p 8090:8080 --name=webgoat8 -t webgoat/webgoat-8.0"
