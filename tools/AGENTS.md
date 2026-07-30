# Helper Library Instructions

## Scope

These instructions apply when developing code under `tools`.

## Implementation Conventions

- Keep modify helper code in `tools/chezmoi_modify` with tests in `tests`.
- Keep `tools/chezmoi_modify` import-only; do not add a CLI entrypoint unless explicitly requested.
- Expose public merge helpers as text-in/text-out APIs returning `MergeResult`.
- Return non-fatal diagnostics in `MergeResult.diagnostics`.
- Raise `ChezmoiModifyError` for invalid managed overlays, invalid structured live input, missing
  source files, or unsafe source paths.
- Prefer parser-backed implementations for structured formats such as TOML, JSON, and YAML.
- Keep format-specific behavior in format-specific modules rather than adding tool-specific logic to
  generic helpers.
- Keep helper functions focused on text transforms; chezmoi remains responsible for file metadata.
