# Project Instructions

## Purpose

This repository maintains a public-safe, reproducible baseline for personal machine setup with
chezmoi. Changes should preserve these outcomes:

- Managed dotfiles apply cleanly from `managed/` with `chezmoi apply`.
- Work-only, private, secret, and machine-local state stays out of tracked public files unless it is
  protected by template or ignore logic.
- Baseline shell, editor, runtime, package-manager, and bootstrap behavior stays consistent across
  machines while leaving room for local overlays.
- Repository tooling and modify helpers remain small, testable, and focused on safely managing
  selected configuration state.

## Repository Model

- This repository is a `chezmoi` source repository.
- Managed files are intended to be materialized with `chezmoi apply`.
- `.chezmoiroot` points chezmoi at `managed/`; treat files under `managed/dot_*` as the source of
  truth for committed configuration.
- Inspect live files under `$HOME` only when diagnosing local drift or machine-specific behavior.

## Public and Private Boundaries

- This repository is intended to remain public-safe.
- Do not add private work endpoints, internal package indexes, credentials, tokens, or
  employer-specific configuration to tracked files.
- Prefer keeping work-only or machine-local configuration outside the repo or behind `chezmoi`
  template and ignore logic.
- In tracked Markdown and other public-facing repo content, do not use absolute local filesystem
  paths such as `/Users/...`.
- Prefer relative repository paths for links and references so docs remain portable and do not leak
  machine-specific paths.

## Glossary

- **Managed overlay:** a repo-owned sidecar file, usually named `*.managed.*`, that authoritatively
  manages selected keys or settings while preserving unrelated live configuration.
- **Modify script:** a chezmoi `modify_` script or modify template that transforms existing
  target-file content instead of replacing the whole file.
- **Modify helper library:** Python helper code under `tools/chezmoi_modify` for use by PEP 723
  modify scripts.

## Project Conventions

- Use the conventional commit format for commit messages.
- Use mise for runtime management and project tasks.
- Use `mise exec --` in non-interactive shells when the command relies on a runtime tool managed by
  mise.
- Use the `mise.toml` task surface (`mise run`) for validation and formatting.
- Use `mise run check` as the default full local gate.
- Use the smallest relevant targeted task when narrowing validation.
- Tasks with the `check` suffix should be non-mutating.
- `format` tasks mutate by default and pair with `:check` variants; `lint` tasks are non-mutating by
  default and pair with `:fix` variants when the linter supports autofixes.
- Define each format and lint command once in the mise task surface; pre-commit hooks delegate to
  `mise run` and stay focused on fast checks and safe fixes for files participating in Git
  operations, plus the pre-push test gate.
- Reserve the pre-commit `manual` stage for hooks that do not run at commit time; CI covers them via
  `mise run format:hygiene`.
- Keep README user-facing and lightweight.
- Keep AGENTS files agent-facing, lightweight, and focused on durable guidance. Avoid temporary
  notes or details that may go stale quickly.
- Treat `AGENTS.md` as canonical agent guidance; sibling `CLAUDE.md` files must import `@AGENTS.md`
  and may add Claude-specific guidance only when it doesn't belong in `AGENTS.md`.

## Dependency Policy

- Treat `pyproject.toml` and `package.json` as compatibility manifests. Leave direct dependencies
  unbounded unless a compatibility or security requirement justifies a constraint.
- Add lower bounds for required features or vulnerable older releases, upper bounds for
  intentionally deferred incompatibilities, exclusions for known-bad releases, and exact pins only
  when a single version is required.
- Constrain transitive Python dependencies with `tool.uv.constraint-dependencies` instead of
  declaring them as direct dependencies.
- Treat `uv.lock` and `pnpm-lock.yaml` as the exact tested resolutions; do not edit them manually.
- Keep lockfiles current through Renovate (`.github/renovate.jsonc`): in-range updates land as
  lockfile-only PRs via `rangeStrategy: update-lockfile`, and scheduled `lockFileMaintenance`
  refreshes transitive dependencies; do not regenerate lockfiles locally as routine maintenance.
- Treat the `[tools]` table in `mise.toml` as the compatibility manifest for repo tooling and
  `mise.lock` as its tested resolution; Renovate manages both, including `mise.lock` regeneration
  and the `package.json` `packageManager` pin.
- Runtime versions are managed manually: Renovate is configured not to update `.node-version`,
  `.python-version`, `requires-python` in `pyproject.toml` or PEP 723 script blocks, or
  `package.json` `engines`.
- Apply a three-day cooldown to new releases from public registries, enforced consistently through
  Renovate `minimumReleaseAge`, pnpm `minimumReleaseAge`, mise `minimum_release_age`, and uv
  `exclude-newer`.

## Python Helper Conventions

- Keep modify helper code in `tools/chezmoi_modify` with tests in `tests`.
- Keep repository tooling outside `managed/` unless it must be part of the chezmoi source state.
- Treat `*.managed.*` overlays as authoritative for the keys or settings they contain.
- Keep modify scripts self-contained as PEP 723 scripts with inline runtime dependencies.
- When modify scripts use the helper library, import it from the repository-root `tools` directory.
  With `.chezmoiroot`, `CHEZMOI_SOURCE_DIR` resolves to `managed/`.
- Keep helper functions focused on text transforms; chezmoi remains responsible for file metadata.

## Shell Conventions

- `managed/dot_config/fish` is the canonical shell configuration.
- `managed/dot_local/bin` holds POSIX `sh` shims applied to `~/.local/bin`, which the shells keep
  first on `PATH`. Decide between a shim and shell config with this matrix:

  | Put it in                                                | When                                                                                                                                                                                                                              |
  | -------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | Shim (`managed/dot_local/bin`)                           | The command never mutates the live shell session, should behave identically for every caller (scripts, agents, and non-interactive shells included), and its logic is shell-agnostic and would otherwise be duplicated per shell. |
  | Shell config (`functions/`, `conf.d/`, abbrs or aliases) | The behavior changes live shell state (environment variables, `source`, `exec`), is an interactive keystroke convenience, or is inherently specific to one shell.                                                                 |

- A shim that shadows a real binary's name (like the `op` shim) changes behavior for every process
  on the machine; shadow deliberately and document why in the shim. Give new commands distinct
  names.
- Write shims in POSIX `sh` while they stay thin wrappers; move a shim to a self-contained,
  stdlib-only Python script once it grows configuration parsing or logic worth testing (like
  `generate-completions`), and wire it into the Python lint, type-check, and test surface.
- Keep zsh behavior aligned with fish for user-facing shell behavior unless the behavior is
  fish-specific, zsh-specific, or intentionally divergent.
- Keep shell implementations idiomatic to their shell.
- Do not track generated shell completions unless explicitly requested; handwritten completions may
  be tracked.

## Editor Conventions

- Neovim (`managed/dot_config/nvim`) and the managed VS Code settings
  (`managed/Library/Application Support/Code/User`) both provide Vim-style editing.
- Keep portable, environment-agnostic Vim keybindings (pure modal motions such as `jj` to exit
  insert, clear-search, and open-line) in sync between Neovim's `init.lua` and the VS Code Vim
  extension settings so muscle memory stays consistent across editors.
- Keep environment-specific behavior where it belongs: Neovim, Lua, and plugin maps (LSP,
  terminal-mode, buffer navigation) stay in `init.lua`; VS Code host concerns (`vim.handleKeys`,
  extension affinity) stay in the VS Code settings.
- The VS Code Vim extension only uses Neovim to execute Ex commands; it does not read `init.lua`
  keymaps, so shared keybindings must be defined in both places.
