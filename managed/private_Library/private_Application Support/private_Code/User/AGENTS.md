# VS Code Settings Instructions

## Role

- This directory holds the managed VS Code user configuration applied through chezmoi.
- `settings.managed.jsonc.tmpl` is an authoritative overlay template rendered and merged into the
  live `settings.json` by the adjacent `modify_private_settings.json` script. It manages only the
  keys it contains and preserves unrelated live settings.
- `extensions.managed.txt` lists extensions installed by
  `managed/run_onchange_install-vscode-extensions.sh.tmpl`.

## Managed Settings Rules

- Keep managed settings portable and public-safe. Do not add work-only, secret, or machine-specific
  values (for example absolute user paths, internal endpoints, or account-bound tokens).
- Gate machine- or OS-specific settings behind chezmoi template logic rather than committing
  machine-specific defaults.
- When using chezmoi directives in `settings.managed.jsonc.tmpl`, do not let a `{{-` trim marker
  consume the newline after a comment line; it will glue the next key onto the comment and the JSONC
  parser will drop it. Prefer `{{- if ... }}` ... `{{- end }}` so rendered content stays on its own
  lines.
- `settings.managed.jsonc.tmpl` is excluded from JSONC formatting because the source contains
  template directives. Keep it hand-formatted and ensure the rendered output is valid JSONC.
- `modify_private_settings.json` is a Python PEP 723 script despite its target-derived suffix. Keep
  it valid Python, preserve its Python file-type marker, and exclude it from JSON checks and
  formatting.
