# The work dotfiles source applies its executables and shims here. Prepend it so
# its shims shadow the real binaries; it is absent on personal machines.
zsh_work_bin="$HOME/.local/bin/work"
if [[ -d $zsh_work_bin ]]; then
  path=("$zsh_work_bin" ${path:#$zsh_work_bin})
fi

ZSH_WORK_ROOT="${ZSH_WORK_ROOT:-$ZSH_CONFIG_DIR/work}"

_source_zsh_globbed_files "$ZSH_WORK_ROOT/functions"

zsh_work_completions_dir="$ZSH_WORK_ROOT/completions"
[[ -d $zsh_work_completions_dir ]] && fpath=("$zsh_work_completions_dir" $fpath)

zsh_work_config="$ZSH_WORK_ROOT/config.zsh"
[[ -f "$zsh_work_config" ]] && source "$zsh_work_config"
