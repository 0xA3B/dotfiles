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

if status is-interactive
    set -q dotenv_enable; or set -g dotenv_enable yes
    set -q dotenv_announce; or set -g dotenv_announce yes
    set -q dotenv_filename; or set -g dotenv_filename ".env"
end

# State tracking
set -g _dotenv_stack # Active .env file paths (root to deepest)
set -g _dotenv_file_vars # "filepath:varname" for each var we set
set -g _dotenv_saved_vals # Parallel array: saved value or "__DOTENV_UNSET__"
set -g _dotenv_initialized 0

function _dotenv_parse --description "Parse .env file, output KEY=VALUE or !KEY (unset)"
    set -l file $argv[1]
    test -f "$file"; or return

    while read -l line
        # Skip empty lines
        string match -qr '^\s*$' -- "$line"; and continue

        # Check for unset directive: # unset: VAR
        set -l unset_match (string match -r '^\s*#\s*unset:\s*([A-Za-z_][A-Za-z0-9_]*)\s*$' -- "$line")
        if test (count $unset_match) -ge 2
            echo "!$unset_match[2]"
            continue
        end

        # Skip other comments
        string match -qr '^\s*#' -- "$line"; and continue

        # Match KEY=VALUE pattern
        set -l match (string match -r '^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$' -- "$line")
        test (count $match) -ge 3; or continue

        set -l key $match[2]
        set -l val $match[3]

        # Remove surrounding quotes if present
        set val (string replace -r '^["\'](.*)["\']$' '$1' -- "$val")

        echo "$key=$val"
    end <"$file"
end

function _dotenv_load --description "Load a .env file, tracking original values"
    set -l file $argv[1]
    test -f "$file"; or return 1

    for line in (_dotenv_parse "$file")
        # Check for unset directive (!KEY)
        if string match -q '!*' -- "$line"
            set -l key (string sub -s 2 -- "$line")

            # Save current value before unsetting
            set -a _dotenv_file_vars "$file:$key"
            if set -q $key
                set -a _dotenv_saved_vals "$$key"
            else
                set -a _dotenv_saved_vals __DOTENV_UNSET__
            end

            # Unset the variable
            set -e $key
        else
            # Normal KEY=VALUE assignment
            set -l parts (string split -m1 '=' -- "$line")
            set -l key $parts[1]
            set -l val $parts[2]

            # Save current value before overwriting
            set -a _dotenv_file_vars "$file:$key"
            if set -q $key
                set -a _dotenv_saved_vals "$$key"
            else
                set -a _dotenv_saved_vals __DOTENV_UNSET__
            end

            # Set new value
            set -gx $key "$val"
        end
    end

    set -a _dotenv_stack "$file"
end

function _dotenv_unload --description "Unload a .env file, restoring original values"
    set -l file $argv[1]

    # Find and restore all vars from this file (reverse order for proper restoration)
    set -l indices_to_remove
    for i in (seq (count $_dotenv_file_vars) -1 1)
        set -l entry $_dotenv_file_vars[$i]
        if string match -q "$file:*" -- "$entry"
            set -l key (string replace "$file:" '' -- "$entry")
            set -l saved $_dotenv_saved_vals[$i]

            if test "$saved" = __DOTENV_UNSET__
                set -e $key
            else
                set -gx $key "$saved"
            end

            set -a indices_to_remove $i
        end
    end

    # Remove entries from tracking arrays (reverse order keeps indices valid)
    for i in $indices_to_remove
        set -e _dotenv_file_vars[$i]
        set -e _dotenv_saved_vals[$i]
    end

    # Remove from stack
    set -l new_stack
    for f in $_dotenv_stack
        test "$f" != "$file"; and set -a new_stack "$f"
    end
    set -g _dotenv_stack $new_stack
end

function _dotenv_get_target_stack --description "Get .env files that should be active for pwd"
    set -l result
    set -l dir (pwd)

    while test "$dir" != /
        set -l envfile "$dir/$dotenv_filename"
        if test -f "$envfile"
            set -p result "$envfile" # Prepend to get root-to-leaf order
        end
        set dir (dirname "$dir")
    end

    printf '%s\n' $result
end

function _dotenv_apply
    test "$dotenv_enable" != yes; and return
    not status is-interactive; and return

    set -l target (_dotenv_get_target_stack)

    # Find common prefix length between current stack and target
    set -l common 0
    set -l max_common (math "min("(count $_dotenv_stack)","(count $target)")")
    for i in (seq 1 $max_common)
        if test "$_dotenv_stack[$i]" = "$target[$i]"
            set common $i
        else
            break
        end
    end

    # Unload files no longer in target (deepest first)
    if test (count $_dotenv_stack) -gt $common
        for i in (seq (count $_dotenv_stack) -1 (math "$common + 1"))
            set -l file $_dotenv_stack[$i]
            if test "$dotenv_announce" = yes
                echo "Unloaded $file"
            end
            _dotenv_unload "$file"
        end
    end

    # Load new files in target (shallowest first)
    if test (count $target) -gt $common
        for i in (seq (math "$common + 1") (count $target))
            set -l file $target[$i]
            test -f "$file"; or continue
            if test "$dotenv_announce" = yes
                echo "Loaded $file"
            end
            _dotenv_load "$file"
        end
    end
end

function _dotenv_on_pwd --on-variable PWD --description "Auto-load .env on directory change"
    _dotenv_apply
end

function _dotenv_on_init --on-event fish_prompt --description "Auto-load .env on shell init"
    if test "$_dotenv_initialized" != 1
        set -g _dotenv_initialized 1
        _dotenv_apply
    end
end
