if [[ -o interactive ]] && command -v zoxide >/dev/null 2>&1; then
  export _ZO_EXCLUDE_DIRS="/tmp:/private/tmp:/Volumes:$HOME/Library"
  eval "$(zoxide init zsh --cmd cd)"
fi
