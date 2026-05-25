# Base shell environment shared across interactive and non-interactive fish
# sessions.

if not set -q EDITOR
    set -gx EDITOR vim
    command -q nvim; and set -gx EDITOR nvim
end

if not set -q VISUAL
    set -gx VISUAL $EDITOR
    # command -q code; and set -gx VISUAL code --wait
end

set -q XDG_CONFIG_HOME; or set -gx XDG_CONFIG_HOME "$HOME/.config"
set -q XDG_DATA_HOME; or set -gx XDG_DATA_HOME "$HOME/.local/share"
set -q XDG_STATE_HOME; or set -gx XDG_STATE_HOME "$HOME/.local/state"
set -q XDG_CACHE_HOME; or set -gx XDG_CACHE_HOME "$HOME/.cache"

fish_add_path --prepend --path "$HOME/.local/bin"

set -gx PNPM_HOME "$XDG_DATA_HOME/pnpm"
mkdir -p "$PNPM_HOME/bin"
fish_add_path --prepend --path "$PNPM_HOME/bin"

if command -q go
    set -l gobin (go env GOBIN)
    test -n "$gobin"; and fish_add_path --append --path "$gobin"
end

switch (uname)
    case Darwin
        set -gx PYTHON_CONFIGURE_OPTS "--enable-framework --enable-optimizations --with-lto"
        set -gx PYTHON_CFLAGS "-march=native -mtune=native"
    case '*'
        set -gx PYTHON_CONFIGURE_OPTS --enable-shared
end
