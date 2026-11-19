"""Merge helpers for JSONC managed overlays.

JSONC comments and trailing commas are accepted as input. Changes emit canonical
JSON, while semantic no-ops preserve the original live text.
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import TYPE_CHECKING, Any

from chezmoi_modify.diagnostics import MergeResult
from chezmoi_modify.exceptions import ChezmoiModifyError

if TYPE_CHECKING:
    from collections.abc import Sequence


def merge_jsonc_overlay(
    live: str,
    managed: str,
    *,
    unordered_string_arrays: bool = False,
    ensure_ascii: bool = True,
) -> MergeResult:
    """Apply an authoritative JSONC object overlay to live JSONC text.

    With ``unordered_string_arrays``, a managed array of strings that holds the same
    entries as the live array keeps the live order, so a different order alone never
    rewrites the file. Arrays of other values still compare in order. With
    ``ensure_ascii=False``, a rewrite writes non-ASCII characters literally instead of
    as Unicode escape sequences.
    """
    live_doc = _parse_jsonc_object(live, "live", default_empty=True)
    managed_doc = _parse_jsonc_object(managed, "managed", default_empty=True)
    if not managed_doc:
        return MergeResult(text=_dump_json(live_doc, ensure_ascii=ensure_ascii), diagnostics=())

    original_doc = deepcopy(live_doc)
    _merge_object(live_doc, managed_doc, unordered_string_arrays=unordered_string_arrays)
    if live_doc == original_doc:
        return MergeResult(text=live, diagnostics=())
    return MergeResult(text=_dump_json(live_doc, ensure_ascii=ensure_ascii), diagnostics=())


def compose_jsonc_overlays(overlays: Sequence[tuple[str, str]]) -> str:
    """Compose ``(label, text)`` JSONC overlays, in order, into one JSON overlay.

    Later overlays win for scalars, objects merge recursively, and arrays concatenate
    without duplicates, so a later overlay can add entries but never remove them. An
    overlay that does not parse raises an error that names its label.
    """
    composed: dict[str, Any] = {}
    for label, text in overlays:
        _compose_object(composed, _parse_jsonc_object(text, label, default_empty=True))
    return json.dumps(composed)


def _compose_object(base: dict[str, Any], overlay: dict[str, Any]) -> None:
    for key, value in overlay.items():
        current = base.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            _compose_object(current, value)
        elif isinstance(current, list) and isinstance(value, list):
            current.extend(item for item in deepcopy(value) if item not in current)
        else:
            base[key] = deepcopy(value)


def _parse_jsonc_object(text: str, label: str, *, default_empty: bool) -> dict[str, Any]:
    normalized = _strip_trailing_commas(_strip_jsonc_comments(text)).strip()
    if not normalized and default_empty:
        return {}
    try:
        value = json.loads(normalized)
    except json.JSONDecodeError as error:
        msg = f"{label} JSONC could not be parsed: {error}"
        raise ChezmoiModifyError(msg) from error
    if not isinstance(value, dict):
        msg = f"{label} JSONC must contain an object at the document root"
        raise ChezmoiModifyError(msg)
    return value


def _merge_object(
    live: dict[str, Any],
    managed: dict[str, Any],
    *,
    unordered_string_arrays: bool = False,
) -> None:
    for key, managed_value in managed.items():
        live_value = live.get(key)
        if isinstance(live_value, dict) and isinstance(managed_value, dict):
            _merge_object(
                live_value, managed_value, unordered_string_arrays=unordered_string_arrays
            )
            continue
        if unordered_string_arrays and _same_string_set(live_value, managed_value):
            continue
        live[key] = deepcopy(managed_value)


def _same_string_set(live_value: Any, managed_value: Any) -> bool:
    return (
        isinstance(live_value, list)
        and isinstance(managed_value, list)
        and all(isinstance(item, str) for item in live_value + managed_value)
        and sorted(live_value) == sorted(managed_value)
    )


def _dump_json(value: dict[str, Any], *, ensure_ascii: bool = True) -> str:
    return f"{json.dumps(value, indent=2, ensure_ascii=ensure_ascii)}\n"


def _strip_jsonc_comments(text: str) -> str:
    result: list[str] = []
    index = 0
    in_string = False
    escape = False

    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""

        if in_string:
            result.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            index += 1
            continue

        if char == '"':
            in_string = True
            result.append(char)
            index += 1
            continue

        if char == "/" and next_char == "/":
            index += 2
            while index < len(text) and text[index] not in "\r\n":
                index += 1
            continue

        if char == "/" and next_char == "*":
            index += 2
            while index < len(text) - 1:
                if text[index] == "*" and text[index + 1] == "/":
                    index += 2
                    break
                if text[index] in "\r\n":
                    result.append(text[index])
                index += 1
            continue

        result.append(char)
        index += 1

    return "".join(result)


def _strip_trailing_commas(text: str) -> str:
    result: list[str] = []
    index = 0
    in_string = False
    escape = False

    while index < len(text):
        char = text[index]

        if in_string:
            result.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            index += 1
            continue

        if char == '"':
            in_string = True
            result.append(char)
            index += 1
            continue

        if char == ",":
            lookahead = index + 1
            while lookahead < len(text) and text[lookahead].isspace():
                lookahead += 1
            if lookahead < len(text) and text[lookahead] in "}]":
                index += 1
                continue

        result.append(char)
        index += 1

    return "".join(result)
