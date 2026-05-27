# Agent/test shells may be interactive while using TERM=dumb; starship errors
# there because the terminal advertises no prompt-rendering capabilities.
if [[ -o interactive && ${TERM:-} != "dumb" ]] && command -v starship >/dev/null 2>&1; then
  eval "$(starship init zsh)"
fi
