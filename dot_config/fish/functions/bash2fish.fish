function bash2fish --description 'Translate basic bash export/unset statements to fish'
    # Generated with GPT-5-Codex
    # This functions also relies on export.fish and unset.fish.
    set -l lineno 0

    while read -l line
        set lineno (math $lineno + 1)

        set -l trimmed (string trim -- $line)
        if test -z "$trimmed"
            continue
        end

        if string match -q '#*' -- $trimmed
            continue
        end

        # Drop inline comments that follow whitespace.
        set trimmed (string replace -r '\s#.*$' '' -- $trimmed)
        set trimmed (string trim -- $trimmed)
        if test -z "$trimmed"
            continue
        end

        # Remove any trailing semicolons.
        set trimmed (string replace -r '[;[:space:]]+$' '' -- $trimmed)
        set trimmed (string trim -- $trimmed)
        if test -z "$trimmed"
            continue
        end

        if string match -rq '^export(\s|$)' -- $trimmed
            printf '%s\n' $trimmed
            continue
        end

        if string match -rq '^unset(\s|$)' -- $trimmed
            printf '%s\n' $trimmed
            continue
        end

        if string match -rq '^[A-Za-z_][A-Za-z0-9_]*=' -- $trimmed
            set -l parts (string split -m1 '=' -- $trimmed)
            set -l name $parts[1]
            set -l value ''

            if test (count $parts) -gt 1
                set value (string trim -- $parts[2])
            end

            if string match -rq '^".*"$' -- $value
                set value (string replace -r '^"(.*)"$' '$1' -- $value)
            else if string match -rq "^'.*'\$" -- $value
                set value (string replace -r "^'(.*)'\$" '$1' -- $value)
            end

            set -l escaped (string escape --style=script -- $value)
            if test -z "$value"
                set escaped "''"
            end

            printf 'set -gx -- %s %s\n' $name $escaped
            continue
        end

        printf 'bash2fish: unsupported input on line %d: %s\n' $lineno $line >&2
        return 1
    end
end
