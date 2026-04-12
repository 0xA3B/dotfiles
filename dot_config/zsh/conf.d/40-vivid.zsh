if [[ -o interactive ]] && command -v vivid >/dev/null 2>&1; then
  export LS_COLORS="$(vivid generate catppuccin-mocha)"
  export EZA_COLORS="$LS_COLORS"
fi
