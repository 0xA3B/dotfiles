###########
# Aliases #
###########

# GNU ls options
LS_OPTIONS='-lhF --color=auto'
alias ls="gls $LS_OPTIONS"
alias la="gls $LS_OPTIONS -a"

alias c='clear'
alias e='exit'

alias zshrc="$EDITOR ~/.zshrc"
alias vimrc="$EDITOR ~/.vimrc"

alias activate="source .venv/bin/activate"

alias python="python3"
alias pip="pip3"
