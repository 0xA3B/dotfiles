# Initialize Homebrew environment and preferences early so later modules can
# rely on Homebrew-managed commands and paths.

set -l brewbin /opt/homebrew/bin/brew
if test -f $brewbin
    $brewbin shellenv fish | source

    set -gx HOMEBREW_NO_AUTO_UPDATE 1
    set -gx HOMEBREW_NO_ANALYTICS 1
    set -gx HOMEBREW_NO_ENV_HINTS 1

    set -l gnubin "$HOMEBREW_PREFIX/opt/coreutils/libexec/gnubin"
    if test -d $gnubin
        fish_add_path --prepend $gnubin
    end
end
