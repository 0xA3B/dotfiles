function __generate_completions_base_registry
    # Format: command<TAB>target-path<TAB>generator-argv...
    printf '%s\n' \
        (string join \t -- chezmoi "$__fish_config_dir/completions/chezmoi.fish" chezmoi completion fish) \
        (string join \t -- codex "$__fish_config_dir/completions/codex.fish" codex completion fish) \
        (string join \t -- ruff "$__fish_config_dir/completions/ruff.fish" ruff generate-shell-completion fish)
end
