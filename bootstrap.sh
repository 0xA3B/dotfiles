#!/bin/sh
# Set up a new Mac: install Homebrew, chezmoi, and mise, apply these dotfiles, make fish the login
# shell, remove unused preinstalled apps, and set up the dotfiles repository for development.
#
# Run it in Terminal with:
#
#   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/0xA3B/dotfiles/main/bootstrap.sh)"
#
# Pass the script to bash as an argument instead of piping it in. The Homebrew installer, sudo,
# and chezmoi prompt on standard input, which a pipe would replace with the script itself.
#
# Each step except the test notification skips work that is already done, so the script is safe to
# rerun. When the dotfiles source is already cloned, the script pulls and applies it instead of
# cloning it.
set -eu

github_user=0xA3B
brew=/opt/homebrew/bin/brew
source_dir="${HOME}/.local/share/chezmoi"
# Keep this version within requires-python of the repository's modify scripts.
python_version=3.14

log() {
  printf '==> %s\n' "$*"
}

die() {
  printf 'bootstrap: %s\n' "$*" >&2
  exit 1
}

[ "$(uname -s)" = Darwin ] || die "this script supports macOS only"
[ "$(uname -m)" = arm64 ] || die "this script supports Apple silicon Macs only"

if [ -x "${brew}" ]; then
  log "Homebrew is installed"
else
  log "Installing Homebrew"
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  [ -x "${brew}" ] || die "Homebrew is still missing at ${brew} after its installer ran"
fi
eval "$("${brew}" shellenv)"

for formula in chezmoi mise; do
  if brew list --formula "${formula}" >/dev/null 2>&1; then
    log "${formula} is installed"
  else
    log "Installing ${formula}"
    brew install "${formula}"
  fi
done

# The modify scripts run through uv, and this apply is what writes the uv config that points uv at
# mise's Python. Until then, run chezmoi with mise's Python and uv on PATH, and set uv's Python
# settings to match that config, so uv uses mise's Python instead of downloading its own.
export UV_PYTHON_PREFERENCE=system
export UV_PYTHON_DOWNLOADS=manual
# The after scripts run tools that mise installs during the apply; its shims put them on PATH.
export PATH="${HOME}/.local/share/mise/shims:${PATH}"

if [ -d "${source_dir}/.git" ]; then
  log "Pulling and applying the dotfiles"
  mise exec "python@${python_version}" uv@latest -- chezmoi update --init
else
  log "Cloning and applying the dotfiles"
  mise exec "python@${python_version}" uv@latest -- chezmoi init --apply "${github_user}"
fi

# The apply installed the Homebrew shells. chsh accepts only shells listed in /etc/shells.
for shell in /opt/homebrew/bin/fish /opt/homebrew/bin/zsh; do
  [ -x "${shell}" ] || die "${shell} is missing after the apply"
  if grep -qx "${shell}" /etc/shells; then
    log "${shell} is in /etc/shells"
  else
    log "Adding ${shell} to /etc/shells"
    printf '%s\n' "${shell}" | sudo tee -a /etc/shells >/dev/null
  fi
done

login_shell=/opt/homebrew/bin/fish
if [ "$(dscl . -read "/Users/$(id -un)" UserShell | awk '{print $2}')" = "${login_shell}" ]; then
  log "fish is the login shell"
else
  log "Changing the login shell to fish"
  chsh -s "${login_shell}"
fi

# Remove the Apple apps that macOS preinstalls and these machines don't use. macOS can block the
# removal if Terminal lacks App Management access in System Settings > Privacy & Security.
for app in GarageBand iMovie Keynote; do
  app_path="/Applications/${app}.app"
  if [ ! -d "${app_path}" ]; then
    log "${app} is not installed"
    continue
  fi
  log "Removing ${app}"
  sudo rm -rf "${app_path}" \
    || log "Could not remove ${app}; allow Terminal App Management access and rerun this script"
done

# Install the repository's own tools, dependencies, and Git hooks, for working on the dotfiles.
log "Setting up the dotfiles repository"
mise trust "${source_dir}"
mise -C "${source_dir}" install
mise -C "${source_dir}" run setup

work_machine=$(chezmoi execute-template '{{ .work_machine }}')

# Keep fetching the public repository over HTTPS, which needs no credentials, so a rerun can pull
# before the 1Password SSH agent is set up. Push over SSH with the personal key. On work machines,
# the work source defines a github-personal host alias that selects that key.
if [ "${work_machine}" = true ]; then
  github_host=github-personal
else
  github_host=github.com
fi
push_url="git@${github_host}:${github_user}/dotfiles.git"
if [ "$(git -C "${source_dir}" remote get-url --push origin)" = "${push_url}" ]; then
  log "The dotfiles push to ${push_url}"
else
  log "Pushing the dotfiles to ${push_url}"
  git -C "${source_dir}" remote set-url --push origin "${push_url}"
fi

# The update agent on personal Macs reports failures through notifications, which macOS attributes
# to Script Editor and asks once to allow. Post one now so the request appears while you are here.
if [ "${work_machine}" != true ]; then
  log "Posting a test notification; allow notifications from Script Editor if macOS asks"
  osascript -e 'display notification "update-all posts its failures like this." with title "update-all"' \
    || log "Could not post the test notification"
fi

log "Done. Open a new terminal window to load the shell configuration."
log "Turn on the 1Password SSH agent before you push the dotfiles."
