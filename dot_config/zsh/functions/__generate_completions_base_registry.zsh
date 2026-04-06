__generate_completions_base_registry() {
  # Format: command<TAB>target-path<TAB>generator-argv...
  printf '%s\n' \
    "$(printf '%s\t%s\t%s\t%s\t%s' chezmoi "$HOME/.config/zsh/completions/_chezmoi" chezmoi completion zsh)" \
    "$(printf '%s\t%s\t%s\t%s\t%s' codex "$HOME/.config/zsh/completions/_codex" codex completion zsh)" \
    "$(printf '%s\t%s\t%s\t%s\t%s' ruff "$HOME/.config/zsh/completions/_ruff" ruff generate-shell-completion zsh)"
}
