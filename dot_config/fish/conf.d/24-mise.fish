if status is-interactive; and command -q mise; and not functions -q __mise_env_eval
    mise activate fish | source
end
