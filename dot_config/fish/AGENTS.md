# Fish Shell Instructions

## Role

- `dot_config/fish` is the canonical shell configuration in this repository.
- When shell behavior changes here, review the zsh configuration and mirror the change there unless the behavior is inherently fish-specific.
- Prefer updating fish first, then porting the behavior to zsh in a zsh-native way.

## Structure

- [`config.fish`](config.fish): main startup flow and interactive shell behavior.
- [`conf.d/`](conf.d): focused startup modules such as dotenv loading, virtualenv activation, and work overlay loading.
- [`functions/`](functions): reusable commands and helpers.
- [`completions/`](completions): tracked handwritten completions. Generated completions are not tracked.
- [`themes/`](themes): fish theme files.

## Change Rules

- Preserve the existing layout. Do not collapse `conf.d`, `functions`, or `completions` back into `config.fish`.
- Keep fish implementations idiomatic to fish. Do not contort fish code to look like zsh.
- If adding or changing functions, aliases, environment defaults, startup hooks, or completion generation here, check whether zsh needs an equivalent update under [`dot_config/zsh`](../zsh).
- If a feature should exist only in fish, document why in the change or nearby comments.

## Completions

- Handwritten fish completions may be tracked in [`completions/`](completions).
- Generated fish completions should be regenerated locally via [`generate-completions.fish`](functions/generate-completions.fish) and should remain untracked unless explicitly requested.
- When changing completion generation registries or command mappings, update the zsh registry in parallel.
