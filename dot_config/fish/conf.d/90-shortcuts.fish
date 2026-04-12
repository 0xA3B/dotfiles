if status is-interactive
    abbr -ag c clear
    abbr -ag e exit
    abbr -ag gs git status
    abbr -ag gp git push

    abbr -ag fish-config "$EDITOR $HOME/.config/fish/config.fish"
    abbr -ag nvim-config "$EDITOR $HOME/.config/nvim/init.lua"
    abbr -ag tmux-config "$EDITOR $HOME/.config/tmux/tmux.conf"

    abbr -ag tl "tmux list-sessions"
    abbr -ag tn "tmux new -t"
    abbr -ag ta "tmux a -t"
    abbr -ag td "tmux kill-session -t"

    abbr -ag fr fish-reload
    abbr -ag fs fish-restart

    alias pip "python3 -m pip"
    alias virtualenv "python3 -m virtualenv"
    alias mkvenv "python3 -m virtualenv .venv"
    alias activate "source .venv/bin/activate.fish"
end
