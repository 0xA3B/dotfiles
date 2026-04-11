if status is-interactive; and command -q vivid
    set -l colors (vivid generate catppuccin-mocha)
    set -gx LS_COLORS $colors
    set -gx EZA_COLORS $colors
end
