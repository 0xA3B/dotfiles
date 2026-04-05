function export --description 'Bash-like export helper for fish'
    # Generated with GPT-5-Codex
    if not set -q argv[1]
        command env | sort
        return 0
    end

    set -l exit_code 0
    for arg in $argv
        if string match -q '*=*' -- $arg
            set -l parts (string split -m1 '=' -- $arg)
            set -l name $parts[1]

            if test -z "$name"
                printf 'export: `%s`: not a valid identifier\n' $arg >&2
                set exit_code 1
                continue
            end

            if not string match -rq '^[A-Za-z_][A-Za-z0-9_]*$' -- $name
                printf 'export: `%s`: not a valid identifier\n' $arg >&2
                set exit_code 1
                continue
            end

            set -l value ''
            if test (count $parts) -gt 1
                set value $parts[2]
            end

            set -gx -- $name "$value"
            continue
        end

        set -l name $arg
        if test -z "$name"
            printf 'export: `%s`: not a valid identifier\n' $arg >&2
            set exit_code 1
            continue
        end

        if not string match -rq '^[A-Za-z_][A-Za-z0-9_]*$' -- $name
            printf 'export: `%s`: not a valid identifier\n' $arg >&2
            set exit_code 1
            continue
        end

        if set -q $name
            set -gx -- $name $$name
        else
            # Match bash behavior: create an exported variable with an empty value.
            set -gx -- $name ''
        end
    end

    return $exit_code
end
