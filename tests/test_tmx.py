import importlib.machinery
import importlib.util
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parent.parent / "managed/dot_local/bin/executable_tmx"
_loader = importlib.machinery.SourceFileLoader("tmx", str(_SCRIPT))
_spec = importlib.util.spec_from_loader("tmx", _loader)
assert _spec is not None
tmx = importlib.util.module_from_spec(_spec)
_loader.exec_module(tmx)


@pytest.fixture
def tmux_server(monkeypatch):
    binary = shutil.which("tmux")
    if binary is None:
        pytest.skip("tmux is required for session integration tests")
    run = subprocess.run
    # Keep the Unix socket path short and isolate the server from personal sessions.
    with tempfile.TemporaryDirectory(prefix="tmx-", dir="/tmp") as scratch:
        config = Path(scratch) / "tmux.conf"
        config.write_text("set -g default-shell /bin/sh\nset -g default-command 'sleep 60'\n")
        prefix = [binary, "-S", str(Path(scratch) / "socket"), "-f", str(config)]

        def command(*args, **kwargs):
            return run([*prefix, *args], **kwargs)

        def isolated_run(args, **kwargs):
            assert args[0] == "tmux"
            return command(*args[1:], **kwargs)

        monkeypatch.setattr(subprocess, "run", isolated_run)
        monkeypatch.delenv("TMUX", raising=False)
        try:
            yield command
        finally:
            command("kill-server", capture_output=True)


def test_current_directory_creates_session_and_attaches(tmux_server, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    attached = []
    monkeypatch.setattr("os.execvp", lambda file, args: attached.append((file, args)))

    assert tmx.main([]) == 0

    result = tmux_server("list-sessions", "-F", "#{session_name}", capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    name = "tmx" + str(tmp_path.resolve())
    assert result.stdout.strip() == name
    assert attached == [("tmux", ["tmux", "attach-session", "-t", "=" + name])]
    result = tmux_server(
        "display-message",
        "-p",
        "-t",
        "=" + name + ":",
        "#{pane_current_path}",
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == str(tmp_path.resolve())


@pytest.fixture
def connections(monkeypatch):
    calls = []
    monkeypatch.setattr("os.execvp", lambda file, args: calls.append((file, args)))
    return calls


def test_symlink_and_relative_path_reuse_session_without_changing_cwd(
    tmux_server, tmp_path, monkeypatch, connections
):
    project = tmp_path / "project"
    project.mkdir()
    (tmp_path / "link").symlink_to(project, target_is_directory=True)
    monkeypatch.chdir(tmp_path)
    assert tmx.main(["project"]) == 0
    before = tmux_server(
        "list-panes",
        "-a",
        "-F",
        "#{session_id}:#{pane_id}:#{pane_pid}",
        capture_output=True,
        text=True,
    ).stdout
    assert tmx.main(["link/../link"]) == 0
    after = tmux_server(
        "list-panes",
        "-a",
        "-F",
        "#{session_id}:#{pane_id}:#{pane_pid}",
        capture_output=True,
        text=True,
    ).stdout
    assert before == after
    assert connections[0] == connections[1]
    assert connections[0][1][-1] == "=tmx" + str(project.resolve())
    assert Path.cwd() == tmp_path.resolve()


@pytest.mark.parametrize("existing", [False, True])
def test_inside_tmux_switches_to_directory_session(
    tmux_server, tmp_path, monkeypatch, connections, existing
):
    if existing:
        assert tmx.main([str(tmp_path)]) == 0
    monkeypatch.setenv("TMUX", "isolated-test-client")
    assert tmx.main([str(tmp_path)]) == 0
    name = "tmx" + str(tmp_path.resolve())
    assert connections[-1] == ("tmux", ["tmux", "switch-client", "-t", "=" + name])
    result = tmux_server("list-sessions", "-F", "#{session_name}", capture_output=True, text=True)
    assert result.stdout.strip() == name


def test_directory_names_are_distinct_and_do_not_expand_tmux_formats(
    tmux_server, tmp_path, connections
):
    for dirname, encoded in [
        ("a.b", "a%2Eb"),
        ("a:b", "a%3Ab"),
        ("a_b", "a_b"),
        ("a%2Eb", "a%252Eb"),
        ("space #{pid} café", "space%20%23%7Bpid%7D%20caf%C3%A9"),
    ]:
        directory = tmp_path / dirname
        directory.mkdir()
        assert tmx.main([str(directory)]) == 0
        name = "tmx" + str(tmp_path.resolve()) + "/" + encoded
        assert connections[-1][1][-1] == "=" + name
        result = tmux_server(
            "display-message",
            "-p",
            "-t",
            "=" + name + ":",
            "#{pane_current_path}",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == str(directory.resolve())
    result = tmux_server("list-sessions", "-F", "#{session_name}", capture_output=True, text=True)
    assert len(result.stdout.splitlines()) == 5


@pytest.mark.parametrize("kind", ["missing", "file"])
def test_invalid_directory_fails_before_invoking_tmux(
    tmp_path, monkeypatch, capsys, connections, kind
):
    path = tmp_path / kind
    if kind == "file":
        path.touch()
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda *args, **_kwargs: calls.append(args))
    with pytest.raises(SystemExit) as error:
        tmx.main([str(path)])
    assert error.value.code == 2
    assert str(path) in capsys.readouterr().err
    assert calls == []
    assert connections == []


def test_missing_tmux_has_clear_error(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("PATH", str(tmp_path))
    assert tmx.main([str(tmp_path)]) == 127
    assert "tmux" in capsys.readouterr().err


def test_creation_failure_is_reported_without_attaching(tmp_path, monkeypatch, capsys, connections):
    def failed_command(args, **_kwargs):
        return subprocess.CompletedProcess(args, 1, "", "cannot create session\n")

    monkeypatch.setattr(subprocess, "run", failed_command)
    assert tmx.main([str(tmp_path)]) == 1
    assert "cannot create session" in capsys.readouterr().err
    assert connections == []


def test_concurrent_creator_still_attaches(tmux_server, tmp_path, monkeypatch, connections):
    isolated_run = subprocess.run

    def create_before_request(args, **kwargs):
        if args[1] == "new-session":
            # A competing caller creates the same session after the existence check.
            created = isolated_run(args, **kwargs)
            assert created.returncode == 0, created.stderr
        return isolated_run(args, **kwargs)

    monkeypatch.setattr(subprocess, "run", create_before_request)
    assert tmx.main([str(tmp_path)]) == 0
    name = "tmx" + str(tmp_path.resolve())
    assert connections == [("tmux", ["tmux", "attach-session", "-t", "=" + name])]
    result = tmux_server("list-sessions", "-F", "#{session_name}", capture_output=True, text=True)
    assert result.stdout.strip() == name
