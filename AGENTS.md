# Project Instructions

## Purpose

This repository maintains a public-safe, reproducible baseline for personal machine setup with
chezmoi. Changes should preserve these outcomes:

- Managed dotfiles apply cleanly from `managed/` with `chezmoi apply`.
- Work-only, private, secret, and machine-local state stays out of tracked public files.
- Baseline shell, editor, runtime, package-manager, and bootstrap behavior stays consistent across
  machines while leaving room for local overlays.
- Repository tooling and modify helpers remain small, testable, and focused on safely managing
  selected configuration state.

## Repository Model

- This repository is a `chezmoi` source repository.
- `.chezmoiroot` points chezmoi at `managed/`. Files there may materialize directly, transform
  existing targets, trigger actions, or remain source-only through `.chezmoiignore.tmpl`.
- Treat the applicable source state under `managed/` as authoritative for committed configuration.
- Inspect live files under `$HOME` only when diagnosing local drift or machine-specific behavior.

## Public and Private Boundaries

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

## Glossary

- **Managed overlay:** a repo-owned sidecar file, usually named `*.managed.*`, that authoritatively
  manages selected keys or settings while preserving unrelated live configuration.
- **Modify script:** a chezmoi `modify_` script or modify template that transforms existing
  target-file content instead of replacing the whole file.
- **Modify helper library:** Python helper code under `tools/chezmoi_modify` for use by PEP 723
  modify scripts.

## Project Conventions

- Use mise for runtime management and project tasks.
- Use `mise exec --` in non-interactive shells when the command relies on a runtime tool managed by
  mise.
- Use the `mise.toml` task surface (`mise run`) for validation and formatting.
- Use `mise run check` as the default full local gate.
- Use the smallest relevant targeted task when narrowing validation.
- Tasks with the `check` suffix should be non-mutating.
- `format` tasks mutate by default and pair with `:check` variants; `lint` tasks are non-mutating by
  default and pair with `:fix` variants when the linter supports autofixes.
- Define each format and lint command once in the mise task surface; pre-commit hooks delegate to
  `mise run` and stay focused on fast checks and safe fixes for files participating in Git
  operations, plus the pre-push test gate.
- Reserve the pre-commit `manual` stage for hooks that do not run at commit time; CI covers them via
  `mise run format:hygiene`.
- Keep repository tooling outside `managed/` unless it must be part of the chezmoi source state.
- Keep README user-facing and lightweight.
- Keep AGENTS files agent-facing, lightweight, and focused on durable guidance. Avoid temporary
  notes or details that may go stale quickly.
- Treat `AGENTS.md` as canonical agent guidance; sibling `CLAUDE.md` files must import `@AGENTS.md`
  and may add Claude-specific guidance only when it doesn't belong in `AGENTS.md`.

## Commit Conventions

- Commits must follow
  [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/#specification).
- Include a `scope` when it meaningfully improves clarity.
- Partition changes into separate commits by type, scope, or rollback boundary when feasible.

## Dependency Policy

- Prefer built-in or standard-library capabilities when they fit the problem; otherwise prefer
  widely adopted, well-maintained ecosystem-standard packages over custom implementations.
- Treat `pyproject.toml` and `package.json` as compatibility manifests. Leave direct dependencies
  without version constraints by default; add constraints only for documented compatibility or
  security requirements.
- Use lower bounds for required features or vulnerable older releases, upper bounds for
  intentionally deferred incompatibilities, exclusions for known-bad releases, and exact pins only
  when no version range is acceptable.
- When a transitive dependency must be constrained, use the owning package manager's constraint or
  override mechanism. Do not declare it as a direct dependency solely to control its resolved
  version.
- Specify mise tools and PEP 723 script dependencies with compatibility ranges bounded at the
  intended breaking-change boundary.
- Treat `mise.lock`, `uv.lock`, and `pnpm-lock.yaml` as the exact tested resolutions. Let Renovate
  perform routine lockfile refreshes; regenerate them locally only when needed to restore a working
  resolution.
- Update major Node.js and Python runtime versions manually; Renovate must not update them.
- Require a three-day cooldown before adopting newly published releases from public package and tool
  sources. Enforce the cooldown consistently through Renovate, pnpm, mise, and uv configuration.
- Bypass the cooldown only when necessary to take an urgent security fix. Keep the exception
  package-specific in each relevant enforcing surface, and remove it once the release has aged out.
