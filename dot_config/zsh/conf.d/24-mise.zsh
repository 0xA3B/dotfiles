if [[ -o interactive ]] && command -v mise >/dev/null 2>&1 && (( ! $+functions[_mise_hook] )); then
  eval "$(mise activate zsh)"
fi
