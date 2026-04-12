if status is-interactive; and command -q zoxide
    set -gx _ZO_EXCLUDE_DIRS "/tmp:/private/tmp:/Volumes:$HOME/Library"
    zoxide init fish --cmd cd | source
end
