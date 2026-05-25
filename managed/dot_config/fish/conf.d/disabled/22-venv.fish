# Deprecated: mise now handles uv project venv activation via
# python.uv_venv_auto in managed/dot_config/mise/config.toml.
#
# To restore this fish-only fallback, move this file back to
# managed/dot_config/fish/conf.d/22-venv.fish.
#
# Auto-activate Python virtual environments on directory change
#
# Settings (set these before this file loads to override):
#   autovenv_enable   - "yes" to enable (default: yes)
#   autovenv_announce - "yes" to print messages (default: yes)
#   autovenv_dir      - venv directory name (default: .venv)

if status is-interactive
    set -q autovenv_enable; or set -g autovenv_enable yes
    set -q autovenv_announce; or set -g autovenv_announce yes
    set -q autovenv_dir; or set -g autovenv_dir ".venv"
end

function _autovenv_deactivate --description "Deactivate the current venv, even if fish did not define deactivate"
    if functions -q deactivate
        deactivate
        return
    end

    if test -n "$VIRTUAL_ENV"
        set -l venv_bin "$VIRTUAL_ENV/bin"
        if contains -- $venv_bin $PATH
            set -gx PATH (string match -v -- $venv_bin $PATH)
        end
    end

    set -e VIRTUAL_ENV
    set -e VIRTUAL_ENV_PROMPT
end

function _autovenv_apply
    # Skip if disabled or non-interactive
    if test "$autovenv_enable" != yes; or not status is-interactive
        return
    end

    # Walk up the directory tree looking for a venv
    set -l dir (pwd)
    set -l venv_source ""

    while test "$dir" != /
        set -l activate "$dir/$autovenv_dir/bin/activate.fish"
        if test -e "$activate"
            set venv_source "$activate"
            if test "$autovenv_announce" = yes
                set -g __autovenv_old $__autovenv_new
                set -g __autovenv_new (basename $dir)
            end
            break
        end
        set dir (dirname $dir)
    end

    # Case 1: No active venv, found one - activate it
    if test -z "$VIRTUAL_ENV" -a -n "$venv_source"
        source "$venv_source"
        if test "$autovenv_announce" = yes
            echo "Activated Virtual Environment ($__autovenv_new)"
        end
        return
    end

    # Case 2: Have active venv
    if test -n "$VIRTUAL_ENV"
        # Check if we're still within the active venv's project
        set -l in_current_venv (string match -q "$VIRTUAL_ENV*" "$venv_source"; and echo "yes")

        if test -z "$venv_source"
            # Left venv project - deactivate
            _autovenv_deactivate
            if test "$autovenv_announce" = yes
                echo "Deactivated Virtual Environment ($__autovenv_new)"
                set -e __autovenv_new __autovenv_old
            end
        else if test "$in_current_venv" != yes
            # Switched to different venv project
            _autovenv_deactivate
            source "$venv_source"
            if test "$autovenv_announce" = yes
                echo "Switched Virtual Environments ($__autovenv_old => $__autovenv_new)"
            end
        end
    end
end

function _autovenv_on_pwd --on-variable PWD --description "Auto-activate venv on directory change"
    _autovenv_apply
end

function _autovenv_on_init --on-event fish_prompt --description "Auto-activate venv on shell init"
    if test "$_autovenv_initialized" != 1
        set -g _autovenv_initialized 1
        _autovenv_apply
    end
end

set -g _autovenv_initialized 0
