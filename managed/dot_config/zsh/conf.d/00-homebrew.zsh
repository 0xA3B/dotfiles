# Initialize Homebrew environment and preferences early so later modules can
# rely on Homebrew-managed commands and paths.

brewbin="/opt/homebrew/bin/brew"
if [[ -f $brewbin ]]; then
  eval "$("$brewbin" shellenv zsh)"

  export HOMEBREW_NO_AUTO_UPDATE=1
  export HOMEBREW_NO_ANALYTICS=1
  export HOMEBREW_NO_ENV_HINTS=1

  gnubin="$HOMEBREW_PREFIX/opt/coreutils/libexec/gnubin"
  if [[ -d $gnubin ]]; then
    path=("$gnubin" $path)
  fi
fi
