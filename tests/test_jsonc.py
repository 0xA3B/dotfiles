import json
import re
from textwrap import dedent

import pytest
from chezmoi_modify.exceptions import ChezmoiModifyError
from chezmoi_modify.jsonc import compose_jsonc_overlays, merge_jsonc_overlay


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


def test_semantically_satisfied_overlay_preserves_live_formatting() -> None:
    live = dedent(
        """\
        {
          // Unmanaged settings keep their existing representation.
          "claudeCode.environmentVariables": [{"name":"MODEL","value":"opus"}],
          "editor.fontSize": 14,
        }
        """,
    )

    result = merge_jsonc_overlay(live, '{"editor.fontSize": 14}')

    assert result.text == live
    assert result.diagnostics == ()


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


def test_composed_overlays_override_scalars_merge_objects_and_append_array_entries() -> None:
    composed = compose_jsonc_overlays(
        [
            (
                "core",
                """{
                  // Comments are allowed in each overlay.
                  "effortLevel": "high",
                  "env": {"SHELL": "bash", "TRACE": "0"},
                  "permissions": {"deny": ["Read(~/.ssh/**)", "Bash(sudo *)"]},
                }""",
            ),
            (
                "work",
                """{
                  "effortLevel": "medium",
                  "env": {"TRACE": "1"},
                  "permissions": {"deny": ["Bash(sudo *)", "Bash(tool *)"]},
                }""",
            ),
        ],
    )

    assert json.loads(composed) == {
        "effortLevel": "medium",
        "env": {"SHELL": "bash", "TRACE": "1"},
        "permissions": {"deny": ["Read(~/.ssh/**)", "Bash(sudo *)", "Bash(tool *)"]},
    }


def test_composed_overlays_name_the_overlay_that_fails_to_parse() -> None:
    with pytest.raises(
        ChezmoiModifyError, match=re.escape("work:settings.json.d/50-work.jsonc JSONC")
    ):
        compose_jsonc_overlays([("work:settings.json.d/50-work.jsonc", "{")])


def test_unordered_string_arrays_keep_live_text_when_only_entry_order_differs() -> None:
    live = '{\n  "deny": ["b", "a"],\n  "ask": ["c"]\n}\n'

    result = merge_jsonc_overlay(
        live,
        '{"deny": ["a", "b"], "ask": ["c"]}',
        unordered_string_arrays=True,
    )

    assert result.text == live


def test_unordered_string_arrays_keep_live_entry_order_when_another_key_changes() -> None:
    result = merge_jsonc_overlay(
        '{"deny": ["b", "a"], "theme": "light"}',
        '{"deny": ["a", "b"], "theme": "dark"}',
        unordered_string_arrays=True,
    )

    assert json.loads(result.text) == {"deny": ["b", "a"], "theme": "dark"}


def test_unordered_string_arrays_take_managed_entries_when_they_differ() -> None:
    result = merge_jsonc_overlay(
        '{"deny": ["b", "a"]}',
        '{"deny": ["a", "c"]}',
        unordered_string_arrays=True,
    )

    assert json.loads(result.text) == {"deny": ["a", "c"]}


def test_unordered_string_arrays_still_order_arrays_of_objects() -> None:
    result = merge_jsonc_overlay(
        '{"hooks": [{"name": "b"}, {"name": "a"}]}',
        '{"hooks": [{"name": "a"}, {"name": "b"}]}',
        unordered_string_arrays=True,
    )

    assert json.loads(result.text) == {"hooks": [{"name": "a"}, {"name": "b"}]}


def test_rewrites_can_keep_non_ascii_characters_literal() -> None:
    result = merge_jsonc_overlay(
        '{"rule": "old"}',
        '{"rule": "work \u2192 personal"}',
        ensure_ascii=False,
    )

    assert result.text == '{\n  "rule": "work \u2192 personal"\n}\n'


def test_unordered_string_arrays_keep_live_text_for_nested_arrays() -> None:
    live = '{"permissions": {"deny": ["b", "a"]}}\n'

    result = merge_jsonc_overlay(
        live,
        '{"permissions": {"deny": ["a", "b"]}}',
        unordered_string_arrays=True,
    )

    assert result.text == live


def test_empty_overlay_keeps_non_ascii_characters_literal() -> None:
    result = merge_jsonc_overlay('{"rule": "a → b"}', "{}", ensure_ascii=False)

    assert result.text == '{\n  "rule": "a → b"\n}\n'
