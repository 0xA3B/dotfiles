import os
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

_BIN_DIR = Path(__file__).resolve().parent.parent / "managed" / "dot_local" / "bin"
_SHIMS = ("update-all", "update-brew", "update-mise")
_TOOLS = ("brew", "mise", "uv", "code", "update-vscode-extensions")


@pytest.fixture
def bin_dir(tmp_path: Path) -> Path:
    """Install the shims under test next to logging stubs for the tools they run."""
    path = tmp_path / "bin"
    path.mkdir()
    for shim in _SHIMS:
        installed = path / shim
        shutil.copyfile(_BIN_DIR / f"executable_{shim}", installed)
        installed.chmod(0o755)
    for tool in _TOOLS:
        stub(path, tool)
    return path


def stub(bin_dir: Path, name: str, *, fail_on: str | None = None) -> None:
    """Write a stub that logs its name and arguments and fails when its first argument is fail_on.

    Pass fail_on="" to fail a call without arguments.

    The stub uses only shell builtins, so the tests can limit PATH to bin_dir and no real tool runs.
    """
    fail = f'if [ "${{1:-}}" = "{fail_on}" ]; then exit 1; fi\n' if fail_on is not None else ""
    script = bin_dir / name
    script.write_text(
        textwrap.dedent(f"""\
            #!/bin/sh
            printf '%s\\n' "{name}${{*:+ $*}}" >>"$UPDATE_LOG"
            """)
        + fail
    )
    script.chmod(0o755)


def run_update_all(
    bin_dir: Path, tmp_path: Path
) -> tuple[subprocess.CompletedProcess[str], list[str]]:
    log = tmp_path / "calls.log"
    log.touch()
    environment = os.environ | {"PATH": str(bin_dir), "UPDATE_LOG": str(log)}
    result = subprocess.run(  # noqa: S603
        [str(bin_dir / "update-all")],
        check=False,
        capture_output=True,
        env=environment,
        text=True,
    )
    return result, log.read_text().splitlines()


def test_update_all_runs_the_work_hook_before_every_update(bin_dir: Path, tmp_path: Path) -> None:
    stub(bin_dir, "update-all-work")

    result, calls = run_update_all(bin_dir, tmp_path)

    assert result.returncode == 0, result.stderr
    assert calls == [
        "update-all-work",
        "brew update",
        "brew upgrade --no-ask",
        "brew cleanup",
        "mise upgrade --global",
        "mise reshim",
        "uv tool upgrade --all",
        "update-vscode-extensions",
    ]


@pytest.mark.parametrize(
    ("tool", "skipped_call"),
    [
        ("brew", "brew update"),
        ("mise", "mise upgrade --global"),
        ("uv", "uv tool upgrade --all"),
        ("code", "update-vscode-extensions"),
    ],
)
def test_update_all_skips_a_step_whose_tool_is_missing(
    bin_dir: Path, tmp_path: Path, tool: str, skipped_call: str
) -> None:
    (bin_dir / tool).unlink()

    result, calls = run_update_all(bin_dir, tmp_path)

    assert result.returncode == 0, result.stderr
    assert f"{tool} not found; skipping" in result.stderr
    assert skipped_call not in calls


def test_update_all_says_nothing_about_an_absent_work_hook(bin_dir: Path, tmp_path: Path) -> None:
    result, _ = run_update_all(bin_dir, tmp_path)

    assert result.returncode == 0, result.stderr
    assert "update-all-work" not in result.stdout + result.stderr


def test_update_all_finishes_every_step_and_reports_the_failed_ones(
    bin_dir: Path, tmp_path: Path
) -> None:
    stub(bin_dir, "update-all-work", fail_on="")
    stub(bin_dir, "brew", fail_on="update")
    stub(bin_dir, "mise", fail_on="upgrade")
    stub(bin_dir, "uv", fail_on="tool")
    stub(bin_dir, "update-vscode-extensions", fail_on="")

    result, calls = run_update_all(bin_dir, tmp_path)

    assert result.returncode == 1
    assert calls == [
        "update-all-work",
        "brew update",
        "mise upgrade --global",
        "uv tool upgrade --all",
        "update-vscode-extensions",
    ]
    assert result.stderr.endswith(
        "Failed steps:\n  Work steps\n  Homebrew\n  mise tools\n  uv tools\n  VS Code extensions\n"
    )
