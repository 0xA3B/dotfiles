set -gx MISE_CACHE_DIR "$XDG_CACHE_HOME/mise"

if status is-interactive; and command -q mise; and not functions -q __mise_env_eval
    mise activate fish | source
end
