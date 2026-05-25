# Project Overview

## Purpose

Chezmoi managed personal dotfile repo.

## Project Conventions

- Use the conventional commit format for commit messages.

## Repository Model

- This repository is a `chezmoi` source repository.
- Managed files are intended to be materialized with `chezmoi` in `file` mode.
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

## Managed and Unmanaged Files

- Local work overlays such as `~/.config/fish/work` and `~/.config/zsh/work` are outside this
  repository and should only be edited when the user explicitly asks for live-environment changes.

## Glossary

- Managed overlay: a repo-owned sidecar file, usually named `*.managed.*`, that authoritatively
  manages selected keys or settings while preserving unrelated live configuration.
- Modify script: a chezmoi `modify_` script or modify template that transforms existing target-file
  content instead of replacing the whole file.
- Modify helper library: Python helper code under `tools/chezmoi_modify` for use by PEP 723 modify
  scripts.

## Python Helper Conventions

- Keep modify helper code under `tools/chezmoi_modify`.
- Keep tests for modify helper code under `tests`.
- Keep repository tooling such as `pyproject.toml`, `uv.lock`, `tools`, and `tests` outside
  `managed/` unless it must be part of the chezmoi source state.
- Treat `*.managed.*` overlays as authoritative for the keys or settings they contain.
- Keep modify scripts as PEP 723 scripts and declare runtime dependencies inline in each script.
- Do not rely on the root `pyproject.toml` dependencies when a modify script runs under
  `uv run --script`; the root project is only for local development and tests.
- When modify scripts use the helper library, import it from the repository-root `tools` directory.
  With `.chezmoiroot`, `CHEZMOI_SOURCE_DIR` resolves to `managed/`.
- Helper functions should transform text content only; file metadata remains chezmoi's
  responsibility.

## Development Commands

- Prefer the `package.json` command surface for local validation and formatting.
- Use `pnpm run format` to normalize all supported file types through pre-commit hooks.
- Use `pnpm run check` as the default pre-commit or pre-push local gate.
- Use targeted scripts such as `pnpm run format:python:check`, `pnpm run format:shell:check`,
  `pnpm run typecheck`, and `pnpm run test` when narrowing validation to a specific area.

## Shell Conventions

- `managed/dot_config/fish` is the canonical shell configuration in this repository.
- `managed/dot_config/zsh` should mirror fish behavior and structure as closely as practical while
  remaining idiomatic to zsh.
- When changing shared shell behavior, update fish first and then port the user-facing behavior to
  zsh in the same change whenever feasible.
- Do not introduce new zsh-only behavior unless it is required by zsh or explicitly requested.
- Generated fish completions are generally not tracked.
- Only handwritten completions should be committed unless the user explicitly asks to track a
  generated completion file.
