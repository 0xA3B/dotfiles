# shellcheck shell=bash
# The Claude settings env sets HOMEBREW_PREFIX and XDG_CONFIG_HOME.
# shellcheck disable=SC2154

# Shell setup for Claude Code Bash commands. A SessionStart hook in the Claude settings sources this
# file through CLAUDE_ENV_FILE, so it runs before every Bash command: keep it fast. Static values
# that hooks and MCP servers also need belong in the settings `env` instead, which reaches every
# process Claude Code starts. Secondary sources add setup as drop-ins in claude-env.d/.

# Apply the mise environment of the command's starting directory. `-s bash` must match
# CLAUDE_CODE_SHELL in the Claude settings.
eval "$(mise hook-env -s bash 2>/dev/null)"

# Point TLS clients at Homebrew's CA bundle, as dot_config/fish/conf.d/00-homebrew.fish does.
if [[ -f ${HOMEBREW_PREFIX}/etc/ca-certificates/cert.pem ]]; then
  export SSL_CERT_FILE="${HOMEBREW_PREFIX}/etc/ca-certificates/cert.pem"
  export REQUESTS_CA_BUNDLE="${SSL_CERT_FILE}"
  export NODE_EXTRA_CA_CERTS="${SSL_CERT_FILE}"
  export CURL_CA_BUNDLE="${SSL_CERT_FILE}"
fi

for claude_env_dropin in "${XDG_CONFIG_HOME}"/bash/claude-env.d/*.bash; do
  # shellcheck source=/dev/null
  [[ ! -f ${claude_env_dropin} ]] || source "${claude_env_dropin}"
done
unset claude_env_dropin
