set -l work_root "$__fish_config_dir/work"

if test -d $work_root
    set -l work_functions "$work_root/functions"
    if test -d $work_functions; and not contains -- $work_functions $fish_function_path
        set -g fish_function_path $work_functions $fish_function_path
    end

    set -l work_completions "$work_root/completions"
    if test -d $work_completions; and not contains -- $work_completions $fish_complete_path
        set -g fish_complete_path $work_completions $fish_complete_path
    end

    set -l work_config "$work_root/config.fish"
    if test -f $work_config
        source $work_config
    end
end
