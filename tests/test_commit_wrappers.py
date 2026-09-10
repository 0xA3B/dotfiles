import json
import os
import selectors
import shlex
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

_BIN_DIR = Path(__file__).resolve().parent.parent / "managed" / "dot_local" / "bin"
_CODEX_COMMIT = _BIN_DIR / "executable_codex-commit"
_CLAUDE_COMMIT = _BIN_DIR / "executable_claude-commit"


def write_executable(path: Path, content: str) -> None:
    path.write_text(textwrap.dedent(content))
    path.chmod(0o755)


def emit_json_lines(*events: dict[str, object]) -> str:
    lines = (
        shlex.quote(json.dumps(event, separators=(",", ":"), sort_keys=True)) for event in events
    )
    return "\n".join(f"printf '%s\\n' {line}" for line in lines)


@pytest.fixture
def fake_bin(tmp_path: Path) -> Path:
    path = tmp_path / "bin"
    path.mkdir()
    return path


def run_wrapper(
    script: Path,
    fake_bin: Path,
    install_dir: Path,
    *,
    standard_input: str | None = None,
    **environment: str,
) -> subprocess.CompletedProcess[str]:
    installed_script = install_dir / script.name.removeprefix("executable_")
    shutil.copyfile(script, installed_script)
    installed_script.chmod(0o755)
    command_environment = os.environ | environment
    command_environment["PATH"] = f"{fake_bin}{os.pathsep}{command_environment['PATH']}"
    return subprocess.run(  # noqa: S603
        [str(installed_script)],
        check=False,
        capture_output=True,
        env=command_environment,
        input=standard_input,
        text=True,
    )


def test_codex_commit_streams_only_progress_and_final_result(
    fake_bin: Path, tmp_path: Path
) -> None:
    stream = emit_json_lines(
        {
            "type": "item.completed",
            "item": {"id": "1", "type": "reasoning", "text": "private detail"},
        },
        {
            "type": "item.completed",
            "item": {
                "id": "2",
                "type": "agent_message",
                "text": "Progress: planned two commits",
            },
        },
        {
            "type": "item.completed",
            "item": {
                "id": "3",
                "type": "command_execution",
                "command": "git status",
                "status": "completed",
            },
        },
        {
            "type": "item.completed",
            "item": {
                "id": "4",
                "type": "agent_message",
                "text": "Progress: created the first commit",
            },
        },
        {
            "type": "item.completed",
            "item": {"id": "5", "type": "agent_message", "text": "Created two commits."},
        },
        {"type": "turn.completed", "usage": {}},
    )
    write_executable(
        fake_bin / "codex",
        f"""
        #!/usr/bin/env bash
        set -euo pipefail

        [[ " $* " == *" --json "* ]]
        [[ " $* " != *" --ephemeral "* ]]
        [[ "$*" == *"Progress: "* ]]
        [[ " $* " == *" after determining the commit plan "* ]]
        [[ " $* " == *" after each successful commit. "* ]]
        [[ " $* " == *" Do not narrate routine commands"* ]]
        [[ " $* " == *" do not begin the final response "* ]]
        [[ " $* " != *" During longer runs "* ]]

        result_file=""
        while (( $# > 0 )); do
          case "$1" in
            -o|--output-last-message)
              result_file=$2
              shift 2
              ;;
            *) shift ;;
          esac
        done

        {stream}
        printf 'routine codex diagnostic\n' >&2
        printf 'Created two commits.\n' >"$result_file"
        """,
    )

    result = run_wrapper(_CODEX_COMMIT, fake_bin, tmp_path)

    assert result.returncode == 0
    assert result.stdout == "Created two commits.\n"
    assert result.stderr == ("Progress: planned two commits\nProgress: created the first commit\n")


def test_codex_commit_does_not_forward_standard_input(fake_bin: Path, tmp_path: Path) -> None:
    write_executable(
        fake_bin / "codex",
        """
        #!/usr/bin/env bash
        set -euo pipefail

        result_file=""
        while (( $# > 0 )); do
          case "$1" in
            -o|--output-last-message)
              result_file=$2
              shift 2
              ;;
            *) shift ;;
          esac
        done

        if IFS= read -r unexpected_input; then
          printf 'unexpected stdin: %s\n' "$unexpected_input" >&2
          exit 9
        fi
        printf 'No changes to commit.\n' >"$result_file"
        """,
    )

    result = run_wrapper(
        _CODEX_COMMIT,
        fake_bin,
        tmp_path,
        standard_input="caller input must be ignored\n",
    )

    assert result.returncode == 0
    assert result.stdout == "No changes to commit.\n"
    assert result.stderr == ""


@pytest.mark.parametrize(
    "event",
    [
        {"type": "turn.failed", "error": {"message": "commit hook failed"}},
        {"type": "error", "message": "commit hook failed"},
        {
            "type": "item.completed",
            "item": {"id": "1", "type": "error", "message": "commit hook failed"},
        },
    ],
)
def test_codex_commit_preserves_failure_status_and_diagnostics(
    fake_bin: Path, tmp_path: Path, event: dict[str, object]
) -> None:
    stream = emit_json_lines(event)
    write_executable(
        fake_bin / "codex",
        f"""
        #!/usr/bin/env bash
        {stream}
        printf 'codex diagnostic\n' >&2
        exit 7
        """,
    )

    result = run_wrapper(_CODEX_COMMIT, fake_bin, tmp_path)

    assert result.returncode == 7
    assert result.stdout == ""
    assert "commit hook failed" in result.stderr
    assert "codex diagnostic" in result.stderr


def test_claude_commit_streams_brief_progress_and_final_result(
    fake_bin: Path, tmp_path: Path
) -> None:
    stream = emit_json_lines(
        {
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "private detail"}]},
        },
        {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "name": "SendUserMessage",
                        "input": {"message": "Progress: planned two commits"},
                    }
                ]
            },
        },
        {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "name": "Bash",
                        "input": {"command": "git status"},
                    }
                ]
            },
        },
        {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "name": "SendUserMessage",
                        "input": {"message": "Progress: created the first commit"},
                    }
                ]
            },
        },
        {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "name": "SendUserMessage",
                        "input": {"message": "Created two commits."},
                    }
                ]
            },
        },
        {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": "fallback result",
        },
    )
    write_executable(
        fake_bin / "claude",
        f"""
        #!/usr/bin/env bash
        set -euo pipefail

        [[ " $* " == *" --brief "* ]]
        [[ " $* " == *" --output-format stream-json "* ]]
        [[ " $* " == *" --verbose "* ]]
        [[ "$*" == *"Progress: "* ]]
        [[ " $* " == *" after determining the commit plan "* ]]
        [[ " $* " == *" after each successful commit. "* ]]
        [[ " $* " == *" Do not narrate routine commands"* ]]
        [[ " $* " == *" do not begin the final response "* ]]
        [[ " $* " != *" During longer runs "* ]]

        {stream}
        printf 'routine claude diagnostic\n' >&2
        """,
    )

    result = run_wrapper(_CLAUDE_COMMIT, fake_bin, tmp_path)

    assert result.returncode == 0
    assert result.stdout == "Created two commits.\n"
    assert result.stderr == ("Progress: planned two commits\nProgress: created the first commit\n")


def test_claude_commit_preserves_failure_status_and_diagnostics(
    fake_bin: Path, tmp_path: Path
) -> None:
    stream = emit_json_lines(
        {
            "type": "result",
            "subtype": "error_during_execution",
            "is_error": True,
            "result": "commit hook failed",
        }
    )
    write_executable(
        fake_bin / "claude",
        f"""
        #!/usr/bin/env bash
        {stream}
        printf 'claude diagnostic\n' >&2
        exit 8
        """,
    )

    result = run_wrapper(_CLAUDE_COMMIT, fake_bin, tmp_path)

    assert result.returncode == 8
    assert result.stdout == ""
    assert "commit hook failed" in result.stderr
    assert "claude diagnostic" in result.stderr


@pytest.mark.parametrize(
    "event",
    [
        {"type": "turn.failed", "error": {"message": "commit hook failed"}},
        {"type": "error", "message": "commit hook failed"},
    ],
)
def test_codex_commit_fails_on_terminal_error_event_when_agent_exits_zero(
    fake_bin: Path, tmp_path: Path, event: dict[str, object]
) -> None:
    stream = emit_json_lines(event)
    write_executable(
        fake_bin / "codex",
        f"""
        #!/usr/bin/env bash
        set -euo pipefail

        result_file=""
        while (( $# > 0 )); do
          case "$1" in
            -o|--output-last-message)
              result_file=$2
              shift 2
              ;;
            *) shift ;;
          esac
        done

        printf 'Created one commit.\n' >"$result_file"
        {stream}
        """,
    )

    result = run_wrapper(_CODEX_COMMIT, fake_bin, tmp_path)

    assert result.returncode != 0
    assert result.stdout == ""
    assert "commit hook failed" in result.stderr


@pytest.mark.parametrize(
    ("item", "expected_diagnostic"),
    [
        (
            {"id": "1", "type": "error", "message": "unstable feature warning"},
            "codex: unstable feature warning\n",
        ),
        ({"id": "1", "type": "error"}, "codex: Codex warning\n"),
    ],
)
def test_codex_commit_treats_item_error_as_recoverable_when_agent_exits_zero(
    fake_bin: Path,
    tmp_path: Path,
    item: dict[str, object],
    expected_diagnostic: str,
) -> None:
    stream = emit_json_lines(
        {"type": "item.completed", "item": item},
        {"type": "turn.completed", "usage": {}},
    )
    write_executable(
        fake_bin / "codex",
        f"""
        #!/usr/bin/env bash
        set -euo pipefail

        result_file=""
        while (( $# > 0 )); do
          case "$1" in
            -o|--output-last-message)
              result_file=$2
              shift 2
              ;;
            *) shift ;;
          esac
        done

        printf 'Created one commit.\n' >"$result_file"
        {stream}
        """,
    )

    result = run_wrapper(_CODEX_COMMIT, fake_bin, tmp_path)

    assert result.returncode == 0
    assert result.stdout == "Created one commit.\n"
    assert result.stderr == expected_diagnostic


def test_claude_commit_fails_on_terminal_error_event_when_agent_exits_zero(
    fake_bin: Path, tmp_path: Path
) -> None:
    stream = emit_json_lines(
        {
            "type": "result",
            "subtype": "error_during_execution",
            "is_error": True,
            "result": "commit hook failed",
        }
    )
    write_executable(
        fake_bin / "claude",
        f"""
        #!/usr/bin/env bash
        {stream}
        """,
    )

    result = run_wrapper(_CLAUDE_COMMIT, fake_bin, tmp_path)

    assert result.returncode != 0
    assert result.stdout == ""
    assert "commit hook failed" in result.stderr


def test_claude_commit_uses_result_when_no_brief_final_message(
    fake_bin: Path, tmp_path: Path
) -> None:
    stream = emit_json_lines(
        {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "name": "SendUserMessage",
                        "input": {"message": "Progress: planned one commit"},
                    }
                ]
            },
        },
        {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": "Created one commit.",
        },
    )
    write_executable(
        fake_bin / "claude",
        f"""
        #!/usr/bin/env bash
        {stream}
        """,
    )

    result = run_wrapper(_CLAUDE_COMMIT, fake_bin, tmp_path)

    assert result.returncode == 0
    assert result.stdout == "Created one commit.\n"
    assert result.stderr == "Progress: planned one commit\n"


@pytest.mark.parametrize(
    ("script", "command", "diagnostic"),
    [
        (_CODEX_COMMIT, "codex", "codex diagnostic"),
        (_CLAUDE_COMMIT, "claude", "claude diagnostic"),
    ],
)
def test_commit_wrapper_reports_renderer_failure_after_successful_agent(
    fake_bin: Path,
    tmp_path: Path,
    script: Path,
    command: str,
    diagnostic: str,
) -> None:
    write_executable(
        fake_bin / command,
        f"""
        #!/usr/bin/env bash
        printf '{{malformed json\n'
        printf '{diagnostic}\n' >&2
        """,
    )

    result = run_wrapper(script, fake_bin, tmp_path)

    assert result.returncode != 0
    assert result.stdout == ""
    assert diagnostic in result.stderr


@pytest.mark.parametrize(
    ("script", "command"),
    [
        (_CODEX_COMMIT, "codex"),
        (_CLAUDE_COMMIT, "claude"),
    ],
)
def test_commit_wrapper_rejects_non_object_stream_event(
    fake_bin: Path,
    tmp_path: Path,
    script: Path,
    command: str,
) -> None:
    write_executable(
        fake_bin / command,
        """
        #!/usr/bin/env bash
        printf '42\n'
        printf 'agent diagnostic\n' >&2
        """,
    )

    result = run_wrapper(script, fake_bin, tmp_path)

    assert result.returncode != 0
    assert result.stdout == ""
    assert "expected a JSON object stream event" in result.stderr
    assert "agent diagnostic" in result.stderr


@pytest.mark.parametrize(
    ("script", "command", "agent_status"),
    [
        (_CODEX_COMMIT, "codex", 7),
        (_CLAUDE_COMMIT, "claude", 8),
    ],
)
def test_commit_wrapper_prefers_agent_status_when_renderer_also_fails(
    fake_bin: Path,
    tmp_path: Path,
    script: Path,
    command: str,
    agent_status: int,
) -> None:
    write_executable(
        fake_bin / command,
        f"""
        #!/usr/bin/env bash
        printf '{{malformed json\n'
        printf 'agent diagnostic\n' >&2
        exit {agent_status}
        """,
    )

    result = run_wrapper(script, fake_bin, tmp_path)

    assert result.returncode == agent_status
    assert result.stdout == ""
    assert "agent diagnostic" in result.stderr


@pytest.mark.parametrize(
    ("script", "command", "agent_status", "invalid_event"),
    [
        (_CODEX_COMMIT, "codex", 7, "{malformed json"),
        (
            _CODEX_COMMIT,
            "codex",
            7,
            '{"type":"item.completed","item":{"type":"agent_message","text":42}}',
        ),
        (_CODEX_COMMIT, "codex", 7, "42"),
        (_CLAUDE_COMMIT, "claude", 8, "{malformed json"),
        (
            _CLAUDE_COMMIT,
            "claude",
            8,
            '{"type":"assistant","message":{"content":[42]}}',
        ),
        (_CLAUDE_COMMIT, "claude", 8, "42"),
    ],
)
def test_commit_wrapper_drains_stream_after_renderer_failure(
    fake_bin: Path,
    tmp_path: Path,
    script: Path,
    command: str,
    agent_status: int,
    invalid_event: str,
) -> None:
    quoted_event = shlex.quote(invalid_event)
    write_executable(
        fake_bin / command,
        f"""
        #!/usr/bin/env bash
        set -euo pipefail

        printf '%s\n' {quoted_event}
        for ((index = 0; index < 10000; index++)); do
          printf '{{"type":"ignored","index":%d}}\n' "$index"
        done
        printf 'agent diagnostic after sustained output\n' >&2
        exit {agent_status}
        """,
    )

    result = run_wrapper(script, fake_bin, tmp_path)

    assert result.returncode == agent_status
    assert result.stdout == ""
    expected_error = (
        "expected a JSON object stream event"
        if invalid_event == "42"
        else "invalid JSON stream event"
    )
    assert expected_error in result.stderr
    assert "agent diagnostic after sustained output" in result.stderr


@pytest.mark.parametrize("failure_mode", ["agent", "renderer"])
def test_codex_commit_suppresses_candidate_result_on_failure(
    fake_bin: Path, tmp_path: Path, failure_mode: str
) -> None:
    failure = "exit 7" if failure_mode == "agent" else "printf '{malformed json\\n'"
    write_executable(
        fake_bin / "codex",
        f"""
        #!/usr/bin/env bash
        set -euo pipefail

        result_file=""
        while (( $# > 0 )); do
          case "$1" in
            -o|--output-last-message)
              result_file=$2
              shift 2
              ;;
            *) shift ;;
          esac
        done

        printf 'Created one commit.\n' >"$result_file"
        {failure}
        """,
    )

    result = run_wrapper(_CODEX_COMMIT, fake_bin, tmp_path)

    assert result.returncode != 0
    assert result.stdout == ""


def test_claude_commit_suppresses_final_result_when_agent_later_fails(
    fake_bin: Path, tmp_path: Path
) -> None:
    stream = emit_json_lines(
        {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": "Created one commit.",
        }
    )
    write_executable(
        fake_bin / "claude",
        f"""
        #!/usr/bin/env bash
        {stream}
        printf 'claude diagnostic\n' >&2
        exit 8
        """,
    )

    result = run_wrapper(_CLAUDE_COMMIT, fake_bin, tmp_path)

    assert result.returncode == 8
    assert result.stdout == ""
    assert "claude diagnostic" in result.stderr


def test_claude_commit_suppresses_final_result_on_trailing_renderer_failure(
    fake_bin: Path, tmp_path: Path
) -> None:
    stream = emit_json_lines(
        {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": "Created one commit.",
        }
    )
    write_executable(
        fake_bin / "claude",
        f"""
        #!/usr/bin/env bash
        {stream}
        printf '{{malformed json\n'
        """,
    )

    result = run_wrapper(_CLAUDE_COMMIT, fake_bin, tmp_path)

    assert result.returncode != 0
    assert result.stdout == ""
    assert "invalid JSON stream event" in result.stderr


@pytest.mark.parametrize("script", [_CODEX_COMMIT, _CLAUDE_COMMIT])
def test_commit_wrapper_declares_bash_interpreter(script: Path) -> None:
    assert script.read_text().splitlines()[0] == "#!/usr/bin/env bash"


@pytest.mark.parametrize(
    ("script", "command"),
    [
        (_CODEX_COMMIT, "codex"),
        (_CLAUDE_COMMIT, "claude"),
    ],
)
def test_commit_wrapper_streams_progress_before_agent_exits(
    fake_bin: Path,
    tmp_path: Path,
    script: Path,
    command: str,
) -> None:
    progress = "Progress: planned one commit"
    release_file = tmp_path / "release-agent"
    if command == "codex":
        progress_stream = emit_json_lines(
            {
                "type": "item.completed",
                "item": {"id": "1", "type": "agent_message", "text": progress},
            }
        )
        final_stream = emit_json_lines({"type": "turn.completed", "usage": {}})
        fake_command = f"""
            #!/usr/bin/env bash
            set -euo pipefail

            result_file=""
            while (( $# > 0 )); do
              case "$1" in
                -o|--output-last-message)
                  result_file=$2
                  shift 2
                  ;;
                *) shift ;;
              esac
            done

            {progress_stream}
            while [[ ! -e "$RELEASE_FILE" ]]; do sleep 0.01; done
            {final_stream}
            printf 'Created one commit.\n' >"$result_file"
        """
    else:
        progress_stream = emit_json_lines(
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {
                            "type": "tool_use",
                            "name": "SendUserMessage",
                            "input": {"message": progress},
                        }
                    ]
                },
            }
        )
        final_stream = emit_json_lines(
            {
                "type": "result",
                "subtype": "success",
                "is_error": False,
                "result": "Created one commit.",
            }
        )
        fake_command = f"""
            #!/usr/bin/env bash
            set -euo pipefail

            {progress_stream}
            while [[ ! -e "$RELEASE_FILE" ]]; do sleep 0.01; done
            {final_stream}
        """

    write_executable(fake_bin / command, fake_command)
    installed_script = tmp_path / script.name.removeprefix("executable_")
    shutil.copyfile(script, installed_script)
    installed_script.chmod(0o755)
    environment = os.environ | {
        "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
        "RELEASE_FILE": str(release_file),
    }
    process = subprocess.Popen(  # noqa: S603
        [str(installed_script)],
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert process.stderr is not None
    selector = selectors.DefaultSelector()
    selector.register(process.stderr, selectors.EVENT_READ)

    try:
        assert selector.select(timeout=3), "progress was not streamed before the agent exited"
        assert process.stderr.readline() == f"{progress}\n"
        assert process.poll() is None
        release_file.touch()
        stdout, stderr = process.communicate(timeout=5)
    finally:
        release_file.touch(exist_ok=True)
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        selector.close()

    assert process.returncode == 0
    assert stdout == "Created one commit.\n"
    assert stderr == ""
