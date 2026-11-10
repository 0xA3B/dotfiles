# Dotfiles

This is my set of personal dotfiles managed with [chezmoi](https://www.chezmoi.io/). Feel free to
explore them for inspiration.

## Install chezmoi

chezmoi is a standalone tool written in Go. On macOS, the simplest install is:

```sh
brew install chezmoi
```

Other package-manager and binary install options are available in the official docs:

- [Install chezmoi](https://www.chezmoi.io/install/)

## Bootstrap This Repo

The repository's modify scripts run through [uv](https://docs.astral.sh/uv/) during `chezmoi apply`,
so install uv first, for example with `brew install uv`.

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

## Apply Secondary Sources

A machine can also apply secondary sources: separate, private chezmoi source repositories checked
out at `managed-<name>/` in this repository. The `dotfiles` command applies this repository first
and then each secondary source.
[ADR 0001](docs/adr/0001-secondary-sources-as-nested-repositories.md) records the design.

`dotfiles` also runs through uv, installed as described in
[Bootstrap This Repo](#bootstrap-this-repo).

If you answer yes to "Is this a work machine?" during `chezmoi init`, it also asks for the work
source's Git URL. An empty answer configures no work source. To set the URL later, run
`chezmoi edit-config` and set `work` under `[data.dotfiles_sources]`.

After `chezmoi apply` installs `~/.local/bin/dotfiles`, apply the secondary sources. If a tool on
the machine must not read work content, follow [Set Up a Work Machine](#set-up-a-work-machine)
instead of the next command. Otherwise, run:

```sh
~/.local/bin/dotfiles init
```

`dotfiles init` reruns `chezmoi init`, which prompts for settings added since the last run. Then it
clones each configured secondary source that is not checked out yet and applies it. If the apply
step fails, fix the cause and run `dotfiles apply`. A rerun of `dotfiles init` skips a source that
is already checked out.

After setup, use `dotfiles update`, `dotfiles apply`, `dotfiles diff`, and `dotfiles status` to act
on every source. Plain `chezmoi` acts on this repository only. To run a chezmoi command against one
secondary source, use `dotfiles <name> <chezmoi arguments>`, such as `dotfiles work diff`. The
aggregate verbs accept only the flags `-n`, `--dry-run`, `-v`, `--verbose`, and `--force`; to pass
other arguments, use plain `chezmoi` for this repository or `dotfiles <name>` for a secondary
source.

### Set Up a Work Machine

The work source's checkout is inside this repository, so a tool that reads this repository can also
read `managed-work/`. Git ignores the checkout, which keeps it out of commits, but Git does not
control what such a tool reads. If a tool on the machine must not read work content, such as a
coding agent that uses this repository as its working directory, set up the machine in this order:

1. Use the tool's own permission settings to deny it read and write access to
   `~/.local/share/chezmoi/managed-work/`.
2. Run `~/.local/bin/dotfiles init` in a shell that the tool does not control. If `chezmoi init`
   prompts for the work source's Git URL, enter it.
3. Confirm that the tool cannot read a file under `~/.local/share/chezmoi/managed-work/`.

### Work in a Secondary Source

A secondary source uses this repository's tooling, so it has no CI or lint configuration of its own.
A secondary source must not ship a chezmoi config template (`.chezmoi.<format>.tmpl`), which would
replace the shared config; `dotfiles` refuses to run against a source that has one.

From inside `managed-<name>/`, install the commit hooks once:

```sh
uv run pre-commit install -c ../.pre-commit-config.yaml -t pre-commit -t commit-msg
```

Before you push, run the format and lint checks. Run from inside `managed-<name>/`, these tasks
check only that checkout. The `:::` separates the two mise tasks.

```sh
mise run format:check ::: lint
```

## Bootstrap Homebrew

The repo manages a curated global Brewfile at
[`managed/dot_config/homebrew/Brewfile`](managed/dot_config/homebrew/Brewfile).

Install the fresh-machine Homebrew (requires `chezmoi apply`):

```sh
brew bundle install --global
```

The Brewfile is intentionally limited to machine bootstrap tools, shell/editor utilities, desktop
apps, and fonts. Developer runtimes are managed by mise.

## License

This repository is available under the [MIT License](LICENSE).
