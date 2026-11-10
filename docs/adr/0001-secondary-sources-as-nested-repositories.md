# Secondary sources are nested repositories applied by separate chezmoi invocations

Some machines need dotfiles that must stay out of this public repository, and chezmoi applies only
one source directory per invocation. Each secondary source is a separate Git repository checked out
at `managed-<name>/` in this repository, and this repository ignores `/managed-*/`. The
[`dotfiles`](../../managed/dot_local/bin/executable_dotfiles) wrapper applies the primary source,
`managed/`, and then each secondary source with its own invocation:
`chezmoi --source managed-<name> --persistent-state ~/.config/chezmoi/chezmoistate-<name>.boltdb`.
Every invocation reads the shared chezmoi config. Nesting keeps the shared tooling one directory up,
so a secondary source's modify scripts resolve `tools/` through `CHEZMOI_SOURCE_DIR/..`, and its
targets land in `$HOME` like the primary source's.

## Considered options

- **One state file for every source.** The state records the config template's hash, so each
  secondary run warns that the template changed. A chezmoi run started from another run's script
  also times out waiting for the state lock that the outer run holds.
- **chezmoi hooks or a `git-repo` external in the primary source.** A hook runs during dry runs too,
  and a failing external, such as a clone attempted off the work network, aborts the primary apply.
- **A sibling checkout with symlinked tooling.** Git refuses a symlinked `.gitignore`, and pnpm
  reinstalls dependencies through the symlinked workspace.

## Consequences

- Nesting puts private content under this repository's root. Git ignores `/managed-*/`, so the
  checkout stays out of this repository's commits, but a tool that uses this repository as its
  working directory, such as a coding agent, can read the checkout unless its permissions deny
  `managed-<name>/`.
- Sources must write disjoint targets. A target that two sources write would hold private content at
  a path outside `managed-<name>/`, which a tool denied the checkout may still read. Secondary
  content reaches shared tools through drop-in directories, `includeIf`, and environment variables.
  Revisit this rule when a setting has none of those routes.
- A secondary source must not ship a chezmoi config template (`.chezmoi.<format>.tmpl`), which
  `chezmoi init` would render over the shared config. The wrapper refuses to run against one.
- A secondary source cannot lint or run CI on its own, because its tooling lives in this repository.
  A maintainer runs this repository's format and lint tasks from inside the source and installs only
  its commit hooks there, because the pre-push hook runs this repository's test suite, which a
  secondary source's push never changes. The [README](../../README.md#work-in-a-secondary-source)
  gives the commands.
- Plain `chezmoi` applies only the primary source. `dotfiles` applies the primary source first, then
  secondary sources alphabetically.
- `chezmoi purge` deletes the config directory, which holds the shared config and every source's
  state, and the source directory, so the wrapper refuses to pass `purge` through.
