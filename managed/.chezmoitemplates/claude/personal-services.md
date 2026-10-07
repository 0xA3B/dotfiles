# Personal services

## GitHub

- Use the `0xA3B` account for GitHub operations. Use each repository's configured remote URL as-is,
  and change the active `gh` account only when the user asks.

## Notion

- Prefer Notion MCP for page and database work; use `ntn` for scripts, structured API requests, and
  capabilities missing from MCP.
- Before Notion writes, verify the workspace ID and destination page or database, not the workspace
  display name alone.
- Use `ntn whoami` or `ntn doctor` for authentication checks. Keep token-printing commands such as
  `ntn auth token` out of diagnostics.

## Personal project credentials

- The `op` CLI uses a service account token with access only to the `Automation` vault. Treat
  credentials and API keys in that vault as approved for agent use and automation scripts.
- If a command needs a 1Password credential, use a secret reference URI such as
  `op://Automation/...` and run the command with `op run`.
