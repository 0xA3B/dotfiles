# Dotfiles

Personal dotfiles managed with [chezmoi](https://www.chezmoi.io/).

Chezmoi source-state files live under [`managed/`](managed/). Repository tooling and development
configuration stay at the repo root.

## Install chezmoi

chezmoi is a standalone tool written in Go. On macOS, the simplest install is:

```sh
brew install chezmoi
```

Other package-manager and binary install options are available in the official docs:

- [Install chezmoi](https://www.chezmoi.io/install/)

## Bootstrap This Repo

Initialize the default chezmoi source directory from GitHub:

```sh
chezmoi init 0xA3B
chezmoi apply --dry-run --verbose
chezmoi apply
```

If setting up a new machine directly from the hosted repo:

```sh
chezmoi init --apply 0xA3B
```

The repo includes `managed/.chezmoi.toml.tmpl` so `chezmoi init` can create an initial machine-local
config automatically. It sets:

- `mode = "file"` so managed files are materialized as normal files
- `work_machine` via an init-time prompt, which is used for machine-specific ignore behavior

The root `.chezmoiroot` file points chezmoi at `managed/`, keeping managed dotfiles separate from
project-local test, lint, and package-manager configuration.
