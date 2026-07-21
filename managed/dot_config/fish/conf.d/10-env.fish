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

# --move keeps ~/.local/bin ahead of Homebrew in inherited PATHs so shims there
# (e.g. the op service-account shim) shadow the real binaries.
fish_add_path --move --prepend --path "$HOME/.local/bin"

set -gx PNPM_HOME "$XDG_DATA_HOME/pnpm"
contains -- "$PNPM_HOME/bin" $PATH; or set -p PATH "$PNPM_HOME/bin"

set -gx GOPATH "$XDG_DATA_HOME/go"
set -gx GOBIN "$GOPATH/bin"
contains -- "$GOBIN" $PATH; or set -a PATH "$GOBIN"
