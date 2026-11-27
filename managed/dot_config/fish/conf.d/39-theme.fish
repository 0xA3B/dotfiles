# Load the color theme from themes/ in each interactive session instead of saving it to universal
# variables, which fish keeps in the untracked fish_variables file. fish_config recommends this over
# `fish_config theme save`. zsh has no equivalent theme setting, so this file exists only for fish.
if status is-interactive
    fish_config theme choose "Catppuccin Mocha"
end
