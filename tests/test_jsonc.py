import json
from textwrap import dedent

import pytest
from chezmoi_modify.exceptions import ChezmoiModifyError
from chezmoi_modify.jsonc import merge_jsonc_overlay


def test_jsonc_overlay_overwrites_scalars_and_recursively_merges_objects() -> None:
    live = dedent(
        """\
        {
          // local setting remains
          "editor.fontSize": 14,
          "files.associations": {
            "*.tmpl": "gotmpl",
            "*.old": "plaintext"
          }
        }
        """,
    )
    managed = dedent(
        """\
        {
          "editor.fontSize": 16,
          "files.associations": {
            "*.tmpl": "toml"
          }
        }
        """,
    )

    result = merge_jsonc_overlay(live, managed)
    merged = json.loads(result.text)

    assert merged["editor.fontSize"] == 16
    assert merged["files.associations"]["*.tmpl"] == "toml"
    assert merged["files.associations"]["*.old"] == "plaintext"
    assert result.diagnostics == ()


def test_jsonc_overlay_replaces_arrays() -> None:
    result = merge_jsonc_overlay(
        '{"editor.rulers": [80, 120]}',
        '{"editor.rulers": [100]}',
    )

    assert json.loads(result.text)["editor.rulers"] == [100]


def test_jsonc_overlay_accepts_comments_trailing_commas_and_comment_markers_in_strings() -> None:
    live = dedent(
        """\
        {
          "url": "https://example.test/*not-comment*/",
          "pattern": "a//b",
        }
        """,
    )
    managed = dedent(
        """\
        {
          /* block comment */
          "managed": true,
        }
        """,
    )

    merged = json.loads(merge_jsonc_overlay(live, managed).text)

    assert merged["url"] == "https://example.test/*not-comment*/"
    assert merged["pattern"] == "a//b"
    assert merged["managed"] is True


def test_empty_managed_jsonc_overlay_is_quiet_noop() -> None:
    result = merge_jsonc_overlay('{"local": true}', "// no managed settings yet\n")

    assert result.text == '{\n  "local": true\n}\n'
    assert result.diagnostics == ()


def test_empty_live_jsonc_defaults_to_empty_object() -> None:
    result = merge_jsonc_overlay("", '{"managed": true}')

    assert result.text == '{\n  "managed": true\n}\n'


def test_jsonc_overlay_rejects_invalid_live_jsonc() -> None:
    with pytest.raises(ChezmoiModifyError, match="live JSONC could not be parsed"):
        merge_jsonc_overlay("{", '{"managed": true}')


def test_jsonc_overlay_rejects_non_object_roots() -> None:
    with pytest.raises(ChezmoiModifyError, match="managed JSONC must contain an object"):
        merge_jsonc_overlay("{}", "[]")
