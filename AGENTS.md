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
- Keep work-only, secret, and machine-local values outside tracked files. Template and ignore logic
  may control whether public-safe source content is applied, but they do not make tracked private
  content safe.
- In tracked Markdown and other public-facing repo content, do not use absolute local filesystem
  paths such as `/Users/...`.
- Use file-relative targets for Markdown links. Use repository-root-relative paths in prose and code
  spans, except for unambiguous same-directory filenames.

## Project conventions

- Use Conventional Commits.
- Use mise for runtime management and project tasks.
- `package.json#devEngines.runtime` and `.python-version` are the canonical runtime versions;
  `mise.toml` is the canonical pnpm version.
- When a command relies on a runtime tool managed by mise, run it with `mise exec --` in
  non-interactive shells.
- Use the `mise.toml` task surface (`mise run`) for validation and formatting instead of raw tool
  commands.
- Use `mise run check` as the default full local gate.
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

- Prefer built-in or standard-library capabilities when they fit the problem; otherwise prefer
  widely adopted, well-maintained ecosystem-standard packages over custom implementations.
- Treat `pyproject.toml` and `package.json` as compatibility manifests. Bound each direct dependency
  below its next major release, such as `<22`, and a 0.x dependency below 1, such as `<1`, except
  the modify-script runtime dependencies in the next rule.
- Mirror every PEP 723 dependency of a modify script in `pyproject.toml`'s `[project].dependencies`
  with the same bound, so CI tests a version from the range that machines resolve. Modify scripts
  resolve these dependencies on every machine without a lockfile, so bound a 0.x one below its next
  minor release, such as `<0.16`.
- Write an upper bound with only the version segments that define its boundary, such as `<1` or
  `<0.16`, not `<1.0.0`. Renovate keeps a bound's precision when it moves the bound, so `<1.0.0` in
  `pyproject.toml` becomes `<1.0.1` rather than `<2`.
- Beyond those bounds, use lower bounds for required features or to exclude vulnerable older
  releases, tighter upper bounds for intentionally deferred incompatibilities, exclusions for
  known-bad releases, and exact pins only when no version range is acceptable. Use the least
  restrictive constraint that expresses the requirement, and remove it when the requirement ends.
- When a transitive dependency must be constrained, use the owning package manager's constraint or
  override mechanism. Do not declare it as a direct dependency solely to control its resolved
  version.
- Treat `mise.lock`, `uv.lock`, and `pnpm-lock.yaml` as the exact tested resolutions. Let Renovate
  perform routine lockfile refreshes; regenerate a lockfile locally when a requested dependency
  change requires a new resolution.
- Renovate automerges, once CI passes, every update that changes only a lockfile and every GitHub
  Actions and pre-commit update. A Renovate PR that rewrites a version in `package.json`,
  `pyproject.toml`, PEP 723 metadata, `mise.toml`, or `managed/dot_config/mise/config.toml` waits
  for review; read its release notes before merging it.
- Update Node.js and Python runtime majors manually. Renovate updates in-range runtime versions only
  through lockfile maintenance.
- Set `mise.toml` tools to `latest` and let CI catch breaking releases. To take in-range releases
  before Renovate's lockfile maintenance, run `mise lock --bump`.
- Write mise-read version ranges as prefixes such as `26`, not caret or comparison ranges such as
  `^26.12.1` or `>=26.12.1 <27`; mise ignores `mise.lock` for those ranges, and
  `MISE_LOCKED=1 mise install` fails. For a tool that `mise.lock` locks, Renovate and
  `mise lock --bump` resolve a prefix only within it, and Renovate never opens a PR to move it, so
  use a prefix there only for a runtime version. To defer a specific tool incompatibility, pin the
  tool to an exact version; Renovate holds each PR that moves the pin for review.
- Keep pnpm out of `package.json`. A `packageManager` or `devEngines.packageManager` field makes
  pnpm lock its own version in `pnpm-lock.yaml`, which then drifts from `mise.lock`.
- Pin each external in `managed/.chezmoiexternal.toml` to a release tag and its `checksum.sha256`.
  Renovate does not track these externals; review and update them manually during routine dependency
  maintenance, selecting only releases that meet the cooldown.
- Require a three-day cooldown before selecting releases from public registries and tool sources.
  Enforce it in every resolver and updater that can select those releases: Renovate, pnpm, mise, and
  uv.
- Bypass the cooldown only for an urgent security fix. Keep explicit exceptions package-specific in
  every applicable resolver or updater, and remove them once the release has aged out.

## Terminology

Use this section for durable domain terms that should guide future work in this repository. Add or
update entries when a term becomes stable during adversarial review, architecture review, or
implementation.

| Term                      | Definition                                                                                                                                                    | Aliases to Avoid           |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------- |
| **Managed overlay**       | A repo-owned sidecar file, usually named `*.managed.*`, that authoritatively manages selected keys or settings while preserving unrelated live configuration. | managed file, sidecar      |
| **Default overlay**       | A repo-owned sidecar file, usually named `*.default.*`, that supplies missing settings or an absent unstructured target without changing existing values.     | default file, fallback     |
| **Modify script**         | A chezmoi `modify_` script or modify template that transforms existing target-file content instead of replacing the whole file.                               | merge script, transform    |
| **Modify helper library** | Python helper code under `tools/chezmoi_modify` for use by PEP 723 modify scripts.                                                                            | helper lib, modify helpers |

Relationships:

- A **Modify script** applies one **Managed overlay** to its live target file.
- A **Modify script** may apply a **Default overlay** before a **Managed overlay**, so managed
  values win while existing live values win over defaults.
- A **Modify script** may import the **Modify helper library**.
