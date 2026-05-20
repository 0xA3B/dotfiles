# Project Overview

## Purpose

Chezmoi dotfile repo.

## Project Conventions

- Use the conventional commit format for commit messages.

## Repository Model

- This repository is a `chezmoi` source repository.
- Managed files are intended to be materialized with `chezmoi` in `file` mode.
- Treat files under `dot_*` as the source of truth for committed configuration.
- Inspect live files under `$HOME` only when diagnosing local drift or machine-specific behavior.

## Public and Private Boundaries

- This repository is intended to remain public-safe.
- Do not add private work endpoints, internal package indexes, credentials, tokens, or employer-specific configuration to tracked files.
- Prefer keeping work-only or machine-local configuration outside the repo or behind `chezmoi` template and ignore logic.
- In tracked Markdown and other public-facing repo content, do not use absolute local filesystem paths such as `/Users/...`.
- Prefer relative repository paths for links and references so docs remain portable and do not leak machine-specific paths.

## Managed and Unmanaged Files

- Local work overlays such as `~/.config/fish/work` and `~/.config/zsh/work` are outside this repository and should only be edited when the user explicitly asks for live-environment changes.

## Shell Conventions

- `dot_config/fish` is the canonical shell configuration in this repository.
- `dot_config/zsh` should mirror fish behavior and structure as closely as practical while remaining idiomatic to zsh.
- When changing shared shell behavior, update fish first and then port the user-facing behavior to zsh in the same change whenever feasible.
- Do not introduce new zsh-only behavior unless it is required by zsh or explicitly requested.
- Generated fish completions are generally not tracked.
- Only handwritten completions should be committed unless the user explicitly asks to track a generated completion file.
