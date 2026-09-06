@AGENTS.md

## Claude Code shell environment

- The Bash tool runs in a snapshot of the user's interactive shell taken at session start, so mise
  is already activated and `mise exec --` is not needed. A `mise.toml` change to `[tools]` or
  `[env]` reaches the Bash tool only after a new session starts.
