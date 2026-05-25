if [[ -o interactive ]]; then
  zsh_completions_dir="$ZSH_CONFIG_DIR/completions"
  [[ -d $zsh_completions_dir ]] && fpath=("$zsh_completions_dir" $fpath)

  autoload -Uz compinit
  mkdir -p "$HOME/.local/share/zsh"
  compinit -i -d "$HOME/.local/share/zsh/.zcompdump-${ZSH_VERSION}"
fi
