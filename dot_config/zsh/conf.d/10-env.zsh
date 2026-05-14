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

if [[ -d $HOME/.local/bin ]]; then
  case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *) path=("$HOME/.local/bin" $path) ;;
  esac
fi

export PNPM_HOME="$XDG_DATA_HOME/pnpm"
if [[ -d $PNPM_HOME ]]; then
  case ":$PATH:" in
    *":$PNPM_HOME:"*) ;;
    *) path=("$PNPM_HOME" $path) ;;
  esac
fi

if command -v go >/dev/null 2>&1; then
  gobin="$(go env GOBIN)"
  if [[ -n $gobin && -d $gobin ]]; then
    path+=("$gobin")
  fi
fi

case "$(uname)" in
  Darwin)
    export PYTHON_CONFIGURE_OPTS="--enable-framework --enable-optimizations --with-lto"
    export PYTHON_CFLAGS="-march=native -mtune=native"
    ;;
  *)
    export PYTHON_CONFIGURE_OPTS="--enable-shared"
    ;;
esac
