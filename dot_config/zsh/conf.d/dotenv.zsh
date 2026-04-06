# Auto-load .env files on directory change with nesting support
#
# Settings (set these before this file loads to override):
#   dotenv_enable   - "yes" to enable (default: yes)
#   dotenv_announce - "yes" to print messages (default: yes)
#   dotenv_filename - env file name (default: .env)
#
# Supports nested .env files: child directories override parent values,
# and leaving a child directory restores parent values.
#
# Unset directive: Use `# unset: VAR` in .env to unset a variable.
# The original value is restored when leaving the directory.

if [[ -o interactive ]]; then
  [[ -z ${dotenv_enable+x} ]] && dotenv_enable="yes"
  [[ -z ${dotenv_announce+x} ]] && dotenv_announce="yes"
  [[ -z ${dotenv_filename+x} ]] && dotenv_filename=".env"
fi

typeset -a _dotenv_stack
typeset -a _dotenv_file_vars
typeset -a _dotenv_saved_vals
_dotenv_initialized=0

_dotenv_parse() {
  local file="$1"
  [[ -f $file ]] || return 0

  local line
  while IFS= read -r line; do
    [[ $line =~ '^\s*$' ]] && continue

    if [[ $line =~ '^\s*#\s*unset:\s*([A-Za-z_][A-Za-z0-9_]*)\s*$' ]]; then
      echo "!${match[1]}"
      continue
    fi

    [[ $line =~ '^\s*#' ]] && continue

    if [[ $line =~ '^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$' ]]; then
      local key="${match[1]}"
      local val="${match[2]}"

      if [[ $val == "\""*"\"" && $val == *"\"" ]]; then
        val="${val#\"}"
        val="${val%\"}"
      elif [[ $val == "'"*"'" && $val == *"'" ]]; then
        val="${val#'}"
        val="${val%'}"
      fi

      echo "$key=$val"
    fi
  done < "$file"
}

_dotenv_load() {
  local file="$1"
  [[ -f $file ]] || return 1

  local line
  while IFS= read -r line; do
    if [[ $line == "!"* ]]; then
      local key="${line#!}"

      _dotenv_file_vars+=("$file:$key")
      if [[ -v $key ]]; then
        _dotenv_saved_vals+=("${(P)key}")
      else
        _dotenv_saved_vals+=("__DOTENV_UNSET__")
      fi

      unset "$key"
    else
      local key="${line%%=*}"
      local val="${line#*=}"

      _dotenv_file_vars+=("$file:$key")
      if [[ -v $key ]]; then
        _dotenv_saved_vals+=("${(P)key}")
      else
        _dotenv_saved_vals+=("__DOTENV_UNSET__")
      fi

      export "$key=$val"
    fi
  done < <(_dotenv_parse "$file")

  _dotenv_stack+=("$file")
}

_dotenv_unload() {
  local file="$1"

  local i
  for (( i=${#_dotenv_file_vars[@]}; i>=1; i-- )); do
    local entry="${_dotenv_file_vars[i]}"
    if [[ $entry == "$file:"* ]]; then
      local key="${entry#"$file:"}"
      local saved="${_dotenv_saved_vals[i]}"

      if [[ $saved == "__DOTENV_UNSET__" ]]; then
        unset "$key"
      else
        export "$key=$saved"
      fi

      unset "_dotenv_file_vars[i]" "_dotenv_saved_vals[i]"
    fi
  done

  _dotenv_stack=(${(@)_dotenv_stack:#$file})
}

_dotenv_get_target_stack() {
  local -a result
  local dir="$PWD"

  while [[ $dir != "/" ]]; do
    local envfile="$dir/$dotenv_filename"
    if [[ -f $envfile ]]; then
      result=("$envfile" "${result[@]}")
    fi
    dir="${dir:h}"
  done

  print -r -l -- "${result[@]}"
}

_dotenv_apply() {
  [[ $dotenv_enable == "yes" ]] || return
  [[ -o interactive ]] || return

  local -a target
  target=(${(f)"$(_dotenv_get_target_stack)"})

  local common=0
  local max_common=$(( ${#_dotenv_stack[@]} < ${#target[@]} ? ${#_dotenv_stack[@]} : ${#target[@]} ))

  local i
  for (( i=1; i<=max_common; i++ )); do
    if [[ ${_dotenv_stack[i]} == ${target[i]} ]]; then
      common=$i
    else
      break
    fi
  done

  if (( ${#_dotenv_stack[@]} > common )); then
    for (( i=${#_dotenv_stack[@]}; i>common; i-- )); do
      local file="${_dotenv_stack[i]}"
      if [[ $dotenv_announce == "yes" ]]; then
        echo "Unloaded $file"
      fi
      _dotenv_unload "$file"
    done
  fi

  if (( ${#target[@]} > common )); then
    for (( i=common+1; i<=${#target[@]}; i++ )); do
      local file="${target[i]}"
      [[ -f $file ]] || continue
      if [[ $dotenv_announce == "yes" ]]; then
        echo "Loaded $file"
      fi
      _dotenv_load "$file"
    done
  fi
}

_dotenv_on_init() {
  if [[ $_dotenv_initialized != "1" ]]; then
    _dotenv_initialized=1
    _dotenv_apply
  fi
}

autoload -Uz add-zsh-hook
add-zsh-hook chpwd _dotenv_apply
add-zsh-hook precmd _dotenv_on_init
