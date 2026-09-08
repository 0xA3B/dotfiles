# Codex Rules Instructions

These instructions apply to the managed source rules under `managed/dot_codex/rules/`.

## Purpose

- These files define Codex execution-policy rules in Starlark using `prefix_rule(...)`.
- Use `prompt` to route command families that need contextual approval review, `allow` to run narrow
  commands that genuinely require sandbox-boundary access without review, and `forbidden` for
  deterministic hard denials. Auto-review handles eligible prompts only when it is configured and
  the approval policy remains interactive.
- Keep rules narrowly scoped, easy to review, and safe to publish.

## Rule Authoring

- Prefer exact prefixes for `allow` and `forbidden`. Use a command-family prefix for `prompt` when
  every matching invocation needs contextual review.
- Use grouped unions in `pattern` only when the grouped commands clearly share the same intent and
  risk profile.
- Use `prompt` for commands that should reach approval review even when the active sandbox or
  network profile could otherwise run them.
- Use `allow` only when every invocation matched by the prefix may run outside the sandbox without
  review. Add narrower overlapping `prompt` or `forbidden` rules for exceptional forms.
- Use `forbidden` for command prefixes that must never run. Put contextual denials, including unsafe
  flags that can appear at arbitrary argv positions, in the automatic-review policy.
- When decisions overlap, rely on Codex's `forbidden` over `prompt` over `allow` precedence and add
  examples that prove the intended result.
- Remember that `pattern` matches argv positions exactly. If a command should also work with leading
  flags like `-C`, add explicit rules for those forms instead of assuming they match.
- Define common absolute installation paths in `host-executables.rules.tmpl`, and test basename and
  absolute forms together with `--resolve-host-executables`.
- Keep mise installation paths in that template synchronized with `.node-version`,
  `.python-version`, and the tool definitions in `mise.toml`.
- Keep `justification` short, specific, and public-safe.

## Match Examples

- Add `match` and `not_match` examples for every rule.
- Treat `match` and `not_match` as inline unit tests for rule intent.
- Include at least one positive example for the base case and one realistic variant with extra
  arguments when relevant.
- Include negative examples for nearby mutating commands, reordered argv, or other cases that should
  not match.
- For overlapping decisions, add examples that make the precedence explicit.

## Safety

- Do not add rules that broadly allow shell wrappers such as `bash -lc` or `zsh -lc`.
- Do not include secrets, internal hosts, tokens, or private repository names in patterns, examples,
  or justifications.
- Prefer first-class command rules over allowing generic API or scripting entry points.

## Testing

- After editing a `.rules` file, run targeted checks with `codex execpolicy check`.
- Use representative commands that should resolve to `allow`, `prompt`, and `forbidden` where
  applicable.
- For overlapping decisions, test the overlap explicitly to confirm the final decision is the
  expected stricter result.
- Example:

```fish
codex execpolicy check --pretty --rules managed/dot_codex/rules/git.rules -- git status
codex execpolicy check --pretty --rules managed/dot_codex/rules/git.rules -- git add README.md
codex execpolicy check --pretty --rules managed/dot_codex/rules/git.rules -- git commit -m test
codex execpolicy check --pretty --rules managed/dot_codex/rules/gh.rules -- gh auth status --show-token
```

- If you changed multiple rule files, run at least one representative `codex execpolicy check`
  command per file.
- Validation confirms the source rules only. `chezmoi apply` materializes them under
  `~/.codex/rules`; restart Codex after applying them so new sessions load the updated policy.
