# Hook direnv into interactive fish shells when available.
#
# Optional setting:
#   direnv_fish_mode - defaults to direnv's upstream behavior when unset

if status is-interactive; and command -q direnv; and not functions -q __direnv_export_eval
    direnv hook fish | source
end
