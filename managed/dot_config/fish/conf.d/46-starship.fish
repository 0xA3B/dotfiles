# Agent/test shells may be interactive while using TERM=dumb; starship errors
# there because the terminal advertises no prompt-rendering capabilities.
if status is-interactive; and test "$TERM" != dumb; and command -q starship
    starship init fish | source
end
