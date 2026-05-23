from textwrap import dedent

import pytest
from chezmoi_modify import ChezmoiModifyError, Diagnostic, merge_managed_keys


def test_managed_key_replaces_first_occurrence_and_removes_duplicates() -> None:
    live = dedent(
        """\
        # registry used before dotfiles managed this key
        registry=https://old.example/

        _authToken=local
        registry=https://duplicate.example/
        """,
    )
    managed = "registry=https://registry.npmjs.org/\n"

    result = merge_managed_keys(live, managed)

    assert result.text == dedent(
        """\
            # registry used before dotfiles managed this key
            registry=https://registry.npmjs.org/

            _authToken=local
            """,
    )
    assert result.diagnostics == ()


def test_missing_managed_keys_are_inserted_as_a_top_block() -> None:
    live = dedent(
        """
        foo=old

        bar=local
        foo=duplicate
        """,
    )
    managed = dedent(
        """\
        baz=new
        qux=also-new
        foo=managed
        """,
    )

    result = merge_managed_keys(live, managed)

    assert result.text == dedent(
        """\
            baz=new
            qux=also-new

            foo=managed

            bar=local
            """,
    )


def test_empty_managed_overlay_warns_and_preserves_live_content() -> None:
    result = merge_managed_keys("local=true", "# temporarily empty\n\n")

    assert result.text == "local=true\n"
    assert result.diagnostics == (
        Diagnostic(
            severity="warning",
            message="managed key/value overlay is empty",
        ),
    )


def test_managed_overlay_rejects_duplicate_keys() -> None:
    managed = dedent(
        """\
        registry=https://registry.npmjs.org/
        registry=https://duplicate.example/
        """,
    )

    with pytest.raises(ChezmoiModifyError, match="duplicate key: registry"):
        merge_managed_keys("", managed)


def test_managed_overlay_rejects_non_assignment_lines() -> None:
    with pytest.raises(ChezmoiModifyError, match="missing separator"):
        merge_managed_keys("", "not-an-assignment\n")


def test_separator_must_not_be_empty() -> None:
    with pytest.raises(ChezmoiModifyError, match="separator must not be empty"):
        merge_managed_keys("", "key=value\n", separator="")


def test_key_matching_uses_text_before_first_separator() -> None:
    live = dedent(
        """\
        @scope:registry=https://old.example/
        //registry.npmjs.org/:_authToken=${NPM_TOKEN}
        """,
    )
    managed = "@scope:registry=https://scope.example/ # inline text is part of value\n"

    result = merge_managed_keys(live, managed)

    assert result.text == dedent(
        """\
            @scope:registry=https://scope.example/ # inline text is part of value
            //registry.npmjs.org/:_authToken=${NPM_TOKEN}
            """,
    )


def test_merge_managed_keys_is_idempotent() -> None:
    live = dedent(
        """\
        baz=old
        foo=old
        foo=duplicate
        local=true
        """,
    )
    managed = dedent(
        """\
        foo=managed
        bar=managed
        """,
    )

    first_result = merge_managed_keys(live, managed)
    second_result = merge_managed_keys(first_result.text, managed)

    assert second_result.text == first_result.text


def test_merge_managed_keys_supports_non_default_separator() -> None:
    live = dedent(
        """\
        key:old
        other:local
        key:duplicate
        """,
    )
    managed = "key:managed\n"

    result = merge_managed_keys(live, managed, separator=":")

    assert result.text == dedent(
        """\
            key:managed
            other:local
            """,
    )
