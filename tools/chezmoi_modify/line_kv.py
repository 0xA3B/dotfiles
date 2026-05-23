"""Merge helpers for simple line-oriented key/value files."""

from __future__ import annotations

from dataclasses import dataclass

from chezmoi_modify.diagnostics import Diagnostic, MergeResult
from chezmoi_modify.exceptions import ChezmoiModifyError


@dataclass(frozen=True)
class _ManagedLine:
    key: str
    text: str


def merge_managed_keys(live: str, managed: str, *, separator: str = "=") -> MergeResult:
    """Apply authoritative managed key/value lines to live text.

    The managed line text is canonical for managed keys. Existing managed keys
    are replaced at their first live occurrence, later live duplicates are
    removed, missing managed keys are inserted as a top block, and unmanaged
    duplicate keys are preserved.
    """
    if separator == "":
        msg = "separator must not be empty"
        raise ChezmoiModifyError(msg)

    managed_lines = _parse_managed_lines(managed, separator)
    if not managed_lines:
        return MergeResult(
            text=_ensure_one_trailing_newline(live),
            diagnostics=(
                Diagnostic(
                    severity="warning",
                    message="managed key/value overlay is empty",
                ),
            ),
        )

    managed_by_key = {line.key: line.text for line in managed_lines}
    seen_managed_keys: set[str] = set()
    output_lines: list[str] = []

    for line in live.splitlines():
        key = _assignment_key(line, separator)
        if key is None or key not in managed_by_key:
            output_lines.append(line)
            continue
        if key in seen_managed_keys:
            continue
        output_lines.append(managed_by_key[key])
        seen_managed_keys.add(key)

    missing_lines = [line.text for line in managed_lines if line.key not in seen_managed_keys]
    if missing_lines:
        output_lines = [*missing_lines, "", *_without_leading_blank_lines(output_lines)]

    return MergeResult(text=_lines_to_text(output_lines))


def _parse_managed_lines(managed: str, separator: str) -> list[_ManagedLine]:
    managed_lines: list[_ManagedLine] = []
    seen_keys: set[str] = set()

    for line in managed.splitlines():
        stripped = line.strip()
        if stripped == "" or stripped.startswith(("#", ";")):
            continue
        key = _assignment_key(line, separator)
        if key is None:
            msg = f"managed key/value line is missing separator {separator!r}: {line!r}"
            raise ChezmoiModifyError(msg)
        if key in seen_keys:
            msg = f"managed key/value overlay contains duplicate key: {key}"
            raise ChezmoiModifyError(msg)
        managed_lines.append(_ManagedLine(key=key, text=line))
        seen_keys.add(key)

    return managed_lines


def _assignment_key(line: str, separator: str) -> str | None:
    if separator not in line:
        return None
    key, _value = line.split(separator, maxsplit=1)
    return key.strip(" \t")


def _lines_to_text(lines: list[str]) -> str:
    if not lines:
        return ""
    return "\n".join(lines).rstrip("\n") + "\n"


def _ensure_one_trailing_newline(text: str) -> str:
    if text == "":
        return ""
    return text.rstrip("\n") + "\n"


def _without_leading_blank_lines(lines: list[str]) -> list[str]:
    first_content_index = next(
        (index for index, line in enumerate(lines) if line.strip() != ""),
        len(lines),
    )
    return lines[first_content_index:]
