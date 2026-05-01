# Base shell environment shared across interactive and non-interactive fish
# sessions.

set -g DOTFILES_HOME "$HOME/.dotfiles"

if not set -q EDITOR
    set -gx EDITOR vim
    command -q nvim; and set -gx EDITOR nvim
end

if not set -q VISUAL
    set -gx VISUAL $EDITOR
    # command -q code; and set -gx VISUAL code --wait
end

if command -q go
    set -l gobin (go env GOBIN)
    if test -n "$gobin"; and test -d "$gobin"
        fish_add_path --append "$gobin"
    end
end

if command -q uv
    fish_add_path --prepend "$HOME/.local/bin"
end

switch (uname)
    case Darwin
        set -gx PYTHON_CONFIGURE_OPTS "--enable-framework --enable-optimizations --with-lto"
        set -gx PYTHON_CFLAGS "-march=native -mtune=native"
    case '*'
        set -gx PYTHON_CONFIGURE_OPTS "--enable-shared"
end
