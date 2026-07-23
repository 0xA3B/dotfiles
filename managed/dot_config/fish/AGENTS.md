# Fish Shell Instructions

## Role

- `managed/dot_config/fish` is the canonical shell configuration in this repository.
- When shell behavior changes here, review the zsh configuration and mirror the change there unless
  the behavior is inherently fish-specific.
- Prefer updating fish first, then porting the behavior to zsh in a zsh-native way.

## Change Rules

- Preserve the existing layout. Do not collapse `conf.d`, `functions`, or `completions` back into
  `config.fish`.
- Keep fish implementations idiomatic to fish. Do not contort fish code to look like zsh.
- If adding or changing functions, aliases, environment defaults, startup hooks, or completion
  generation here, check whether zsh needs an equivalent update under
  [`managed/dot_config/zsh`](../zsh).
- If a feature should exist only in fish, document why in the change or nearby comments.

## Completions

- Handwritten fish completions may be tracked in [`completions/`](completions).
- Generated fish completions should remain untracked unless explicitly requested.
- Completion generation for both shells is handled by the shared `generate-completions` shim in
  [`managed/dot_local/bin`](../../dot_local/bin); its registry is the chezmoi-managed
  [`config.json`](../generate-completions/config.json) instead of per-shell generation functions.
  Machine-local commands belong in `~/.config/generate-completions/config.local.json`. A
  `run_onchange_` script reruns generation on `chezmoi apply` when the managed registry changes.
