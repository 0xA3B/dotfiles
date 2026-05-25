typeset -U path fpath

_source_zsh_globbed_files() {
  local dir="$1"
  local file

  [[ -d $dir ]] || return 0

  for file in "$dir"/*.zsh(N); do
    source "$file"
  done
}

ZSH_CONFIG_DIR="${ZSH_CONFIG_DIR:-$HOME/.config/zsh}"

_source_zsh_globbed_files "$ZSH_CONFIG_DIR/functions"
_source_zsh_globbed_files "$ZSH_CONFIG_DIR/conf.d"
