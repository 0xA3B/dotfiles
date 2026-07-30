# Test Conventions

## Scope

These instructions apply when writing or reviewing tests under `tests`.

## Testing Style

- Test public helper and command behavior rather than private implementation details.
- Prefer direct string input and output assertions for merge behavior.
- Use temporary files and environment fixtures only for file-backed behavior such as
  `CHEZMOI_SOURCE_DIR` resolution.
- Cover idempotency, invalid managed overlays, source-root containment, and diagnostics for new
  helper behavior. Containment cases include absolute paths, parent traversal, and symlinks that
  escape the source root.
