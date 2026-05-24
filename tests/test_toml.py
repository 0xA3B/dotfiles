from textwrap import dedent

import pytest
import tomlkit
from chezmoi_modify.diagnostics import Diagnostic
from chezmoi_modify.exceptions import ChezmoiModifyError
from chezmoi_modify.toml import merge_toml_overlay


def test_toml_overlay_overwrites_scalars_and_recursively_merges_tables() -> None:
    live = dedent(
        """\
        exclude-newer = false

        [tool]
        local-only = true
        owned = "old"
        """,
    )
    managed = dedent(
        """\
        exclude-newer = "3 days"

        [tool]
        owned = "new"
        """,
    )

    result = merge_toml_overlay(live, managed)
    merged = tomlkit.parse(result.text)

    assert merged["exclude-newer"] == "3 days"
    assert merged["tool"]["local-only"] is True
    assert merged["tool"]["owned"] == "new"
    assert result.diagnostics == ()


def test_toml_overlay_matches_array_tables_by_configured_identity() -> None:
    live = dedent(
        """\
        [[index]]
        name = "local-pypi"
        url = "https://pypi.org/simple"
        authenticate = "never"

        [[index]]
        name = "duplicate-pypi"
        url = "https://pypi.org/simple"
        extra = true

        [[index]]
        name = "internal"
        url = "https://internal.example/simple"
        """,
    )
    managed = dedent(
        """\
        [[index]]
        name = "pypi"
        url = "https://pypi.org/simple"

        [[index]]
        name = "other"
        url = "https://other.example/simple"
        """,
    )

    result = merge_toml_overlay(
        live,
        managed,
        array_table_identity={"index": ("url",)},
    )
    merged = tomlkit.parse(result.text)

    assert [index["url"] for index in merged["index"]] == [
        "https://pypi.org/simple",
        "https://internal.example/simple",
        "https://other.example/simple",
    ]
    assert merged["index"][0]["name"] == "pypi"
    assert merged["index"][0]["authenticate"] == "never"
    assert "extra" not in merged["index"][0]
    assert result.diagnostics == (
        Diagnostic(
            severity="warning",
            message=(
                "removed 1 duplicate live TOML array table entry "
                "at index for identity ('https://pypi.org/simple',)"
            ),
        ),
    )


def test_toml_overlay_rejects_managed_array_table_missing_identity() -> None:
    managed = dedent(
        """\
        [[index]]
        name = "pypi"
        """,
    )

    with pytest.raises(ChezmoiModifyError, match="missing identity key: url"):
        merge_toml_overlay("", managed, array_table_identity={"index": ("url",)})


def test_toml_overlay_rejects_duplicate_managed_array_table_identity() -> None:
    managed = dedent(
        """\
        [[index]]
        name = "pypi"
        url = "https://pypi.org/simple"

        [[index]]
        name = "duplicate"
        url = "https://pypi.org/simple"
        """,
    )

    with pytest.raises(ChezmoiModifyError, match="duplicate managed identity"):
        merge_toml_overlay("", managed, array_table_identity={"index": ("url",)})


def test_toml_overlay_supports_dotted_array_table_identity_paths() -> None:
    live = dedent(
        """\
        [[tool.uv.index]]
        name = "local"
        url = "https://pypi.org/simple"
        """,
    )
    managed = dedent(
        """\
        [[tool.uv.index]]
        name = "pypi"
        url = "https://pypi.org/simple"
        """,
    )

    result = merge_toml_overlay(
        live,
        managed,
        array_table_identity={"tool.uv.index": ("url",)},
    )
    merged = tomlkit.parse(result.text)

    assert len(merged["tool"]["uv"]["index"]) == 1
    assert merged["tool"]["uv"]["index"][0]["name"] == "pypi"


def test_toml_overlay_replaces_arrays_without_identity_rules() -> None:
    live = 'values = ["local", "old"]\n'
    managed = 'values = ["managed"]\n'

    result = merge_toml_overlay(live, managed)
    merged = tomlkit.parse(result.text)

    assert merged["values"] == ["managed"]


def test_toml_overlay_warns_and_preserves_live_content_for_empty_managed_overlay() -> None:
    result = merge_toml_overlay('live = "ok"\n', "# temporarily empty\n")

    assert result.text == 'live = "ok"\n'
    assert result.diagnostics == (
        Diagnostic(
            severity="warning",
            message="managed TOML overlay is empty",
        ),
    )


def test_toml_overlay_matches_non_string_array_table_identity_values() -> None:
    live = dedent(
        """\
        [[server]]
        id = 1
        enabled = false
        local = true
        """,
    )
    managed = dedent(
        """\
        [[server]]
        id = 1
        enabled = true
        """,
    )

    result = merge_toml_overlay(live, managed, array_table_identity={"server": ("id",)})
    merged = tomlkit.parse(result.text)

    assert merged["server"][0]["enabled"] is True
    assert merged["server"][0]["local"] is True


def test_toml_overlay_array_table_merge_is_idempotent() -> None:
    live = dedent(
        """\
        [[index]]
        name = "local-pypi"
        url = "https://pypi.org/simple"

        [[index]]
        name = "duplicate-pypi"
        url = "https://pypi.org/simple"
        """,
    )
    managed = dedent(
        """\
        [[index]]
        name = "pypi"
        url = "https://pypi.org/simple"
        """,
    )

    first_result = merge_toml_overlay(
        live,
        managed,
        array_table_identity={"index": ("url",)},
    )
    second_result = merge_toml_overlay(
        first_result.text,
        managed,
        array_table_identity={"index": ("url",)},
    )

    assert second_result.text == first_result.text


def test_toml_overlay_rejects_invalid_live_toml() -> None:
    with pytest.raises(ChezmoiModifyError, match="live TOML could not be parsed"):
        merge_toml_overlay("invalid = [", 'managed = "ok"\n')


def test_toml_overlay_rejects_invalid_managed_toml() -> None:
    with pytest.raises(ChezmoiModifyError, match="managed TOML could not be parsed"):
        merge_toml_overlay('live = "ok"\n', "invalid = [")
