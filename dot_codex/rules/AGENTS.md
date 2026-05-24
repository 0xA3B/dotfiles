# Codex Rules Instructions

These instructions apply to files under `dot_codex/rules/`.

## Purpose

- These files define Codex execution-policy rules in Starlark using `prefix_rule(...)`.
- Keep rules narrowly scoped, easy to review, and safe to publish.

## Rule Authoring

- Prefer exact command-prefix rules over broad allowances.
- Use grouped unions in `pattern` only when the grouped commands clearly share the same intent and
  risk profile.
- Prefer absent rules to force prompts by default.
- Use `forbidden` sparingly for intentional hard denials where prompting is not desired.
- When allow and forbidden rules overlap, rely on Codex's most-restrictive-wins behavior
  intentionally and document it with examples.
- Remember that `pattern` matches argv positions exactly. If a command should also work with leading
  flags like `-C`, add explicit rules for those forms instead of assuming they match.
- Keep `justification` short, specific, and public-safe.

## Match Examples

- Add `match` and `not_match` examples for every rule.
- Treat `match` and `not_match` as inline unit tests for rule intent.
- Include at least one positive example for the base case and one realistic variant with extra
  arguments when relevant.
- Include negative examples for nearby mutating commands, reordered argv, or other cases that should
  not match.
- For overlapping rules, add examples that make the precedence explicit.

## Safety

- Do not add rules that broadly allow shell wrappers such as `bash -lc` or `zsh -lc`.
- Do not include secrets, internal hosts, tokens, or private repository names in patterns, examples,
  or justifications.
- Prefer first-class command rules over allowing generic API or scripting entry points.

## Testing

- After editing a `.rules` file, run targeted checks with `codex execpolicy check`.
- Use representative commands that should resolve to `allow`, `prompt`, and `forbidden` where
  applicable.
- For overlapping rules, test the overlap explicitly to confirm the final decision is the expected
  stricter result.
- Example:

```fish
codex execpolicy check --pretty --rules dot_codex/rules/git.rules -- git status
codex execpolicy check --pretty --rules dot_codex/rules/git.rules -- git commit -m test
codex execpolicy check --pretty --rules dot_codex/rules/git.rules -- git commit --no-verify -m test
```

- If you changed multiple rule files, run at least one representative `codex execpolicy check`
  command per file.
- Restart Codex if required so updated rules are loaded for normal use.
