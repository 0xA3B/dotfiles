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

Initial setup may prompt for machine-specific configuration so chezmoi can apply the right managed
state for the system.

The root `.chezmoiroot` file points chezmoi at `managed/`, keeping managed dotfiles separate from
project-local test, lint, and package-manager configuration.

## Bootstrap Homebrew

The repo manages a curated global Brewfile at
[`managed/dot_config/homebrew/Brewfile`](managed/dot_config/homebrew/Brewfile).

Install the fresh-machine Homebrew (requires `chezmoi apply`):

```sh
brew bundle install --global
```

The Brewfile is intentionally limited to machine bootstrap tools, shell/editor utilities, desktop
apps, and fonts. Developer runtimes are managed by mise.
