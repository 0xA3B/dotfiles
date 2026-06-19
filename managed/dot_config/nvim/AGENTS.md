# Neovim Instructions

## Role

- `managed/dot_config/nvim` is the canonical standalone Neovim configuration in this repository.
- The managed VS Code settings (`managed/Library/Application Support/Code/User`) provide a parallel
  Vim-style editing experience through the VS Code Vim extension.

## Keybinding Sync

- Keep portable, environment-agnostic Vim keybindings in sync with the VS Code Vim extension
  settings so muscle memory stays consistent across editors.
- Portable keybindings are pure modal motions with no editor, Lua, or plugin dependency, such as
  `jj` to exit insert mode, clear-search, and open-line-without-insert.
- When adding, changing, or removing a portable keybinding here, mirror it in the VS Code Vim
  extension settings, and vice versa.
- The VS Code Vim extension only uses Neovim to execute Ex commands; it does not read `init.lua`
  keymaps. Shared keybindings must therefore be defined in both places.

## Change Rules

- Keep Neovim-only behavior here: Lua and plugin maps (LSP, terminal-mode, buffer navigation,
  diagnostics) have no VS Code equivalent and should not be mirrored.
- Prefer leader-based mappings over shadowing built-in normal-mode commands so default motions stay
  available.
- `mapleader` is `<space>`; keep it aligned with the VS Code Vim extension's leader.
