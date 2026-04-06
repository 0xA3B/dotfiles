ZSH_WORK_ROOT="${ZSH_WORK_ROOT:-$HOME/.config/zsh/work}"

_source_zsh_globbed_files "$ZSH_WORK_ROOT/functions"

zsh_work_completions_dir="$ZSH_WORK_ROOT/completions"
[[ -d $zsh_work_completions_dir ]] && fpath=("$zsh_work_completions_dir" $fpath)

zsh_work_config="$ZSH_WORK_ROOT/config.zsh"
[[ -f "$zsh_work_config" ]] && source "$zsh_work_config"
