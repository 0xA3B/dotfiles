# Project Overview

## Purpose

My personal dotfiles repository to manage and share my configuration files across different machines.

## Project Conventions

- Use the conventional commit format for commit messages.

## Repository Model

- This repository is a `chezmoi` source repository, not a GNU Stow repository.
- Managed files are intended to be materialized with `chezmoi` in `symlink` mode.
- Treat files under `dot_*` as the source of truth even if the live file in `$HOME` is a symlink.

## Public and Private Boundaries

- This repository is intended to remain public-safe.
- Do not add private work endpoints, internal package indexes, credentials, tokens, or employer-specific configuration to tracked files.
- Prefer keeping work-only or machine-local configuration outside the repo or behind `chezmoi` template and ignore logic.
- In tracked Markdown and other public-facing repo content, do not use absolute local filesystem paths such as `/Users/...`.
- Prefer relative repository paths for links and references so docs remain portable and do not leak machine-specific paths.

## Managed and Unmanaged Files

- `dot_config/uv/uv.toml` is the public base UV config in the repo, but it may be intentionally ignored on work machines via `.chezmoiignore.tmpl`.
- `dot_config/fish/fish_variables` is intentionally unmanaged and should not be added to the repository.
- Local work overlays such as `~/.config/fish/work` and `~/.config/zsh/work` are outside this repository and should only be edited when the user explicitly asks for live-environment changes.

## Shell Conventions

- `dot_config/fish` is the canonical shell configuration in this repository.
- `dot_config/zsh` should mirror fish behavior and structure as closely as practical while remaining idiomatic to zsh.
- When changing shared shell behavior, update fish first and then port the user-facing behavior to zsh in the same change whenever feasible.
- Do not introduce new zsh-only behavior unless it is required by zsh or explicitly requested.
- Generated fish completions are generally not tracked.
- Only handwritten completions should be committed unless the user explicitly asks to track a generated completion file.
- Use `generate-completions` to regenerate local completion files for both fish and zsh.
- For bash-style environment output, prefer `source-bash` as the user-facing command and keep `bash2fish` as the translator helper.
- `bash2fish` only supports these input patterns:
  - `KEY=value;`
  - `export ...`
  - `unset ...`

## Workspace Hygiene

- Keep `.vscode/` minimal and limited to settings that materially help this repository.
- Do not add empty recommendation files or personal editor-preference extensions unless the user explicitly wants them tracked.
