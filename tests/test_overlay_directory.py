"""Overlay directory reads against a real chezmoi binary, which renders the templates.

CI installs no chezmoi, so these tests skip there.
"""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import tomlkit
from chezmoi_modify.exceptions import ChezmoiModifyError
from chezmoi_modify.source import read_overlay_directory

pytestmark = pytest.mark.skipif(shutil.which("chezmoi") is None, reason="chezmoi is not on PATH")

MODIFY_SCRIPT = "private_dot_app/modify_private_settings.json.tmpl"
OVERLAY_DIRECTORY = "private_dot_app/settings.json.d"


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A dotfiles repository whose config makes `work` active and `old` inactive."""
    root = tmp_path / "repo"
    (root / "managed").mkdir(parents=True)
    config = write(
        tmp_path / "chezmoi.toml",
        '[data]\nflavor = "dark"\n\n[data.dotfiles_sources]\nwork = "git@example.invalid:w"\n'
        'old = ""\n',
    )
    monkeypatch.setenv("CHEZMOI_SOURCE_DIR", str(root / "managed"))
    monkeypatch.setenv("CHEZMOI_CONFIG_FILE", str(config))
    return root


def add_checkout(root: Path, name: str) -> Path:
    checkout = root / f"managed-{name}"
    (checkout / ".git").mkdir(parents=True)
    return checkout


def test_reads_primary_overlays_by_name_then_each_active_secondary_source(repo: Path) -> None:
    primary = repo / "managed" / OVERLAY_DIRECTORY
    write(primary / "20-later.jsonc", '{"b": 2}\n')
    write(primary / "10-first.jsonc.tmpl", '{"flavor": "{{ .flavor }}"}\n')
    write(primary / ".hidden.jsonc", '{"hidden": true}\n')
    work = add_checkout(repo, "work")
    write(work / ".chezmoiroot", "home\n")
    write(work / "home/.chezmoitemplates/team", "sre")
    write(
        work / "home" / OVERLAY_DIRECTORY / "50-work.jsonc.tmpl",
        '{"team": "{{ template "team" }}"}',
    )
    old = add_checkout(repo, "old")
    write(old / OVERLAY_DIRECTORY / "50-old.jsonc", '{"old": true}\n')

    assert read_overlay_directory(MODIFY_SCRIPT) == [
        (f"personal:{OVERLAY_DIRECTORY}/10-first.jsonc.tmpl", '{"flavor": "dark"}\n'),
        (f"personal:{OVERLAY_DIRECTORY}/20-later.jsonc", '{"b": 2}\n'),
        (f"work:{OVERLAY_DIRECTORY}/50-work.jsonc.tmpl", '{"team": "sre"}'),
    ]


def test_names_the_overlay_directory_after_a_dot_file_target(repo: Path) -> None:
    write(add_checkout(repo, "work") / "dot_apprc.d/.keep", "")
    write(repo / "managed/dot_apprc.d/10-core.jsonc", "{}\n")

    assert read_overlay_directory("modify_private_dot_apprc") == [
        ("personal:dot_apprc.d/10-core.jsonc", "{}\n"),
    ]


def test_reads_only_the_primary_source_when_no_secondary_source_is_configured(
    tmp_path: Path,
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CHEZMOI_CONFIG_FILE", str(write(tmp_path / "personal.toml", "[data]\n")))
    write(repo / "managed" / OVERLAY_DIRECTORY / "10-core.jsonc", "{}\n")

    assert read_overlay_directory(MODIFY_SCRIPT) == [
        (f"personal:{OVERLAY_DIRECTORY}/10-core.jsonc", "{}\n"),
    ]


def test_reads_active_secondary_sources_alphabetically(
    tmp_path: Path,
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = write(
        tmp_path / "two.toml",
        '[data.dotfiles_sources]\nwork = "git@example.invalid:w"\n'
        'alpha = "git@example.invalid:a"\n',
    )
    monkeypatch.setenv("CHEZMOI_CONFIG_FILE", str(config))
    for name in ("work", "alpha"):
        write(add_checkout(repo, name) / OVERLAY_DIRECTORY / f"50-{name}.jsonc", "{}\n")

    assert [label for label, _ in read_overlay_directory(MODIFY_SCRIPT)] == [
        f"alpha:{OVERLAY_DIRECTORY}/50-alpha.jsonc",
        f"work:{OVERLAY_DIRECTORY}/50-work.jsonc",
    ]


def test_fails_when_an_active_secondary_source_is_not_a_git_checkout(repo: Path) -> None:
    write(repo / "managed-work" / OVERLAY_DIRECTORY / "50-work.jsonc", "{}\n")

    with pytest.raises(ChezmoiModifyError, match="active source work has no checkout"):
        read_overlay_directory(MODIFY_SCRIPT)


def test_fails_when_an_active_secondary_source_lacks_the_overlay_directory(repo: Path) -> None:
    write(repo / "managed" / OVERLAY_DIRECTORY / "10-core.jsonc", "{}\n")
    add_checkout(repo, "work")

    with pytest.raises(ChezmoiModifyError, match=re.escape(f"work has no {OVERLAY_DIRECTORY}")):
        read_overlay_directory(MODIFY_SCRIPT)


def test_accepts_an_overlay_directory_that_holds_only_hidden_files(repo: Path) -> None:
    write(repo / "managed" / OVERLAY_DIRECTORY / "10-core.jsonc", "{}\n")
    write(add_checkout(repo, "work") / OVERLAY_DIRECTORY / ".keep", "")

    assert read_overlay_directory(MODIFY_SCRIPT) == [
        (f"personal:{OVERLAY_DIRECTORY}/10-core.jsonc", "{}\n"),
    ]


def test_fails_when_an_active_secondary_source_has_no_checkout(repo: Path) -> None:
    write(repo / "managed" / OVERLAY_DIRECTORY / "10-core.jsonc", "{}\n")

    with pytest.raises(ChezmoiModifyError, match="active source work has no checkout"):
        read_overlay_directory(MODIFY_SCRIPT)


def test_fails_when_an_overlay_cannot_be_rendered(repo: Path) -> None:
    work = add_checkout(repo, "work")
    write(work / OVERLAY_DIRECTORY / "50-work.jsonc.tmpl", "{{ .missing.key }}\n")

    with pytest.raises(ChezmoiModifyError, match=re.escape(f"work:{OVERLAY_DIRECTORY}/50-work")):
        read_overlay_directory(MODIFY_SCRIPT)


def test_fails_when_an_overlay_directory_cannot_be_listed(repo: Path) -> None:
    work = add_checkout(repo, "work")
    write(work / OVERLAY_DIRECTORY / "50-work.jsonc", "{}\n")
    (work / "private_dot_app").chmod(0)
    try:
        with pytest.raises(ChezmoiModifyError, match=re.escape(f"work:{OVERLAY_DIRECTORY}")):
            read_overlay_directory(MODIFY_SCRIPT)
    finally:
        (work / "private_dot_app").chmod(0o755)


def test_rejects_an_overlay_that_links_outside_its_source(tmp_path: Path, repo: Path) -> None:
    add_checkout(repo, "work")
    outside = write(tmp_path / "private.jsonc", '{"private": true}\n')
    overlay = repo / "managed" / OVERLAY_DIRECTORY / "10-core.jsonc"
    overlay.parent.mkdir(parents=True)
    overlay.symlink_to(outside)

    with pytest.raises(ChezmoiModifyError, match="outside its source"):
        read_overlay_directory(MODIFY_SCRIPT)


@pytest.mark.usefixtures("repo")
@pytest.mark.parametrize("modify_script", ["/abs/modify_settings.json", "../modify_settings.json"])
def test_rejects_a_modify_script_path_outside_the_primary_source(modify_script: str) -> None:
    with pytest.raises(ChezmoiModifyError, match=r"relative|outside CHEZMOI_SOURCE_DIR"):
        read_overlay_directory(modify_script)


_REPO = Path(__file__).resolve().parent.parent
_MODIFY_BODY = "modify_jsonc_overlay_directory.py"


def chezmoi_cat(tmp_path: Path, repo: Path, target: Path) -> subprocess.CompletedProcess[str]:
    """Render a target through chezmoi with the repository's real tools and modify body."""
    (repo / "tools").symlink_to(_REPO / "tools")
    templates = repo / "managed/.chezmoitemplates"
    templates.mkdir(parents=True, exist_ok=True)
    shutil.copy(_REPO / "managed/.chezmoitemplates" / _MODIFY_BODY, templates)
    return subprocess.run(  # noqa: S603
        [  # noqa: S607
            "chezmoi",
            "--source",
            str(repo / "managed"),
            "--destination",
            str(tmp_path / "home"),
            "--config",
            os.environ["CHEZMOI_CONFIG_FILE"],
            "--persistent-state",
            str(tmp_path / "state.boltdb"),
            "cat",
            str(target),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_modify_script_applies_the_composed_overlays_to_the_live_file(
    tmp_path: Path,
    repo: Path,
) -> None:
    write(repo / "managed" / MODIFY_SCRIPT, f'{{{{- template "{_MODIFY_BODY}" . -}}}}\n')
    write(
        repo / "managed" / OVERLAY_DIRECTORY / "10-core.jsonc",
        '{\n  // Core.\n  "theme": "dark",\n  "deny": ["Bash(sudo *)"],\n}\n',
    )
    work = add_checkout(repo, "work")
    write(work / OVERLAY_DIRECTORY / "50-work.jsonc", '{"deny": ["Bash(tool *)"]}\n')
    target = write(tmp_path / "home/.app/settings.json", '{"local": "→ kept", "theme": "light"}\n')

    result = chezmoi_cat(tmp_path, repo, target)

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "local": "→ kept",
        "theme": "dark",
        "deny": ["Bash(sudo *)", "Bash(tool *)"],
    }
    assert "→ kept" in result.stdout


def test_modify_script_keeps_the_live_text_when_only_array_order_differs(
    tmp_path: Path,
    repo: Path,
) -> None:
    write(repo / "managed" / MODIFY_SCRIPT, f'{{{{- template "{_MODIFY_BODY}" . -}}}}\n')
    write(
        repo / "managed" / OVERLAY_DIRECTORY / "10-core.jsonc", '{"p": {"deny": ["Bash(sudo *)"]}}'
    )
    work = add_checkout(repo, "work")
    write(work / OVERLAY_DIRECTORY / "50-work.jsonc", '{"p": {"deny": ["Bash(tool *)"]}}\n')
    live = '{\n  "p": {"deny": ["Bash(tool *)", "Bash(sudo *)"]}\n}\n'
    target = write(tmp_path / "home/.app/settings.json", live)

    result = chezmoi_cat(tmp_path, repo, target)

    assert result.returncode == 0, result.stderr
    assert result.stdout == live


def test_modify_script_fails_without_writing_when_an_overlay_is_missing(
    tmp_path: Path,
    repo: Path,
) -> None:
    write(repo / "managed" / MODIFY_SCRIPT, f'{{{{- template "{_MODIFY_BODY}" . -}}}}\n')
    target = write(tmp_path / "home/.app/settings.json", '{"deny": ["Bash(tool *)"]}\n')

    result = chezmoi_cat(tmp_path, repo, target)

    assert result.returncode != 0
    assert "active source work has no checkout" in result.stderr


def test_uv_modify_script_composes_its_overlay_directory_into_the_live_config(
    tmp_path: Path,
    repo: Path,
) -> None:
    script = repo / "managed/dot_config/uv/modify_uv.toml"
    script.parent.mkdir(parents=True)
    shutil.copy(_REPO / "managed/dot_config/uv/modify_uv.toml", script)
    write(
        repo / "managed/dot_config/uv/uv.toml.d/10-core.toml",
        'exclude-newer = "3 days"\n\n[[index]]\nname = "pypi"\nurl = "https://pypi.example/simple"\n',
    )
    work = add_checkout(repo, "work")
    write(
        work / "dot_config/uv/uv.toml.d/50-work.toml",
        '[[index]]\nname = "internal"\nurl = "https://packages.example/simple"\nexplicit = true\n',
    )
    target = write(
        tmp_path / "home/.config/uv/uv.toml",
        'cache-dir = "/kept"\n',
    )

    result = chezmoi_cat(tmp_path, repo, target)

    assert result.returncode == 0, result.stderr
    assert tomlkit.parse(result.stdout).unwrap() == {
        "cache-dir": "/kept",
        "exclude-newer": "3 days",
        "index": [
            {"name": "pypi", "url": "https://pypi.example/simple"},
            {"name": "internal", "url": "https://packages.example/simple", "explicit": True},
        ],
    }
