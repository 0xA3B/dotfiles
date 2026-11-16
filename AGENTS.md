# Project instructions

## Purpose

This repository maintains a public-safe, reproducible baseline for personal machine setup with
chezmoi. Preserve these outcomes:

- Managed dotfiles apply cleanly from `managed/` with `chezmoi apply`.
- Work-only, private, secret, and machine-local state stays out of tracked public files.
- Baseline shell, editor, runtime, package-manager, and bootstrap behavior stays consistent across
  machines while leaving room for local overlays.
- Repository tooling and modify helpers remain small, testable, and focused on safely managing
  selected configuration state.

## Repository model

- This repository is a `chezmoi` source repository.
- `.chezmoiroot` points chezmoi at `managed/`. Files there may materialize directly, transform
  existing targets, trigger actions, or remain source-only through `.chezmoiignore.tmpl`.
- Treat the applicable source state under `managed/` as authoritative for committed configuration.
- Inspect live files under `$HOME` only when diagnosing local drift or machine-specific behavior.
- Keep local working artifacts under `.local/`, not tracked project state.

## Public and private boundaries

- This repository is intended to remain public-safe.
- Do not add private work endpoints, internal package indexes, credentials, tokens, or
  employer-specific configuration to tracked files.
- Keep work-only, secret, and machine-local values outside tracked files; put content private to a
  **Secondary source** in that source's own repository. Template and ignore logic may control
  whether public-safe source content is applied, but they do not make tracked private content safe.
- Write each target from exactly one source. Before adding a `managed/` file, check that no
  **Secondary source** writes its target; route secondary content into shared tools through drop-in
  directories, `includeIf`, or environment variables instead.
- Before changing how `dotfiles` applies secondary sources or the `managed-*` layout, read
  [ADR 0001](docs/adr/0001-secondary-sources-as-nested-repositories.md).
- In tracked Markdown and other public-facing repo content, do not use absolute local filesystem
  paths such as `/Users/...`.
- Use file-relative targets for Markdown links. Use repository-root-relative paths in prose and code
  spans, except for unambiguous same-directory filenames.

## Project conventions

- Use Conventional Commits.
- Use mise for runtime management and project tasks.
- When a command relies on a runtime tool managed by mise, run it with `mise exec --` in
  non-interactive shells.
- Use the `mise.toml` task surface (`mise run`) for validation and formatting instead of raw tool
  commands.
- Use `mise run check` as the default full local gate.
- Configure shfmt through `.editorconfig` only. shfmt ignores `.editorconfig` when it receives any
  parser or printer flag, such as `-i`, `-ci`, or `-s`, so pass none.
- Use the smallest relevant targeted task when narrowing validation.
- Keep `check`-suffixed tasks non-mutating.
- Reserve the pre-commit `manual` stage for hooks that do not run at commit time; CI covers them via
  `mise run format:hygiene`.
- When adding or renaming a source file whose final suffix does not identify its language, including
  extensionless files and `.tmpl` sources, add an explicit `files.associations` entry in
  `.vscode/settings.json`. In the same change, review `.editorconfig` and add the narrowest matching
  section when the applicable rules do not supply the formatter dialect or indentation.
- Keep repository tooling outside `managed/` unless it must be part of the chezmoi source state.
- Treat `AGENTS.md` as canonical agent guidance; sibling `CLAUDE.md` files must import `@AGENTS.md`
  and may add Claude-specific guidance only when it doesn't belong in `AGENTS.md`.

## Dependency policy

Apply `engineering:dependency-policy`, with these additions:

- Renovate is the updater. Once CI passes, it automerges every update that changes only a lockfile
  and every GitHub Actions and pre-commit update. It holds for review every update that rewrites a
  version in `package.json`, `pyproject.toml`, PEP 723 metadata, `mise.toml`, or
  `managed/dot_config/mise/config.toml`.
- Update Node.js majors and Python feature releases, such as 3.14 to 3.15, by hand, and keep their
  Renovate updates disabled in `.github/renovate.jsonc`. Renovate takes their in-range releases only
  through weekly lockfile maintenance.
- In `managed/dot_config/mise/config.toml`, the machine-wide mise config, which has no lockfile and
  which CI never installs, write runtime versions as prefixes such as `go = "1.27"`, which Renovate
  moves, and other tools as `latest`.
- Pin each external in `managed/.chezmoiexternal.toml` to a release tag and its `checksum.sha256`;
  Renovate does not track them.

## Ubiquitous language

Use these terms, with these meanings, in conversation, code, tests, and documents. When a request,
or code the task changes, uses an alias to avoid or uses a term with a different meaning, say so
before you continue. Change this section through `engineering:ubiquitous-language`.

- **Managed overlay**: A repo-owned file, usually named `*.managed.*`, that authoritatively sets
  selected keys or settings in a live target while preserving unrelated live configuration. Aliases
  to avoid: managed file, sidecar.
- **Default overlay**: A repo-owned file, usually named `*.default.*`, that supplies missing
  settings or an absent unstructured target without changing existing values. Aliases to avoid:
  default file, fallback, sidecar.
- **Modify script**: A chezmoi `modify_` script or modify template that transforms existing
  target-file content instead of replacing the whole file. Aliases to avoid: merge script,
  transform.
- **Primary source**: The chezmoi source state in this repository's `managed/` directory, applied by
  plain `chezmoi`. Aliases to avoid: personal source.
- **Secondary source**: A separate Git repository checked out at `managed-<name>/` in this
  repository and applied by the `dotfiles` wrapper. Aliases to avoid: work repo (for the general
  concept), overlay repo, sub-source.

Relationships:

- A **Modify script** applies one **Managed overlay** to its live target file.
- A **Modify script** may apply a **Default overlay** before a **Managed overlay**, so managed
  values win while existing live values win over defaults.
- `dotfiles` applies the **Primary source** first, then each **Secondary source** alphabetically,
  each with its own chezmoi state
  ([ADR 0001](docs/adr/0001-secondary-sources-as-nested-repositories.md)).
