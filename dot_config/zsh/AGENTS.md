# Zsh Shell Instructions

## Role

- `dot_config/zsh` is not the canonical shell configuration. Fish is the source of truth.
- Keep zsh behavior aligned with [`dot_config/fish`](../fish) as closely as practical.
- When fish changes, mirror the user-facing behavior in zsh unless the feature is fish-specific or zsh cannot support it cleanly.

## Structure

- [`config.zsh`](config.zsh): main startup flow and interactive shell behavior.
- [`conf.d/`](conf.d): focused startup modules such as dotenv loading, virtualenv activation, and work overlay loading.
- [`functions/`](functions): reusable zsh commands and helpers.
- [`completions/`](completions): tracked handwritten completions. Generated completions are not tracked.

## Change Rules

- Do not introduce new zsh-only behavior unless it is required by zsh or explicitly requested.
- Mirror fish structure conceptually: main config, `conf.d`, `functions`, `completions`, and work overlay loading.
- Keep zsh implementations native to zsh. Match fish behavior, not fish syntax.
- If fish behavior changes, update zsh in the same change whenever feasible.
- If zsh must intentionally diverge from fish, keep the divergence minimal and document the reason in code comments or the change summary.

## Completions

- Use zsh-native completion files in [`completions/`](completions) and `fpath`/`compinit` conventions.
- Generated zsh completions should be regenerated locally via [`generate-completions.zsh`](functions/generate-completions.zsh) and should remain untracked unless explicitly requested.
- When changing completion generation registries or command mappings here, make sure the fish completion registry remains in sync with the intended command set.
