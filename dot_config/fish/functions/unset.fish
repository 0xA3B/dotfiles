function unset --description 'Bash-like unset helper for fish'
    # Generated with GPT-5-Codex
    if not set -q argv[1]
        printf 'unset: not enough arguments\n' >&2
        return 1
    end

    set -l mode 'both'
    set -l names
    set -l args $argv

    while set -q args[1]
        set -l token $args[1]
        set args $args[2..-1]

        switch $token
            case '-f' '--function'
                if test $mode = 'variable'
                    printf 'unset: options `-f` and `-v` are mutually exclusive\n' >&2
                    return 2
                end
                set mode 'function'
            case '-v' '--variable'
                if test $mode = 'function'
                    printf 'unset: options `-f` and `-v` are mutually exclusive\n' >&2
                    return 2
                end
                set mode 'variable'
            case '--'
                set names $args
                set args
                break
            case '-*'
                printf 'unset: invalid option `%s`\n' $token >&2
                return 2
            case '*'
                set names $names $token $args
                break
        end
    end

    if not set -q names[1]
        printf 'unset: not enough arguments\n' >&2
        return 1
    end

    set -l exit_code 0
    for name in $names
        if not string match -rq '^[A-Za-z_][A-Za-z0-9_]*$' -- $name
            printf 'unset: `%s`: not a valid identifier\n' $name >&2
            set exit_code 1
            continue
        end

        if test $mode = 'variable'
            or test $mode = 'both'
            if set -q $name
                set -e -- $name
            end
        end

        if test $mode = 'function'
            or test $mode = 'both'
            if functions -q $name
                functions -e $name
            end
        end
    end

    return $exit_code
end
