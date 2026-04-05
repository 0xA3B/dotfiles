function __generate_completions_base_registry
    # Format: command<TAB>target-path<TAB>generator command.
    printf '%s\t%s\t%s\n' \
        codex "$__fish_config_dir/completions/codex.fish" "codex completion fish" \
        ruff "$__fish_config_dir/completions/ruff.fish" "ruff generate-shell-completion fish"
end
