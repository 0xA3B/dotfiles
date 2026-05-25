if status is-interactive; and command -q bat
    set -gx BAT_THEME "Catppuccin Mocha"
    set -gx MANPAGER "sh -c 'col -bx | bat -l man -p'"
    alias cat "bat --paging=never"
end
