export MISE_CACHE_DIR="$XDG_CACHE_HOME/mise"

if [[ -o interactive ]] && command -v mise >/dev/null 2>&1 && ((!$+functions[_mise_hook])); then
  eval "$(mise activate zsh)"
fi
