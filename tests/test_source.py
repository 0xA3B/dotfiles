import subprocess
from pathlib import Path

import pytest
from chezmoi_modify.exceptions import ChezmoiModifyError
from chezmoi_modify.source import read_source_template_text, read_source_text


def test_read_source_text_resolves_relative_paths_from_chezmoi_source_dir(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    managed_file = source_dir / "dot_config" / "uv" / "uv.managed.toml"
    managed_file.parent.mkdir(parents=True)
    managed_file.write_text('exclude-newer = "3 days"\n', encoding="utf-8")
    monkeypatch.setenv("CHEZMOI_SOURCE_DIR", str(source_dir))

    assert read_source_text("dot_config/uv/uv.managed.toml") == 'exclude-newer = "3 days"\n'


def test_read_source_text_rejects_absolute_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("CHEZMOI_SOURCE_DIR", str(tmp_path))

    with pytest.raises(ChezmoiModifyError, match="must be relative"):
        read_source_text(str(tmp_path / "managed.toml"))


def test_read_source_text_rejects_paths_outside_source_dir(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    monkeypatch.setenv("CHEZMOI_SOURCE_DIR", str(source_dir))

    with pytest.raises(ChezmoiModifyError, match="outside CHEZMOI_SOURCE_DIR"):
        read_source_text("../private.txt")


def test_read_source_text_rejects_symlinks_outside_source_dir(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    private_file = tmp_path / "private.txt"
    private_file.write_text("private\n", encoding="utf-8")
    (source_dir / "linked.txt").symlink_to(private_file)
    monkeypatch.setenv("CHEZMOI_SOURCE_DIR", str(source_dir))

    with pytest.raises(ChezmoiModifyError, match="outside CHEZMOI_SOURCE_DIR"):
        read_source_text("linked.txt")


def test_read_source_text_requires_chezmoi_source_dir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CHEZMOI_SOURCE_DIR", raising=False)

    with pytest.raises(ChezmoiModifyError, match="CHEZMOI_SOURCE_DIR is not set"):
        read_source_text("dot_npmrc.managed")


def test_read_source_text_raises_for_missing_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("CHEZMOI_SOURCE_DIR", str(tmp_path))

    with pytest.raises(ChezmoiModifyError, match="source file does not exist"):
        read_source_text("missing.managed")


def test_read_source_template_text_renders_with_chezmoi(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    template = source_dir / "settings.managed.jsonc.tmpl"
    template.write_text('{"home": "{{ .chezmoi.homeDir }}"}\n', encoding="utf-8")
    monkeypatch.setenv("CHEZMOI_SOURCE_DIR", str(source_dir))

    def fake_run(
        args: list[str],
        *,
        check: bool,
        capture_output: bool,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        assert args == [
            "chezmoi",
            "execute-template",
            "--source",
            str(source_dir),
            "--file",
            str(template),
        ]
        assert check is True
        assert capture_output is True
        assert text is True
        return subprocess.CompletedProcess(args, 0, stdout='{"home": "/Users/example"}\n')

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert read_source_template_text("settings.managed.jsonc.tmpl") == (
        '{"home": "/Users/example"}\n'
    )


def test_read_source_template_text_reports_render_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    template = source_dir / "settings.managed.jsonc.tmpl"
    template.write_text("{{ bad template }}\n", encoding="utf-8")
    monkeypatch.setenv("CHEZMOI_SOURCE_DIR", str(source_dir))

    def fake_run(
        args: list[str],
        *,
        check: bool,
        capture_output: bool,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        assert check is True
        assert capture_output is True
        assert text is True
        raise subprocess.CalledProcessError(1, args, stderr="template failed")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(ChezmoiModifyError, match="source template could not be rendered"):
        read_source_template_text("settings.managed.jsonc.tmpl")
