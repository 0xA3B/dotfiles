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

export DOTFILES_HOME="$HOME/.dotfiles"

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

if command -v uv >/dev/null 2>&1; then
  path=("$HOME/.local/bin" $path)
fi
