import os
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

_SHIM = (
    Path(__file__).resolve().parent.parent
    / "managed"
    / "dot_local"
    / "bin"
    / "executable_update-all-unattended"
)


@pytest.fixture
def home(tmp_path: Path) -> Path:
    """A home directory whose ~/.local/bin holds the shim and stubs for the commands it runs.

    The tests limit PATH to the system directories, so the shim finds these stubs only through the
    PATH it builds itself, and a missing stub cannot fall through to a real update-all.
    """
    path = tmp_path / "home"
    bin_dir = path / ".local" / "bin"
    bin_dir.mkdir(parents=True)
    installed = bin_dir / "update-all-unattended"
    shutil.copyfile(_SHIM, installed)
    installed.chmod(0o755)
    write_stub(bin_dir, "route", "exit 0\n")
    write_stub(bin_dir, "osascript", 'printf \'%s\\n\' "$@" >>"$HOME/osascript.log"\n')
    write_stub(bin_dir, "update-all", 'printf "PATH=%s\\n" "$PATH"\necho updated\n')
    return path


def write_stub(bin_dir: Path, name: str, body: str) -> None:
    script = bin_dir / name
    script.write_text("#!/bin/sh\n" + body)
    script.chmod(0o755)


def run_shim(home: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ | {"HOME": str(home), "PATH": "/usr/bin:/bin"}
    return subprocess.run(  # noqa: S603
        [str(home / ".local" / "bin" / "update-all-unattended")],
        check=False,
        capture_output=True,
        env=environment,
        text=True,
    )


def read_log(home: Path) -> str:
    return (home / "Library" / "Logs" / "update-all.log").read_text()


def notifications(home: Path) -> list[str]:
    log = home / "osascript.log"
    return log.read_text().splitlines() if log.exists() else []


def test_a_clean_run_logs_the_output_and_sends_no_notification(home: Path) -> None:
    result = run_shim(home)

    assert result.returncode == 0, result.stderr
    assert "updated\n" in read_log(home)
    assert notifications(home) == []


def test_update_all_runs_with_the_user_tools_on_path(home: Path) -> None:
    run_shim(home)

    path_line = next(line for line in read_log(home).splitlines() if line.startswith("PATH="))
    entries = path_line.removeprefix("PATH=").split(":")
    assert entries[:5] == [
        f"{home}/.local/bin",
        f"{home}/.local/share/mise/shims",
        "/opt/homebrew/bin",
        "/opt/homebrew/sbin",
        "/usr/local/bin",
    ]


def test_a_failed_run_notifies_with_the_failed_steps_and_keeps_the_status(home: Path) -> None:
    write_stub(
        home / ".local" / "bin",
        "update-all",
        textwrap.dedent("""\
            printf 'Failed steps:\\n  Homebrew\\n  uv tools\\n' >&2
            exit 1
            """),
    )

    result = run_shim(home)

    assert result.returncode == 1
    assert notifications(home)[-2:] == [
        "Failed: Homebrew, uv tools",
        "See ~/Library/Logs/update-all.log",
    ]


def test_a_failure_without_a_step_list_notifies_with_the_exit_status(home: Path) -> None:
    write_stub(home / ".local" / "bin", "update-all", "exit 3\n")

    result = run_shim(home)

    assert result.returncode == 3
    assert notifications(home)[-2:] == [
        "update-all exited with status 3",
        "See ~/Library/Logs/update-all.log",
    ]


def test_each_run_replaces_the_previous_log(home: Path) -> None:
    run_shim(home)
    run_shim(home)

    assert read_log(home).count("update-all-unattended started") == 1
