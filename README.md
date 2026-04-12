# Dotfiles

Personal dotfiles managed with [chezmoi](https://www.chezmoi.io/).

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
