function source-bash --description 'Source bash-style environment output from stdin'
    # Supported input patterns:
    #   KEY=value;
    #   export ...
    #   unset ...
    bash2fish | source
    set -l statuses $pipestatus

    if test $statuses[1] -ne 0
        return $statuses[1]
    end

    return $statuses[2]
end
