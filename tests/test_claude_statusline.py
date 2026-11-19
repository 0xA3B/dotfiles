"""The Claude Code status line script, run with bash on status line JSON."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT = _ROOT / "managed/dot_local/bin/executable_claude-statusline"
_ANSI = re.compile(r"\x1b\[[0-9;]*m|\x1b\]8;;[^\a]*\a")

# Nerd Font glyphs the script prints, by code point
FOLDER = ""
MODEL = "\U000f0674"
COST = "\U000f01c1"
BRIEFCASE = ""
USER = ""


def pie(eighths: int) -> str:
    """Return the usage pie filled to `eighths`: md-circle_slice_1 through md-circle_slice_8."""
    return chr(0xF0A9D + eighths)


def status_line(tmp_path: Path, data: dict[str, object], *args: str) -> list[str]:
    """Run the script on `data` in a directory outside Git and return its lines without colors."""
    payload = {
        "workspace": {"project_dir": str(tmp_path / "proj"), "current_dir": str(tmp_path)},
        "model": {"id": "claude-opus-5-5", "display_name": "Claude Opus 5.5"},
        **data,
    }
    result = subprocess.run(  # noqa: S603
        ["bash", str(_SCRIPT), *args],  # noqa: S607
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
    )
    return _ANSI.sub("", result.stdout).split("\n")


def test_without_a_label_the_first_line_starts_at_the_project(tmp_path: Path) -> None:
    first, *_ = status_line(tmp_path, {})

    assert first == f"{FOLDER} proj via {MODEL} Opus 5.5"


@pytest.mark.parametrize(("label", "icon"), [("work", BRIEFCASE), ("personal", USER)])
def test_a_label_argument_leads_the_first_line(tmp_path: Path, label: str, icon: str) -> None:
    first, *_ = status_line(tmp_path, {}, label)

    assert first == f"{icon} {label} in {FOLDER} proj via {MODEL} Opus 5.5"


def test_the_model_shows_its_display_name_and_effort(tmp_path: Path) -> None:
    first, *_ = status_line(
        tmp_path,
        {
            "model": {"id": "provider-model-id", "display_name": "Claude Fable 5.2"},
            "effort": {"level": "high"},
        },
    )

    assert first.endswith(f"via {MODEL} Fable 5.2 · high")


def test_a_subscription_shows_its_rate_limit_windows_and_no_cost(tmp_path: Path) -> None:
    _, meters = status_line(
        tmp_path,
        {
            "cost": {"total_cost_usd": 3.5},
            "rate_limits": {
                "five_hour": {"used_percentage": 42, "resets_at": 0},
                "seven_day": {"used_percentage": 80.4, "resets_at": 0},
            },
        },
    )

    assert meters == f"5h {pie(3)} 42% │ 7d {pie(6)} 80%"


def test_a_subscription_window_may_be_absent_on_its_own(tmp_path: Path) -> None:
    _, meters = status_line(
        tmp_path,
        {
            "cost": {"total_cost_usd": 3.5},
            "rate_limits": {"seven_day": {"used_percentage": 10, "resets_at": 0}},
        },
    )

    assert meters == f"7d {pie(1)} 10%"


def test_api_billing_shows_the_session_cost(tmp_path: Path) -> None:
    _, meters = status_line(tmp_path, {"cost": {"total_cost_usd": 12.345}})

    assert meters == f"cost {COST} 12.35"


def test_no_cost_shows_before_the_first_response(tmp_path: Path) -> None:
    assert status_line(tmp_path, {"cost": {"total_cost_usd": 0}}) == [
        f"{FOLDER} proj via {MODEL} Opus 5.5"
    ]


def test_a_gateway_spend_limit_shows_beside_the_cost(tmp_path: Path) -> None:
    _, meters = status_line(
        tmp_path,
        {
            "cost": {"total_cost_usd": 1},
            "rate_limits": {
                "spend_limit": {
                    "used_percentage": 50,
                    "resets_at": 0,
                    "used_usd": 250,
                    "limit_usd": 500,
                    "period": "monthly",
                },
            },
        },
    )

    assert meters == f"cost {COST} 1.00 │ month {pie(4)} 50% $250.00/$500"


@pytest.mark.skipif(shutil.which("chezmoi") is None, reason="chezmoi is not on PATH")
@pytest.mark.parametrize(
    ("overlay", "work_machine", "command"),
    [
        ("private_dot_claude", False, "bash ~/.local/bin/claude-statusline"),
        ("private_dot_claude", True, "bash ~/.local/bin/claude-statusline work"),
        ("private_dot_claude-personal", True, "bash ~/.local/bin/claude-statusline personal"),
    ],
)
def test_core_labels_the_status_line_only_on_work_machines(
    tmp_path: Path, overlay: str, *, work_machine: bool, command: str
) -> None:
    template = _ROOT / "managed" / overlay / "settings.json.d/10-core.jsonc.tmpl"
    config = tmp_path / "chezmoi.toml"
    config.write_text("")
    rendered = subprocess.run(  # noqa: S603
        [  # noqa: S607
            "chezmoi",
            "execute-template",
            "--config",
            str(config),
            "--source",
            str(_ROOT / "managed"),
            "--override-data",
            json.dumps({"work_machine": work_machine}),
            "--file",
            str(template),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout

    assert f'"command": "{command}"' in rendered
