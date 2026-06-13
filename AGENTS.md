# Project Overview

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
- Use mise for runtime management.
- Use `mise exec --` in non-interactive shells when the command relies on a runtime tool managed by
  mise.
- Use the `package.json` script surface for validation and formatting.
- Use `pnpm run check` as the default full local gate.
- Use the smallest relevant targeted script when narrowing validation.
- Scripts with the `check` suffix should be non-mutating.
- `mise.lock` is the canonical `stylua` version for repo scripts. When updating `stylua`, keep
  `.vscode/settings.json#stylua.targetReleaseVersion` pinned to the same version, including the VS
  Code extension's `v` prefix.
- Keep README user-facing and lightweight.
- Keep AGENTS files agent-facing, lightweight, and focused on durable guidance. Avoid temporary
  notes or details that may go stale quickly.

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
- Keep zsh behavior aligned with fish for user-facing shell behavior unless the behavior is
  fish-specific, zsh-specific, or intentionally divergent.
- Keep shell implementations idiomatic to their shell.
- Do not track generated shell completions unless explicitly requested; handwritten completions may
  be tracked.
