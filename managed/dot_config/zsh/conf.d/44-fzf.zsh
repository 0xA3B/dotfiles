if [[ -o interactive ]] && command -v fzf >/dev/null 2>&1; then
  fzf_opts="--height=40% --layout=reverse --border"

  if command -v bat >/dev/null 2>&1 && command -v eza >/dev/null 2>&1; then
    fzf_opts+=" --preview='test -d {} && eza -la --color=always --icons=auto {} || bat --color=always --style=numbers --line-range=:500 {}'"
  fi

  if command -v fd >/dev/null 2>&1; then
    export FZF_DEFAULT_COMMAND="fd --type f --hidden --follow --exclude .git"
  fi

  export FZF_DEFAULT_OPTS="$fzf_opts"

  if [[ -t 0 && -t 1 ]]; then
    if [[ -f "$HOME/.fzf.zsh" ]]; then
      source "$HOME/.fzf.zsh"
    else
      if fzf --zsh >/dev/null 2>&1; then
        source <(fzf --zsh)
      fi
    fi
  fi
fi
