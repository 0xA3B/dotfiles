# Test Conventions

## Scope

These instructions apply when writing or reviewing tests under `tests`.

## Testing Style

- Test public helper APIs rather than private functions.
- Prefer direct string input and output assertions for merge behavior.
- Use temporary files and environment fixtures only for file-backed behavior such as
  `CHEZMOI_SOURCE_DIR` resolution.
- Cover idempotency, invalid managed overlays, public/private path boundaries, and diagnostics for
  new helper behavior.
