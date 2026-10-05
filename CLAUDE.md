@AGENTS.md

## Claude Code shell environment

- Before each Bash command, a SessionStart hook applies mise's environment for the command's
  starting directory, so run mise-managed tools directly. After a `cd` inside the same command line,
  run tools with `mise exec --`. Changes to shell configuration or the launching environment reach
  the Bash tool only in a new session.
