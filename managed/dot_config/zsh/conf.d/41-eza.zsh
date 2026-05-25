[[ -o interactive ]] || return

if command -v eza >/dev/null 2>&1; then
  export EZA_GRID_ROWS=10

  ls() {
    command eza -Ghl --classify=auto --color=auto --icons=auto --group-directories-first --git --no-user "$@"
  }

  la() { ls -a "$@"; }
  lt() { ls -T -L 3 "$@"; }
  lat() { ls -aT -L 3 "$@"; }
  lart() { ls -a -s modified --reverse "$@"; }
  lsl() { command eza -l --no-permissions --no-filesize --no-user --no-time "$@"; }
else
  ls() { command ls -lhF --color=auto "$@"; }
  la() { ls -a "$@"; }
  lart() { ls -art "$@"; }
fi
