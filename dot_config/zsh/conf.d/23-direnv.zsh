# Hook direnv into interactive zsh shells when available.

if [[ -o interactive ]] && command -v direnv >/dev/null 2>&1; then
  eval "$(direnv hook zsh)"
fi
