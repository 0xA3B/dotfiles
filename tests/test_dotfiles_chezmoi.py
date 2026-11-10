"""Smoke test of the dotfiles wrapper against a real chezmoi binary.

test_dotfiles.py fakes chezmoi; this test checks the parts the fake assumes, such as the
output of chezmoi source-path and chezmoi data. CI installs no chezmoi, so it skips there.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parent.parent / "managed/dot_local/bin/executable_dotfiles"

pytestmark = pytest.mark.skipif(shutil.which("chezmoi") is None, reason="chezmoi is not on PATH")


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)  # noqa: S603, S607


@pytest.fixture
def machine(tmp_path, monkeypatch):
    """A home directory whose chezmoi config names a primary source and one secondary."""
    home = tmp_path / "home"
    config = home / ".config"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")

    primary = tmp_path / "repo" / "managed"
    primary.mkdir(parents=True)
    (primary / "dot_primary").write_text("primary\n")

    origin = tmp_path / "work-origin"
    origin.mkdir()
    (origin / "dot_work").write_text("work\n")
    git(origin, "init", "--quiet")
    git(origin, "add", ".")
    git(origin, "-c", "user.name=T", "-c", "user.email=t@example.invalid", "commit", "-qm", "init")

    (config / "chezmoi").mkdir(parents=True)
    (config / "chezmoi" / "chezmoi.toml").write_text(
        f'sourceDir = "{primary}"\n\n[data.dotfiles_sources]\nwork = "{origin}"\n'
    )
    return home


def dotfiles(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [sys.executable, str(_SCRIPT), *args], capture_output=True, text=True, check=False
    )


def test_init_clones_and_applies_the_secondary_with_its_own_state(machine):
    result = dotfiles("init")

    assert result.returncode == 0, result.stderr
    assert (machine / ".work").read_text() == "work\n"
    assert (machine / ".config/chezmoi/chezmoistate-work.boltdb").is_file()


def test_aggregate_and_per_source_commands_act_on_the_cloned_secondary(machine):
    assert dotfiles("init").returncode == 0
    (machine / ".work").write_text("drift\n")

    status = dotfiles("status")
    managed = dotfiles("work", "managed")
    apply = dotfiles("apply", "--force")

    assert status.returncode == 0, status.stderr
    assert apply.returncode == 0, apply.stderr
    assert (machine / ".primary").read_text() == "primary\n"
    assert (machine / ".work").read_text() == "work\n"
    assert ".work" in status.stdout
    assert managed.stdout.split() == [".work"]


@pytest.mark.usefixtures("machine")
def test_per_source_flags_outvote_a_source_override(tmp_path):
    # chezmoi takes the last value of a repeated flag, and dotfiles appends its own.
    assert dotfiles("init").returncode == 0

    managed = dotfiles("work", f"--source={tmp_path / 'repo' / 'managed'}", "managed")

    assert managed.stdout.split() == [".work"], managed.stderr
