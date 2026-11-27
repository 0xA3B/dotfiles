# Dotfiles

This is my set of personal dotfiles managed with [chezmoi](https://www.chezmoi.io/). Feel free to
explore them for inspiration.

## Set Up a New Mac

On a new Apple silicon Mac, run the bootstrap script in Terminal:

```sh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/0xA3B/dotfiles/main/bootstrap.sh)"
```

Pass the script to `bash` as an argument, as shown. Do not pipe it into a shell. The Homebrew
installer, `sudo`, and `chezmoi init` read their prompts from standard input, and a pipe replaces
standard input with the script.

[`bootstrap.sh`](bootstrap.sh) installs Homebrew, chezmoi, and mise. Then it runs
`chezmoi init --apply` with mise's Python and uv on `PATH`, because the modify scripts need uv
before the apply installs it. The apply also installs the packages in the [Brewfile](#homebrew) and
the tools in the mise config, creates the `~/Code` directories, writes `~/.ssh/config`, and sets the
managed macOS user defaults.

After the apply, the script:

- Adds Homebrew's fish and zsh to `/etc/shells` and makes fish the login shell.
- Removes GarageBand, iMovie, and Keynote. macOS can block the removal if Terminal lacks App
  Management access in System Settings > Privacy & Security.
- Trusts the repository's mise config, then installs its tools, dependencies, and Git hooks with
  `mise run setup`.
- Sets the repository to push over SSH, as described below.
- On personal Macs, posts a test notification, so macOS asks now whether to allow notifications from
  Script Editor, which the [update agent](#unattended-updates) uses to report failures.

These steps prompt for your password through `sudo` and `chsh`.

Each step skips work that is already done, except the test notification, so you can rerun the
script. If the source directory is already cloned, the script pulls and applies it instead of
cloning it.

The script clones and pulls the public repository over HTTPS, which needs no credentials, so a rerun
works before the 1Password SSH agent is set up. It sets the push URL to SSH:
`git@github.com:0xA3B/dotfiles.git` on personal Macs, and `git@github-personal:0xA3B/dotfiles.git`
on work machines. On personal Macs, `~/.ssh/config` points `github.com` at the personal key in the
1Password SSH agent. On work machines, the work source defines the `github-personal` host alias in
`~/.ssh/config.d/`. On every machine, ssh also checks GitHub against the host keys that GitHub
publishes, kept in `~/.ssh/github_known_hosts`, so the first connection asks no questions. Turn on
the 1Password SSH agent before you push.

## Install chezmoi

chezmoi is a standalone tool written in Go. On macOS, the simplest install is:

```sh
brew install chezmoi
```

Other package-manager and binary install options are available in the official docs:

- [Install chezmoi](https://www.chezmoi.io/install/)

## Bootstrap This Repo

To set up a machine without the bootstrap script, install chezmoi as described in
[Install chezmoi](#install-chezmoi), then follow these steps. The repository's modify scripts run
through [uv](https://docs.astral.sh/uv/) during `chezmoi apply`, so install uv first, for example
with `brew install uv`.

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

## Homebrew

The repo manages a curated global Brewfile at
[`managed/dot_config/homebrew/Brewfile.tmpl`](managed/dot_config/homebrew/Brewfile.tmpl). The apps
in its personal block install only when `work_machine` is false. The Brewfile applies only on macOS,
and its install needs Homebrew at `/opt/homebrew/bin/brew`.

When the rendered Brewfile changes, `chezmoi apply` runs `brew bundle install --no-upgrade` through
[`run_onchange_after_10-brew-bundle.sh.tmpl`](managed/run_onchange_after_10-brew-bundle.sh.tmpl).
The install does not run `brew upgrade` on packages that are already installed, although installing
a new package can upgrade a dependency that it needs. chezmoi writes every file before it runs the
install, so a failed install leaves the dotfiles applied, and the next apply retries the install. If
you remove an entry from the Brewfile, the package stays installed until you run `brew uninstall`
for it.

The Brewfile is intentionally limited to machine bootstrap tools, shell/editor utilities, desktop
apps, and fonts. Developer runtimes are managed by mise.

To upgrade packages, run `update-brew`, a command that `chezmoi apply` installs in `~/.local/bin`.
It runs `brew update`, `brew upgrade`, and `brew cleanup`. `brew upgrade` skips casks that Homebrew
marks `auto_updates`, which include every desktop app in the Brewfile, because those apps update
themselves. Homebrew would otherwise upgrade such an app when it falls behind, quitting it and
sometimes asking for `sudo`. The shell configs and `update-all-unattended` set
`HOMEBREW_NO_UPGRADE_AUTO_UPDATES_CASKS` to turn that off; run `brew upgrade --greedy` to upgrade
them anyway.

## Unattended Updates

On personal Macs, `chezmoi apply` installs a launchd agent that runs `update-all` every day at noon.
If the Mac is asleep then, launchd runs it once when the Mac wakes. `update-all` upgrades Homebrew
packages, mise tools, uv tools, and VS Code extensions. It runs every step even when one fails.

The agent runs `update-all-unattended`, which sets up `PATH` and the Homebrew and mise environment,
writes the run's output to `~/Library/Logs/update-all.log`, replacing the previous run's log. If a
run fails, it posts a notification that names the failed steps. The first notification may need you
to allow notifications from Script Editor in System Settings.
[`run_onchange_after_50-load-update-agent.sh.tmpl`](managed/run_onchange_after_50-load-update-agent.sh.tmpl)
loads the agent and reloads it when its plist changes. Work machines skip the agent,
`update-all-unattended`, and the loader script, because work tools usually need the VPN.

To run an update now, run `launchctl kickstart`. To unload the agent until you next log in or an
apply changes its plist, run `launchctl bootout`.

```sh
# Run update-all now
launchctl kickstart "gui/$(id -u)/io.github.0xa3b.update-all"
# Unload the agent
launchctl bootout "gui/$(id -u)/io.github.0xa3b.update-all"
```

## License

This repository is available under the [MIT License](LICENSE).
