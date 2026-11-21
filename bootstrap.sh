#!/bin/sh
# Set up a new Mac: install Homebrew, chezmoi, and mise, then apply these dotfiles.
#
# Run it in Terminal with:
#
#   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/0xA3B/dotfiles/main/bootstrap.sh)"
#
# Pass the script to bash as an argument instead of piping it in. The Homebrew installer, sudo,
# and chezmoi prompt on standard input, which a pipe would replace with the script itself.
#
# Each step skips work that is already done, so the script is safe to rerun. When the dotfiles
# source is already cloned, the script pulls and applies it instead of cloning it.
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

log "Done. Open a new terminal window to load the shell configuration."
