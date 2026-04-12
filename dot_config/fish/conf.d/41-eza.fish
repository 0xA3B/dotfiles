if status is-interactive
    if command -q eza
        set -gx EZA_GRID_ROWS 10

        function ls --wraps=eza --description "List files"
            command eza -Ghl --classify=auto --color=auto --icons=auto --group-directories-first --git --no-user $argv
        end

        function la --wraps=eza --description "List all files"
            ls -a $argv
        end

        function lt --wraps=eza --description "Tree view (3 levels)"
            ls -T -L 3 $argv
        end

        function lat --wraps=eza --description "Tree view all (3 levels)"
            ls -aT -L 3 $argv
        end

        function lart --wraps=eza --description "List all by modified time"
            ls -a -s modified --reverse $argv
        end

        function lsl --wraps=eza --description "List only filenames (no details)"
            command eza -l --no-permissions --no-filesize --no-user --no-time $argv
        end
    else
        function ls --wraps=ls --description "List files"
            command ls -lhF --color=auto $argv
        end

        function la --wraps=ls --description "List all files"
            ls -a $argv
        end

        function lart --wraps=ls --description "List all by modified time"
            ls -art $argv
        end
    end
end
