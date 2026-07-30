# Zsh Shell Instructions

## Change Rules

- Do not introduce new zsh-only behavior unless it is required by zsh or explicitly requested.
- Mirror the fish structure conceptually: main config, `conf.d`, `functions`, `completions`, and
  work overlay loading.
- If zsh must intentionally diverge from fish, keep the divergence minimal and document the reason
  in code comments or the change summary.

## Completions

- Use zsh-native completion files in [`completions/`](completions) and `fpath`/`compinit`
  conventions.
