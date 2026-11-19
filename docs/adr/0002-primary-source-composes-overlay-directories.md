# The primary source composes overlay directories across sources

Claude Code reads user settings from one `settings.json` per config directory and has no user-level
drop-in or include mechanism, so a secondary source cannot reach it through the routes that
[ADR 0001](0001-secondary-sources-as-nested-repositories.md) names. For such a target, the primary
source's modify script reads an overlay directory named after the target, such as
`settings.json.d/`, from the primary source and then from the same path in each active secondary
source (one whose URL in the `dotfiles_sources` config data is non-empty), composes the managed
overlays it finds in that order, and applies the result. Each target still has one writer, and the
merge logic stays in this repository, where tests and CI run.

## Considered options

- **A modify script in each source for the same target.** Every apply would write the file twice, a
  key that two sources set would flip between their values, and arrays such as permission rules
  would need per-entry ownership tracking so one source does not drop the other's entries.
- **The secondary source owns the target and reads the primary's overlays.** This follows ADR 0001's
  rule that each target has one writer, but puts the merge logic in a repository that cannot run
  tests or CI on its own, and needs a designated owner once a second secondary source writes the
  same target.
- **Claude Code's `managed-settings.d/`.** It applies machine-wide policy to every account on the
  machine and requires administrator rights, so it cannot give the work and personal accounts
  different settings.
- **The `--settings` flag from a launcher.** The `claude-personal` launcher could pass it, but the
  desktop app starts the work account without a launcher.

## Consequences

- Plain `chezmoi` reads active secondary sources for these targets, and the composed target holds
  secondary content outside `managed-<name>/`, as ADR 0001 warns.
- The modify script fails, instead of skipping, when an active secondary source has no checkout or
  no overlay directory, or an overlay cannot be read or rendered. A secondary source that supplies
  nothing for a target commits the directory with only a hidden placeholder, such as `.keep`.
  Managed arrays replace live arrays, so a skipped overlay would delete the entries it supplies,
  such as deny rules. A sandboxed session that cannot read a secondary source therefore cannot apply
  these targets.
- A later overlay can add array entries and override values, but cannot remove an earlier overlay's
  entries.
