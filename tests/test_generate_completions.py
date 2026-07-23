import importlib.machinery
import importlib.util
import json
from pathlib import Path

import pytest

_SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "managed"
    / "dot_local"
    / "bin"
    / "executable_generate-completions"
)
_loader = importlib.machinery.SourceFileLoader("generate_completions", str(_SCRIPT))
_spec = importlib.util.spec_from_loader("generate_completions", _loader)
assert _spec is not None
gc = importlib.util.module_from_spec(_spec)
_loader.exec_module(gc)


@pytest.fixture
def config_home(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    (tmp_path / "generate-completions").mkdir()
    return tmp_path


def write_config(config_home, filename, commands):
    path = config_home / "generate-completions" / filename
    path.write_text(json.dumps({"commands": commands}))
    return path


def test_load_commands_merges_local_over_base(config_home):
    write_config(
        config_home,
        "config.json",
        {
            "chezmoi": {"generator": ["chezmoi", "completion", "{shell}"]},
            "dropped": {"generator": ["dropped"]},
            "kept": {"generator": ["kept"]},
        },
    )
    write_config(
        config_home,
        "config.local.json",
        {
            "chezmoi": {"generator": ["work-chezmoi", "completion", "{shell}"]},
            "dropped": None,
            "work-tool": {"generator": ["work-tool", "completions", "{shell}"]},
        },
    )

    commands = gc.load_commands()

    assert sorted(commands) == ["chezmoi", "kept", "work-tool"]
    assert commands["chezmoi"]["generator"][0] == "work-chezmoi"


@pytest.mark.usefixtures("config_home")
def test_load_commands_without_any_config_fails():
    with pytest.raises(gc.ConfigError, match="no config found"):
        gc.load_commands()


def test_load_commands_rejects_malformed_config(config_home):
    path = config_home / "generate-completions" / "config.json"
    path.write_text(json.dumps({"commands": ["not", "a", "mapping"]}))

    with pytest.raises(gc.ConfigError, match="commands"):
        gc.load_commands()


def test_default_targets_follow_shell_conventions(config_home):
    entry = {"generator": ["tool"]}

    fish = gc.resolve_target("tool", entry, "fish")
    zsh = gc.resolve_target("tool", entry, "zsh")

    assert fish == config_home / "fish" / "completions" / "tool.fish"
    assert zsh == config_home / "zsh" / "completions" / "_tool"


def test_target_override_expands_tilde(config_home, monkeypatch):
    monkeypatch.setenv("HOME", str(config_home))
    entry = {"generator": ["tool"], "targets": {"fish": "~/custom/tool.fish"}}

    assert gc.resolve_target("tool", entry, "fish") == config_home / "custom" / "tool.fish"


def test_generator_substitutes_shell_placeholder():
    entry = {"generator": ["tool", "--completions={shell}"]}

    assert gc.command_generator("tool", entry, "fish") == ["tool", "--completions=fish"]


def test_generate_shell_writes_target(config_home):
    entry = {"generator": ["sh", "-c", "echo {shell}"]}

    assert gc.generate_shell("tool", entry, "fish") is True
    target = config_home / "fish" / "completions" / "tool.fish"
    assert target.read_text() == "fish\n"


@pytest.mark.usefixtures("config_home")
def test_generate_shell_missing_binary_skips(capsys):
    entry = {"generator": ["definitely-not-on-path-12345"]}

    assert gc.generate_shell("tool", entry, "fish") is False
    assert "not found in PATH" in capsys.readouterr().err


def test_generate_shell_discards_empty_output(config_home):
    entry = {"generator": ["sh", "-c", "true"]}

    assert gc.generate_shell("tool", entry, "fish") is False
    completions_dir = config_home / "fish" / "completions"
    assert list(completions_dir.iterdir()) == []


def test_generate_shell_discards_failed_generator(config_home):
    entry = {"generator": ["sh", "-c", "echo partial; exit 1"]}

    assert gc.generate_shell("tool", entry, "fish") is False
    completions_dir = config_home / "fish" / "completions"
    assert list(completions_dir.iterdir()) == []


def test_main_generates_for_all_shells(config_home):
    write_config(
        config_home,
        "config.json",
        {"tool": {"generator": ["sh", "-c", "echo {shell}"]}},
    )

    assert gc.main([]) == 0
    assert (config_home / "fish" / "completions" / "tool.fish").read_text() == "fish\n"
    assert (config_home / "zsh" / "completions" / "_tool").read_text() == "zsh\n"


def test_main_rejects_unsupported_command(config_home, capsys):
    write_config(config_home, "config.json", {"tool": {"generator": ["tool"]}})

    assert gc.main(["nope"]) == 1
    assert "Unsupported command 'nope'" in capsys.readouterr().err


def test_main_reports_config_errors_for_bad_entries(config_home, capsys):
    write_config(config_home, "config.json", {"tool": {"generator": "not-a-list"}})

    assert gc.main(["tool"]) == 1
    assert "generator" in capsys.readouterr().err
