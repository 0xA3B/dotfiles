# Dotfiles

Personal dotfiles managed with [chezmoi](https://www.chezmoi.io/).

## Goals

- Keep the main dotfiles repo public.
- Support both personal and work machines.
- Manage shared config from this repo.
- Leave work-only overlays and other local-only files unmanaged on each system.
- Prefer symlinked leaf files over full directory ownership.

## Install chezmoi

chezmoi is a standalone tool written in Go. On macOS, the simplest install is:

```sh
brew install chezmoi
```

Other package-manager and binary install options are available in the official docs:

- [Install chezmoi](https://www.chezmoi.io/install/)

## Bootstrap This Repo

If this repo is already cloned to `~/.dotfiles`:

```sh
chezmoi init --source="$HOME/.dotfiles"
chezmoi apply --dry-run --verbose
chezmoi apply
```

If setting up a new machine directly from the hosted repo:

```sh
chezmoi init --apply <repo>
```

The repo includes a `.chezmoi.toml.tmpl` so `chezmoi init` can create an initial
machine-local config automatically. It sets:

- `sourceDir` to the actual source directory used by `chezmoi init`
- `mode = "symlink"` so regular managed files are symlinked back to the repo
- `work_machine` via an init-time prompt, which is used for machine-specific
  ignore behavior

## Work Overlay

This repo is intentionally only the shared/public layer.

Work-specific config should remain local to the machine, for example:

- `~/.config/fish/work/`
- `~/.config/zsh/work.zsh`

The shared shell config is expected to source those local overlays when they
exist, but the overlay files/directories themselves should not live in this
public repo.

## Fish Completions

Fish completions are split into two categories:

- Handwritten completions that are part of the config are tracked in the repo.
- Generated completions are not tracked and should be regenerated locally.

At the moment this means:

- `dot_config/fish/completions/vault.fish` is tracked.
- Generated completions such as `codex.fish` and `ruff.fish` are ignored.

The generation logic lives in:

- `dot_config/fish/functions/generate-completions.fish`
- `dot_config/fish/functions/__generate_completions_base_registry.fish`

Use `generate-completions` locally after installing the relevant tools if you
want those completions available on a machine.

## UV Config

The repo keeps a public base [uv config](/Users/alebaker/.dotfiles/dot_config/uv/uv.toml)
for reference and personal-machine use.

On work machines, chezmoi is configured to skip applying `~/.config/uv/uv.toml`
so a local private/internal index configuration can remain unmanaged on the
system.

## Notes

- In chezmoi `symlink` mode, regular files can be symlinked, but directories are
  still managed as directories. That matches the intended model here: manage
  individual files while allowing extra unmanaged files under config
  directories.
- [`.chezmoiignore.tmpl`](/Users/alebaker/.dotfiles/.chezmoiignore.tmpl) excludes repo
  metadata and local-only state so they are not applied into `$HOME`.
- `~/.config/fish/fish_variables` is currently ignored because Fish manages it
  as machine-specific state.
