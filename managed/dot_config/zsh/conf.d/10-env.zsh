# Base shell environment shared across interactive and non-interactive zsh
# sessions.

if [[ -z ${EDITOR+x} ]]; then
  export EDITOR="vim"
  command -v nvim >/dev/null 2>&1 && export EDITOR="nvim"
fi

if [[ -z ${VISUAL+x} ]]; then
  export VISUAL="$EDITOR"
  # command -v code >/dev/null 2>&1 && export VISUAL="code --wait"
fi

export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
export XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
export XDG_STATE_HOME="${XDG_STATE_HOME:-$HOME/.local/state}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}"

# Move-to-front keeps ~/.local/bin ahead of Homebrew in inherited PATHs so
# shims there (e.g. the op service-account shim) shadow the real binaries.
if [[ -d $HOME/.local/bin ]]; then
  path=("$HOME/.local/bin" ${path:#$HOME/.local/bin})
fi

export PNPM_HOME="$XDG_DATA_HOME/pnpm"
case ":$PATH:" in
  *":$PNPM_HOME/bin:"*) ;;
  *) path=("$PNPM_HOME/bin" $path) ;;
esac

export GOPATH="$XDG_DATA_HOME/go"
export GOBIN="$GOPATH/bin"
case ":$PATH:" in
  *":$GOBIN:"*) ;;
  *) path+=("$GOBIN") ;;
esac
