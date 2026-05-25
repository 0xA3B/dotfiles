__generate_completions_registry() {
  # Registries live in helper functions:
  #   - __generate_completions_base_registry
  #   - __generate_completions_work_registry (optional)
  #
  # Registry format:
  #   command<TAB>target-path<TAB>generator-argv...
  # Older 3-field entries with a space-delimited generator command are still
  # supported for compatibility with local work overlays.
  __generate_completions_base_registry

  if (($+functions[__generate_completions_work_registry])); then
    __generate_completions_work_registry
  fi
}

__generate_completions_supported_commands() {
  local entry
  local -a fields

  while IFS= read -r entry; do
    fields=(${(@ps:\t:)entry})
    print -r -- "${fields[1]}"
  done < <(__generate_completions_registry)
}

__generate_completions_registry_entry() {
  local name="$1"
  local entry
  local -a fields

  while IFS= read -r entry; do
    fields=(${(@ps:\t:)entry})
    if [[ ${fields[1]} == "$name" ]]; then
      print -r -- "$entry"
      return 0
    fi
  done < <(__generate_completions_registry)

  return 1
}

__generate_completions_write() {
  local name="$1"
  local target="$2"
  shift 2

  local -a generator=("$@")
  [[ ${#generator[@]} -gt 0 ]] || {
    echo "No completion generator configured for $name" >&2
    return 1
  }

  command -v "${generator[1]}" >/dev/null 2>&1 || {
    echo "$name not found in PATH, skipping completions generation" >&2
    return 1
  }

  local completions_dir="${target:h}"
  command mkdir -p "$completions_dir" || {
    echo "Failed to create completions directory: $completions_dir" >&2
    return 1
  }

  local tmpfile
  tmpfile="$(command mktemp "${target}.tmp.XXXXXX")" || {
    echo "Failed to create temporary file for $name completions" >&2
    return 1
  }

  if "${generator[@]}" >"$tmpfile"; then
    if [[ -s $tmpfile ]]; then
      command mv -f "$tmpfile" "$target" || {
        command rm -f "$tmpfile"
        echo "Failed to install completions for $name" >&2
        return 1
      }

      echo "Generated completions for $name"
      return 0
    fi

    echo "Completion generator for $name produced empty output" >&2
  else
    echo "Failed to generate completions for $name" >&2
  fi

  command rm -f "$tmpfile"
  return 1
}

__generate_completions_one() {
  local name="$1"
  local entry
  entry="$(__generate_completions_registry_entry "$name")" || {
    echo "Unsupported command '$name'" >&2
    return 1
  }

  local -a fields generator
  fields=(${(@ps:\t:)entry})
  generator=("${fields[@]:2}")

  if [[ ${#generator[@]} -eq 1 ]]; then
    generator=(${=generator[1]})
  fi

  __generate_completions_write "${fields[1]}" "${fields[2]}" "${generator[@]}"
}

generate-completions() {
  local -a supported requested unique_requested
  local -A seen

  supported=("${(@f)$(__generate_completions_supported_commands)}")

  if [[ $1 == "-h" || $1 == "--help" ]]; then
    echo "Usage: generate-completions [COMMAND ...]"
    echo
    echo "Regenerate zsh completions for supported commands."
    echo "When no commands are provided, regenerate all supported completions."
    echo
    echo "Supported commands: ${supported[*]}"
    return 0
  fi

  requested=("$@")
  if [[ ${#requested[@]} -eq 0 ]]; then
    requested=("${supported[@]}")
  fi

  local name
  for name in "${requested[@]}"; do
    if [[ -z ${seen[$name]} ]]; then
      unique_requested+=("$name")
      seen[$name]=1
    fi
  done

  local status_code=0
  for name in "${unique_requested[@]}"; do
    if ((${supported[(Ie)$name]} == 0)); then
      echo "Unsupported command '$name'. Supported commands: ${supported[*]}" >&2
      status_code=1
      continue
    fi

    __generate_completions_one "$name" || status_code=1
  done

  return "$status_code"
}
