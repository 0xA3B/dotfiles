if status is-interactive; and command -q fzf
    set -l fzf_opts "--height=40% --layout=reverse --border"

    if command -q bat; and command -q eza
        set -a fzf_opts "--preview='test -d {} && eza -la --color=always --icons=auto {} || bat --color=always --style=numbers --line-range=:500 {}'"
    end

    if command -q fd
        set -gx FZF_DEFAULT_COMMAND "fd --type f --hidden --follow --exclude .git"
    end

    set -gx FZF_DEFAULT_OPTS $fzf_opts
    fzf --fish | source
end
