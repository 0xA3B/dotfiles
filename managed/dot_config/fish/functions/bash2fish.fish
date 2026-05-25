function bash2fish --description 'Translate basic bash export/unset statements to fish'
    # Generated with GPT-5-Codex
    # Supports bash-style environment output only:
    #   KEY=value;
    #   export ...
    #   unset ...
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

        # Drop inline comments that start outside quotes after whitespace.
        set trimmed (__bash2fish_strip_inline_comment $trimmed)
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

function __bash2fish_strip_inline_comment --description 'Strip bash-style inline comments while preserving quoted #'
    set -l text $argv[1]
    set -l length (string length -- "$text")
    set -l in_single 0
    set -l in_double 0
    set -l escaped 0
    set -l prev ''

    for i in (seq $length)
        set -l char (string sub -s $i -l 1 -- "$text")

        if test "$in_single" = 1
            if test "$char" = "'"
                set in_single 0
            end
        else if test "$in_double" = 1
            if test "$escaped" = 1
                set escaped 0
            else if test "$char" = "\\"
                set escaped 1
            else if test "$char" = '"'
                set in_double 0
            end
        else
            if test "$char" = "'"
                set in_single 1
            else if test "$char" = '"'
                set in_double 1
            else if test "$char" = '#'
                if string match -rq '\s' -- "$prev"
                    printf '%s\n' (string sub -s 1 -l (math "$i - 1") -- "$text")
                    return 0
                end
            end
        end

        set prev "$char"
    end

    printf '%s\n' "$text"
end
