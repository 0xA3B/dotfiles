if [[ -o interactive ]] && command -v bat >/dev/null 2>&1; then
  export BAT_THEME="Catppuccin Mocha"
  export MANPAGER="sh -c 'col -bx | bat -l man -p'"
  alias cat="bat --paging=never"
fi
