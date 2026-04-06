typeset -U path fpath

_source_zsh_globbed_files() {
  local dir="$1"
  local file

  [[ -d $dir ]] || return 0

  for file in "$dir"/*.zsh(N); do
    source "$file"
  done
}

ZSH_CONFIG_DIR="${ZSH_CONFIG_DIR:-$HOME/.config/zsh}"
ZSH_WORK_ROOT="${ZSH_WORK_ROOT:-$ZSH_CONFIG_DIR/work}"

##############
## Homebrew ##
##############

brewbin="/opt/homebrew/bin/brew"
if [[ -f $brewbin ]]; then
  eval "$("$brewbin" shellenv)"

  export HOMEBREW_NO_AUTO_UPDATE=1
  export HOMEBREW_NO_ANALYTICS=1
  export HOMEBREW_NO_ENV_HINTS=1

  gnubin="$HOMEBREW_PREFIX/opt/coreutils/libexec/gnubin"
  if [[ -d $gnubin ]]; then
    path=("$gnubin" $path)
  fi
fi

##############
## ENV Init ##
##############

# Set default editors while preserving any inherited values
if [[ -z ${EDITOR+x} ]]; then
  export EDITOR="vim"
  command -v nvim >/dev/null 2>&1 && export EDITOR="nvim"
fi

if [[ -z ${VISUAL+x} ]]; then
  export VISUAL="$EDITOR"
  command -v code >/dev/null 2>&1 && export VISUAL="code --wait"
fi

# Personal dotfiles location for scripts and configs
export DOTFILES_HOME="$HOME/.dotfiles"

# Add Go binaries to PATH if Go is installed and GOBIN is configured
if command -v go >/dev/null 2>&1; then
  gobin="$(go env GOBIN)"
  if [[ -n $gobin && -d $gobin ]]; then
    path+=("$gobin")
  fi
fi


############
## Python ##
############

case "$(uname)" in
  Darwin)
    export PYTHON_CONFIGURE_OPTS="--enable-framework --enable-optimizations --with-lto"
    export PYTHON_CFLAGS="-march=native -mtune=native"
    ;;
  *)
    export PYTHON_CONFIGURE_OPTS="--enable-shared"
    ;;
esac

# uv installs tools to ~/.local/bin
if command -v uv >/dev/null 2>&1; then
  path=("$HOME/.local/bin" $path)
fi


#############
## Scripts ##
#############

_source_zsh_globbed_files "$ZSH_CONFIG_DIR/functions"
_source_zsh_globbed_files "$ZSH_CONFIG_DIR/conf.d"


#################
## Interactive ##
#################

if [[ -o interactive ]]; then
  zsh_completions_dir="$ZSH_CONFIG_DIR/completions"
  [[ -d $zsh_completions_dir ]] && fpath=("$zsh_completions_dir" $fpath)

  autoload -Uz compinit
  mkdir -p "$HOME/.local/share/zsh"
  compinit -i -d "$HOME/.local/share/zsh/.zcompdump-${ZSH_VERSION}"

  #-----------#
  # LS_COLORS #
  #-----------#
  if command -v vivid >/dev/null 2>&1; then
    export LS_COLORS="$(vivid generate catppuccin-mocha)"
    export EZA_COLORS="$LS_COLORS"
  fi

  #-----#
  # eza #
  #-----#
  if command -v eza >/dev/null 2>&1; then
    export EZA_GRID_ROWS=10
    ls() {
      command eza -Ghl --classify=auto --color=auto --icons=auto --group-directories-first --git --no-user "$@"
    }
    la() { ls -a "$@"; }
    lt() { ls -T -L 3 "$@"; }
    lat() { ls -aT -L 3 "$@"; }
    lart() { ls -a -s modified --reverse "$@"; }
    lsl() { command eza -l --no-permissions --no-filesize --no-user --no-time "$@"; }
  else
    ls() { command ls -lhF --color=auto "$@"; }
    la() { ls -a "$@"; }
    lart() { ls -art "$@"; }
  fi

  #---------#
  # zoxide  #
  #---------#
  if command -v zoxide >/dev/null 2>&1; then
    export _ZO_EXCLUDE_DIRS="/tmp:/private/tmp:/Volumes:$HOME/Library"
    eval "$(zoxide init zsh --cmd cd)"
  fi

  #-----#
  # bat #
  #-----#
  if command -v bat >/dev/null 2>&1; then
    export BAT_THEME="Catppuccin Mocha"
    export MANPAGER="sh -c 'col -bx | bat -l man -p'"
    alias cat="bat --paging=never"
  fi

  #-----#
  # fzf #
  #-----#
  if command -v fzf >/dev/null 2>&1; then
    fzf_opts="--height=40% --layout=reverse --border"
    if command -v bat >/dev/null 2>&1 && command -v eza >/dev/null 2>&1; then
      fzf_opts+=" --preview='test -d {} && eza -la --color=always --icons=auto {} || bat --color=always --style=numbers --line-range=:500 {}'"
    fi

    if command -v fd >/dev/null 2>&1; then
      export FZF_DEFAULT_COMMAND="fd --type f --hidden --follow --exclude .git"
    fi

    export FZF_DEFAULT_OPTS="$fzf_opts"

    if [[ -t 0 && -t 1 ]]; then
      if [[ -f "$HOME/.fzf.zsh" ]]; then
        source "$HOME/.fzf.zsh"
      else
        if fzf --zsh >/dev/null 2>&1; then
          source <(fzf --zsh)
        fi
      fi
    fi
  fi


  #------#
  # glow #
  #------#

  # Terminal markdown renderer
  if command -v glow >/dev/null 2>&1; then
    export GLOW_STYLE="$HOME/.config/glow/themes/catppuccin-mocha.json"
  fi

  #---------------#
  # Abbreviations #
  #---------------#
  alias c="clear"
  alias e="exit"

  # git
  alias gs="git status"
  alias gp="git push"

  # Quick config file access
  alias fish-config="$EDITOR $HOME/.config/fish/config.fish"
  alias nvim-config="$EDITOR $HOME/.config/nvim/init.lua"
  alias tmux-config="$EDITOR $HOME/.config/tmux/tmux.conf"

  # tmux session management
  alias tl="tmux list-sessions"
  alias tn="tmux new -t"
  alias ta="tmux a -t"
  alias td="tmux kill-session -t"

  # Misc
  alias fr="zsh-reload"
  alias fs="zsh-restart"
  alias cc="claude"
  alias ccl="cc-login"
  alias cce="cc-env"

  #---------#
  # Aliases #
  #---------#

  # These ensure pip/virtualenv use the correct Python.
  alias pip="python3 -m pip"
  alias virtualenv="python3 -m virtualenv"
  alias mkvenv="python3 -m virtualenv .venv"
  alias activate="source .venv/bin/activate"

  #----------#
  # Starship #
  #----------#

  # Cross-shell prompt with git info, language versions, etc.
  if command -v starship >/dev/null 2>&1; then
    eval "$(starship init zsh)"
  fi
fi
