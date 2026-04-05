##########
## Fish ##
##########

# Custom key bindings for autosuggestions
# bind ctrl-i accept-autosuggest  # Accept entire suggestion (conflicts with tab)
# bind ctrl-n forward-word        # Accept next word of suggestion
bind ctrl-j forward-char          # Accept next character of suggestion

##############
## Homebrew ##
##############

set -l brewbin /opt/homebrew/bin/brew
if test -f $brewbin
    # Initialize Homebrew environment (PATH, MANPATH, etc.)
    $brewbin shellenv fish | source

    # Disable auto-update on every brew command (run `brew update` manually)
    set -gx HOMEBREW_NO_AUTO_UPDATE 1
    # Opt out of Homebrew analytics
    set -gx HOMEBREW_NO_ANALYTICS 1
    # Disable hints about environment variables
    set -gx HOMEBREW_NO_ENV_HINTS 1

    # Prefer GNU coreutils over macOS BSD versions (ls, cp, mv, etc.)
    # Provides consistent behavior with Linux and better features
    set -l gnubin "$HOMEBREW_PREFIX/opt/coreutils/libexec/gnubin"
    if test -d $gnubin
        fish_add_path --prepend $gnubin
    end
end


##############
## ENV Init ##
##############

# Set default editors while preserving any inherited values
if not set -q EDITOR
    set -gx EDITOR vim
    command -q nvim; and set -gx EDITOR nvim
end

if not set -q VISUAL
    set -gx VISUAL $EDITOR
    command -q code; and set -gx VISUAL code --wait
end

# Personal dotfiles location for scripts and configs
set -g DOTFILES_HOME "$HOME/.dotfiles"

# Add Go binaries to PATH if Go is installed and GOBIN is configured
if command -q go
    set -l gobin (go env GOBIN)
    if test -n "$gobin"; and test -d "$gobin"
        fish_add_path --append "$gobin"
    end
end


############
## Python ##
############

# Configure Python build options for pyenv/python-build
# These optimize Python compilation for the local machine
switch (uname)
    case Darwin
        # macOS: Build as framework (required for some GUI libs), with optimizations
        set -gx PYTHON_CONFIGURE_OPTS "--enable-framework --enable-optimizations --with-lto"
        # Native CPU optimizations for better performance
        set -gx PYTHON_CFLAGS "-march=native -mtune=native"
    case '*'
        # Linux/other: Build as shared library
        set -gx PYTHON_CONFIGURE_OPTS "--enable-shared"
end

# uv installs tools to ~/.local/bin
if command -q uv
    fish_add_path --prepend "$HOME/.local/bin"
end


#################
## Interactive ##
#################

if status is-interactive
    fish_config theme choose "Catppuccin Mocha"

    #-----------#
    # LS_COLORS #
    #-----------#

    # vivid generates LS_COLORS from theme definitions
    # This sets colors for ls, eza, and other tools that respect LS_COLORS
    if command -q vivid
        set -l colors (vivid generate catppuccin-mocha)
        set -gx LS_COLORS $colors
        set -gx EZA_COLORS $colors
    end

    #-----#
    # eza #
    #-----#

    # Modern replacement for ls with git integration and icons
    if command -q eza
        # EZA_GRID_ROWS: Switch from grid to long format when output exceeds this many rows
        # With both -G (grid) and -l (long), eza auto-selects based on output size
        set -gx EZA_GRID_ROWS 10

        # Base ls function with common options:
        #   -G  grid mode (for short listings)
        #   -l  long format (for detailed listings)
        #   --classify=auto      add indicators (/, *, @) to entries
        #   --icons=auto         show file type icons (requires nerd font)
        #   --group-directories-first  sort directories before files
        #   --git                show git status for each file
        #   --no-user            hide owner column (cleaner when you're the only user)
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
        # Fallback to standard ls if eza not installed
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

    #---------#
    # zoxide  #
    #---------#

    # Smart cd that learns your most-used directories
    # Use `cd` normally, it tracks frequency; `cd <partial>` jumps to best match
    if command -q zoxide
        # Don't track these directories (temp files, external drives, macOS system)
        set -gx _ZO_EXCLUDE_DIRS "/tmp:/private/tmp:/Volumes:$HOME/Library"
        # --cmd cd: Replace the built-in cd command (also provides cdi for interactive)
        zoxide init fish --cmd cd | source
    end

    #-----#
    # bat #
    #-----#

    # Modern replacement for cat with syntax highlighting
    if command -q bat
        # Use catppuccin theme (built into bat 0.24+)
        set -gx BAT_THEME "Catppuccin Mocha"
        # Colorized man pages using bat as the pager
        set -gx MANPAGER "sh -c 'col -bx | bat -l man -p'"
        # Replace cat with bat (--paging=never for cat-like behavior)
        # Use `command cat` for raw output when needed
        alias cat "bat --paging=never"
    end

    #-----#
    # fzf #
    #-----#

    # Fuzzy finder for files, history, and more
    # Key bindings: Ctrl+R (history), Ctrl+T (files), Alt+C (cd)
    if command -q fzf
        # Base options:
        #   --height=40%    use 40% of terminal (inline, not fullscreen)
        #   --layout=reverse  results top-to-bottom (more natural)
        #   --border        visual separation
        set -l fzf_opts "--height=40% --layout=reverse --border"

        # Enhanced preview pane: show file contents (bat) or directory listings (eza)
        if command -q bat; and command -q eza
            set -a fzf_opts "--preview='test -d {} && eza -la --color=always --icons=auto {} || bat --color=always --style=numbers --line-range=:500 {}'"
        end

        # Use fd for faster file finding (respects .gitignore)
        if command -q fd
            set -gx FZF_DEFAULT_COMMAND "fd --type f --hidden --follow --exclude .git"
        end

        set -gx FZF_DEFAULT_OPTS $fzf_opts
        # Enable fzf key bindings and completions
        fzf --fish | source
    end


    #------#
    # glow #
    #------#

    # Terminal markdown renderer
    if command -q glow
        # Catppuccin theme for glow: https://github.com/catppuccin/glamour
        set -gx GLOW_STYLE "$HOME/.config/glow/themes/catppuccin-mocha.json"
    end

    #---------------#
    # Abbreviations #
    #---------------#

    # Abbreviations expand inline when you press space/enter, so you see what runs.
    # Great for shortcuts you want to be transparent and editable.

    abbr -ag c clear
    abbr -ag e exit

    # git
    abbr -ag gs git status
    abbr -ag gp git push

    # Quick config file access
    abbr -ag fish-config "$EDITOR $HOME/.config/fish/config.fish"
    abbr -ag nvim-config "$EDITOR $HOME/.config/nvim/init.lua"
    abbr -ag tmux-config "$EDITOR $HOME/.config/tmux/tmux.conf"

    # tmux session management
    abbr -ag tl "tmux list-sessions"
    abbr -ag tn "tmux new -t"
    abbr -ag ta "tmux a -t"
    abbr -ag td "tmux kill-session -t"

    # Misc
    abbr -ag fr fish-reload
    abbr -ag fs fish-restart

    #---------#
    # Aliases #
    #---------#

    # These ensure pip/virtualenv use the correct Python.
    alias pip "python3 -m pip"
    alias virtualenv "python3 -m virtualenv"
    alias mkvenv "python3 -m virtualenv .venv"
    alias activate "source .venv/bin/activate.fish"

    #----------#
    # Starship #
    #----------#

    # Cross-shell prompt with git info, language versions, etc.
    if command -q starship
        starship init fish | source
    end
end
