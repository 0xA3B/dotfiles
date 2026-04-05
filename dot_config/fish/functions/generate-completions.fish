function __generate_completions_registry
    # Registries live in autoloaded helper functions:
    #   - __generate_completions_base_registry
    #   - __generate_completions_work_registry (optional)
    __generate_completions_base_registry

    if functions -q __generate_completions_work_registry
        __generate_completions_work_registry
    end
end

function __generate_completions_supported_commands
    for entry in (__generate_completions_registry)
        set -l fields (string split \t -- $entry)
        printf '%s\n' $fields[1]
    end
end

function __generate_completions_registry_entry --argument-names name
    for entry in (__generate_completions_registry)
        set -l fields (string split \t -- $entry)
        if test "$fields[1]" = "$name"
            printf '%s\n' $entry
            return 0
        end
    end

    return 1
end

function __generate_completions_write --argument-names name target
    set -l generator $argv[3..-1]

    if test (count $generator) -eq 0
        echo "No completion generator configured for $name" >&2
        return 1
    end

    if not command -q $generator[1]
        echo "$name not found in PATH, skipping completions generation" >&2
        return 1
    end

    set -l completions_dir (path dirname $target)
    command mkdir -p $completions_dir
    or begin
        echo "Failed to create completions directory: $completions_dir" >&2
        return 1
    end

    set -l tmpfile (command mktemp "$target.tmp.XXXXXX")
    or begin
        echo "Failed to create temporary file for $name completions" >&2
        return 1
    end

    if command $generator >$tmpfile
        if test -s $tmpfile
            command mv -f $tmpfile $target
            or begin
                command rm -f $tmpfile
                echo "Failed to install completions for $name" >&2
                return 1
            end

            echo "Generated completions for $name"
            return 0
        end

        echo "Completion generator for $name produced empty output" >&2
    else
        echo "Failed to generate completions for $name" >&2
    end

    command rm -f $tmpfile
    return 1
end

function __generate_completions_one --argument-names name
    set -l entry (__generate_completions_registry_entry $name)
    or begin
        echo "Unsupported command '$name'" >&2
        return 1
    end

    set -l fields (string split \t -- $entry)
    set -l generator (string split ' ' -- $fields[3])

    __generate_completions_write $fields[1] $fields[2] $generator
end

function generate-completions --description "(Re)Generate fish completions in 'completions/' for supported commands"
    argparse h/help -- $argv
    or return

    set -l supported (__generate_completions_supported_commands)

    if set -q _flag_help
        echo "Usage: generate-completions [COMMAND ...]"
        echo
        echo "Regenerate fish completions for supported commands."
        echo "When no commands are provided, regenerate all supported completions."
        echo
        echo "Supported commands: "(string join ", " $supported)
        return 0
    end

    set -l requested $argv
    if test (count $requested) -eq 0
        set requested $supported
    end

    set -l unique_requested
    for name in $requested
        if not contains -- $name $unique_requested
            set -a unique_requested $name
        end
    end

    set -l status_code 0
    for name in $unique_requested
        if not contains -- $name $supported
            echo "Unsupported command '$name'. Supported commands: "(string join ", " $supported) >&2
            set status_code 1
            continue
        end

        __generate_completions_one $name
        or set status_code 1
    end

    return $status_code
end
