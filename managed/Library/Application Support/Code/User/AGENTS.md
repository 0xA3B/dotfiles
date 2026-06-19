# VS Code Settings Instructions

## Role

- This directory holds the managed VS Code user configuration applied through chezmoi.
- `settings.managed.jsonc` is an authoritative overlay merged into the live `settings.json` by the
  adjacent `modify_settings.json` script. It manages only the keys it contains and preserves
  unrelated live settings.
- `extensions.managed.txt` lists extensions installed by
  `managed/run_onchange_install-vscode-extensions.sh.tmpl`.

## Managed Settings Rules

- Keep managed settings portable and public-safe. Do not add work-only, secret, or machine-specific
  values (for example absolute user paths, internal endpoints, or account-bound tokens).
- Gate machine- or OS-specific settings behind chezmoi template logic rather than committing
  machine-specific defaults.
- When using chezmoi template directives in this JSONC file, do not let a `{{-` trim marker consume
  the newline after a comment line; it will glue the next key onto the comment and the JSONC parser
  will drop it. Prefer `{{- if ... }}` ... `{{- end }}` so content stays on its own lines.
- `settings.managed.jsonc` and `modify_settings.json` are excluded from formatting; keep them
  hand-formatted and valid JSONC.

## Keybinding Sync

- Keep portable, environment-agnostic Vim keybindings (pure modal motions such as `jj` to exit
  insert, clear-search, and open-line) in sync with Neovim's `init.lua` (`managed/dot_config/nvim`)
  so muscle memory stays consistent across editors.
- The VS Code Vim extension only uses Neovim to execute Ex commands; it does not read `init.lua`
  keymaps, so shared keybindings must be defined here as well.
- Keep VS Code host concerns here only: `vim.handleKeys`, extension affinity, and formatter wiring
  have no standalone-Neovim equivalent and should not be mirrored to `init.lua`.
