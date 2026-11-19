"""Merge helpers for TOML managed overlays."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

import tomlkit
from tomlkit.items import AoT, Array, Table

from chezmoi_modify.diagnostics import Diagnostic, MergeResult
from chezmoi_modify.exceptions import ChezmoiModifyError

type _IdentityConfig = Mapping[str, tuple[str, ...]]
type _IdentityPathConfig = dict[tuple[str, ...], tuple[str, ...]]


def merge_toml_overlay(
    live: str,
    managed: str,
    *,
    array_table_identity: _IdentityConfig | None = None,
) -> MergeResult:
    """Apply an authoritative TOML overlay to live TOML text."""
    live_doc = _parse_toml(live, "live")
    managed_doc = _parse_toml(managed, "managed")
    diagnostics: list[Diagnostic] = []
    if not managed_doc:
        return MergeResult(
            text=_ensure_one_trailing_newline(tomlkit.dumps(live_doc)),
            diagnostics=(
                Diagnostic(
                    severity="warning",
                    message="managed TOML overlay is empty",
                ),
            ),
        )

    identity_config = _normalize_identity_config(array_table_identity or {})

    _merge_table(
        live_doc,
        managed_doc,
        path=(),
        identity_config=identity_config,
        diagnostics=diagnostics,
    )

    return MergeResult(
        text=_ensure_one_trailing_newline(tomlkit.dumps(live_doc)),
        diagnostics=tuple(diagnostics),
    )


def compose_toml_overlays(
    overlays: Sequence[tuple[str, str]],
    *,
    array_table_identity: _IdentityConfig | None = None,
) -> str:
    """Compose ``(label, text)`` TOML overlays, in order, into one TOML overlay.

    Standard tables merge recursively. In an array of tables named in
    ``array_table_identity``, a later entry merges into the earlier entry with the same
    identity and other entries append, and inline arrays concatenate without duplicates,
    so a later overlay adds entries to those without removing any. The later overlay
    replaces every other value: scalars, inline tables, arrays of tables without an
    identity, and values whose type differs between overlays. An overlay that does not
    parse raises an error that names its label.
    """
    identity_config = _normalize_identity_config(array_table_identity or {})
    composed = tomlkit.document()
    for label, text in overlays:
        _compose_table(composed, _parse_toml(text, label), path=(), identity_config=identity_config)
    return tomlkit.dumps(composed)


def _compose_table(
    base: Any,
    overlay: Any,
    *,
    path: tuple[str, ...],
    identity_config: _IdentityPathConfig,
) -> None:
    for key, value in overlay.items():
        key_path = (*path, str(key))
        base_value = base.get(key)
        if key_path in identity_config:
            if not isinstance(value, AoT):
                msg = f"managed TOML path {'.'.join(key_path)} must be an array of tables"
                raise ChezmoiModifyError(msg)
            identity_fields = identity_config[key_path]
            _validate_managed_identities(value, identity_fields, key_path)
            if base_value is None:
                base[key] = deepcopy(value)
                continue
            for entry in value:
                identity = _entry_identity(entry, identity_fields, key_path)
                match = next(
                    (
                        base_entry
                        for base_entry in base_value
                        if _entry_matches_identity(base_entry, identity_fields, identity)
                    ),
                    None,
                )
                if match is None:
                    base_value.append(deepcopy(entry))
                else:
                    _compose_table(match, entry, path=key_path, identity_config=identity_config)
        elif _is_mergeable_table(base_value, value):
            _compose_table(base_value, value, path=key_path, identity_config=identity_config)
        elif isinstance(base_value, Array) and isinstance(value, Array):
            for item in value:
                if item not in base_value:
                    base_value.append(deepcopy(item))
        else:
            base[key] = deepcopy(value)


def _parse_toml(text: str, label: str) -> Any:
    try:
        return tomlkit.parse(text)
    except tomlkit.exceptions.ParseError as error:
        msg = f"{label} TOML could not be parsed: {error}"
        raise ChezmoiModifyError(msg) from error


def _normalize_identity_config(identity_config: _IdentityConfig) -> _IdentityPathConfig:
    return {
        tuple(path.split(".")): identity_fields for path, identity_fields in identity_config.items()
    }


def _merge_table(
    live_table: Any,
    managed_table: Any,
    *,
    path: tuple[str, ...],
    identity_config: _IdentityPathConfig,
    diagnostics: list[Diagnostic],
) -> None:
    for key, managed_value in managed_table.items():
        key_path = (*path, str(key))
        if key_path in identity_config:
            _merge_array_table(
                live_table,
                str(key),
                managed_value,
                identity_fields=identity_config[key_path],
                identity_path=key_path,
                identity_config=identity_config,
                diagnostics=diagnostics,
            )
            continue

        live_value = live_table.get(key)
        if _is_mergeable_table(live_value, managed_value):
            _merge_table(
                live_value,
                managed_value,
                path=key_path,
                identity_config=identity_config,
                diagnostics=diagnostics,
            )
            continue

        live_table[key] = deepcopy(managed_value)


def _merge_array_table(
    live_table: Any,
    key: str,
    managed_value: Any,
    *,
    identity_fields: tuple[str, ...],
    identity_path: tuple[str, ...],
    identity_config: _IdentityPathConfig,
    diagnostics: list[Diagnostic],
) -> None:
    if not isinstance(managed_value, AoT):
        msg = f"managed TOML path {'.'.join(identity_path)} must be an array of tables"
        raise ChezmoiModifyError(msg)

    _validate_managed_identities(managed_value, identity_fields, identity_path)
    live_value = live_table.get(key)
    if live_value is None:
        live_table[key] = deepcopy(managed_value)
        return
    if not isinstance(live_value, AoT):
        msg = f"live TOML path {'.'.join(identity_path)} must be an array of tables"
        raise ChezmoiModifyError(msg)

    for managed_entry in managed_value:
        identity = _entry_identity(managed_entry, identity_fields, identity_path)
        first_match: Table | None = None
        duplicate_indexes: list[int] = []
        for index, live_entry in enumerate(live_value):
            if _entry_matches_identity(live_entry, identity_fields, identity):
                if first_match is None:
                    first_match = live_entry
                else:
                    duplicate_indexes.append(index)

        if first_match is None:
            live_value.append(deepcopy(managed_entry))
            continue

        _merge_table(
            first_match,
            managed_entry,
            path=identity_path,
            identity_config=identity_config,
            diagnostics=diagnostics,
        )
        if duplicate_indexes:
            diagnostics.append(
                Diagnostic(
                    severity="warning",
                    message=(
                        f"removed {len(duplicate_indexes)} duplicate live TOML "
                        f"array table entry at {'.'.join(identity_path)} "
                        f"for identity {identity!r}"
                    ),
                ),
            )
        for index in reversed(duplicate_indexes):
            del live_value[index]


def _validate_managed_identities(
    managed_entries: AoT,
    identity_fields: tuple[str, ...],
    identity_path: tuple[str, ...],
) -> None:
    seen_identities: set[tuple[Any, ...]] = set()
    for managed_entry in managed_entries:
        identity = _entry_identity(managed_entry, identity_fields, identity_path)
        if identity in seen_identities:
            msg = (
                "managed TOML array table contains duplicate managed identity "
                f"at {'.'.join(identity_path)}: {identity!r}"
            )
            raise ChezmoiModifyError(msg)
        seen_identities.add(identity)


def _entry_identity(
    entry: Table,
    identity_fields: tuple[str, ...],
    identity_path: tuple[str, ...],
) -> tuple[Any, ...]:
    values: list[Any] = []
    for field in identity_fields:
        if field not in entry:
            msg = (
                f"managed TOML array table at {'.'.join(identity_path)} "
                f"missing identity key: {field}"
            )
            raise ChezmoiModifyError(msg)
        values.append(entry[field])
    return tuple(values)


def _entry_matches_identity(
    entry: Table,
    identity_fields: tuple[str, ...],
    identity: tuple[Any, ...],
) -> bool:
    return all(
        field in entry and entry[field] == identity[index]
        for index, field in enumerate(identity_fields)
    )


def _is_mergeable_table(live_value: Any, managed_value: Any) -> bool:
    return (
        isinstance(live_value, Table)
        and isinstance(managed_value, Table)
        and not isinstance(live_value, AoT)
        and not isinstance(managed_value, AoT)
    )


def _ensure_one_trailing_newline(text: str) -> str:
    if text == "":
        return ""
    return text.rstrip("\n") + "\n"
