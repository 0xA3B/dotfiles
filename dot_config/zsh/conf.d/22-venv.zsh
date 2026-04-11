# Auto-activate Python virtual environments on directory change
#
# Settings (set these before this file loads to override):
#   autovenv_enable   - "yes" to enable (default: yes)
#   autovenv_announce - "yes" to print messages (default: yes)
#   autovenv_dir      - venv directory name (default: .venv)

if [[ -o interactive ]]; then
  [[ -z ${autovenv_enable+x} ]] && autovenv_enable="yes"
  [[ -z ${autovenv_announce+x} ]] && autovenv_announce="yes"
  [[ -z ${autovenv_dir+x} ]] && autovenv_dir=".venv"
fi

_autovenv_apply() {
  [[ $autovenv_enable == "yes" ]] || return
  [[ -o interactive ]] || return

  local dir="$PWD"
  local venv_source=""

  while [[ $dir != "/" ]]; do
    local activate="$dir/$autovenv_dir/bin/activate"
    if [[ -e $activate ]]; then
      venv_source="$activate"
      if [[ $autovenv_announce == "yes" ]]; then
        __autovenv_old="$__autovenv_new"
        __autovenv_new="${dir:t}"
      fi
      break
    fi
    dir="${dir:h}"
  done

  if [[ -z $VIRTUAL_ENV && -n $venv_source ]]; then
    source "$venv_source"
    if [[ $autovenv_announce == "yes" ]]; then
      echo "Activated Virtual Environment ($__autovenv_new)"
    fi
    return
  fi

  if [[ -n $VIRTUAL_ENV ]]; then
    if [[ -z $venv_source ]]; then
      if typeset -f deactivate >/dev/null 2>&1; then
        deactivate
      fi
      if [[ $autovenv_announce == "yes" ]]; then
        echo "Deactivated Virtual Environment ($__autovenv_new)"
        unset __autovenv_new __autovenv_old
      fi
    elif [[ $venv_source != "$VIRTUAL_ENV"* ]]; then
      if typeset -f deactivate >/dev/null 2>&1; then
        deactivate
      fi
      source "$venv_source"
      if [[ $autovenv_announce == "yes" ]]; then
        echo "Switched Virtual Environments ($__autovenv_old => $__autovenv_new)"
      fi
    fi
  fi
}

_autovenv_on_init() {
  if [[ $_autovenv_initialized != "1" ]]; then
    _autovenv_initialized=1
    _autovenv_apply
  fi
}

_autovenv_initialized=0

autoload -Uz add-zsh-hook
add-zsh-hook chpwd _autovenv_apply
add-zsh-hook precmd _autovenv_on_init
