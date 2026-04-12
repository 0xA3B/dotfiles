[[ -o interactive ]] || return

alias c="clear"
alias e="exit"
alias gs="git status"
alias gp="git push"

alias fish-config="$EDITOR $HOME/.config/fish/config.fish"
alias nvim-config="$EDITOR $HOME/.config/nvim/init.lua"
alias tmux-config="$EDITOR $HOME/.config/tmux/tmux.conf"

alias tl="tmux list-sessions"
alias tn="tmux new -t"
alias ta="tmux a -t"
alias td="tmux kill-session -t"

alias fr="zsh-reload"
alias fs="zsh-restart"
alias cc="claude"
alias ccl="cc-login"
alias cce="cc-env"

alias pip="python3 -m pip"
alias virtualenv="python3 -m virtualenv"
alias mkvenv="python3 -m virtualenv .venv"
alias activate="source .venv/bin/activate"
