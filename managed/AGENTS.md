# Managed Configuration Instructions

These instructions define source-state and coordination rules shared across managed configuration.
More specific `AGENTS.md` files retain implementation details for their directories.

## Modify Scripts and Managed Overlays

- Treat `*.managed.*` and `*.managed` overlays as authoritative for the keys or settings they
  contain.
- Keep modify scripts executable through PEP 723 metadata, and declare any third-party runtime
  dependencies inline.
- When a modify script uses the helper library, import it from the repository-root `tools`
  directory. With `.chezmoiroot`, `CHEZMOI_SOURCE_DIR` resolves to `managed/`, so the repository
  root is its parent.

## Reference Agent Configuration

- [`dot_claude`](dot_claude) and [`dot_codex`](dot_codex) contain public-safe reference
  configuration. `.chezmoiignore.tmpl` excludes them from `chezmoi apply`.
- Editing these reference files does not change active configuration under `~/.claude` or
  `~/.codex`. Synchronize changes explicitly only when requested.

## Shell Conventions

- [`dot_config/fish`](dot_config/fish) is the canonical shell configuration. Implement shared
  behavior in fish first, then mirror it in [`dot_config/zsh`](dot_config/zsh) unless the behavior
  is shell-specific or intentionally divergent.
- Keep shell implementations idiomatic to their shell. Match user-facing behavior rather than
  syntax.
- [`dot_local/bin`](dot_local/bin) holds POSIX `sh` shims applied to `~/.local/bin`, which the
  shells keep first on `PATH`. Decide between a shim and shell configuration with this matrix:

  | Put it in                                     | When                                                                                                                                                                                                                              |
  | --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | Shim ([`dot_local/bin`](dot_local/bin))       | The command never mutates the live shell session, should behave identically for every caller (scripts, agents, and non-interactive shells included), and its logic is shell-agnostic and would otherwise be duplicated per shell. |
  | Shell configuration (`functions/`, `conf.d/`) | The behavior changes live shell state (environment variables, `source`, `exec`), is inherently shell-specific, or must run during shell startup.                                                                                  |
  | Interactive abbreviation or alias             | The behavior is only a keystroke convenience for an interactive shell.                                                                                                                                                            |

- A shim that shadows a real binary's name, such as the `op` shim, changes behavior for every
  process on the machine. Shadow deliberately and document why in the shim; give new commands
  distinct names.
- Write shims in POSIX `sh` while they stay thin wrappers. Move a shim to a self-contained,
  standard-library-only Python script once it grows configuration parsing or logic worth testing,
  such as `generate-completions`, and wire it into the Python lint, type-check, and test surface.

### Completions

- Handwritten shell completions may be tracked; generated completions should remain untracked unless
  explicitly requested.
- Completion generation for both shells is handled by the shared
  [`generate-completions`](dot_local/bin/executable_generate-completions) shim. Its registry is the
  chezmoi-managed [`config.json`](dot_config/generate-completions/config.json), rather than
  per-shell generation functions.
- Machine-local commands belong in `~/.config/generate-completions/config.local.json`. A
  `run_onchange_` script reruns generation on `chezmoi apply` when the managed registry changes.

## Editor Conventions

- [`dot_config/nvim`](dot_config/nvim) and the
  [managed VS Code settings](<private_Library/private_Application Support/private_Code/User>) both
  provide Vim-style editing.
- Keep portable, environment-agnostic Vim keybindings, such as `jj` to exit insert mode,
  clear-search, and open-line, in sync between Neovim and the VS Code Vim extension.
- Keep environment-specific behavior where it belongs. Neovim Lua and plugin maps, including LSP,
  terminal-mode, and buffer navigation, stay in `init.lua`; VS Code host concerns, including
  `vim.handleKeys`, extension affinity, and formatter wiring, stay in the VS Code settings.
- The VS Code Vim extension only uses Neovim to execute Ex commands; it does not read `init.lua`
  keymaps. Shared keybindings must therefore be defined in both places.
