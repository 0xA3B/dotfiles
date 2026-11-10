"""Behavior of the dotfiles wrapper, which applies the primary and secondary chezmoi sources.

Quoted requirements come from the multi-source design handoff; docs/adr/0001 records the
decision.
CI has no chezmoi binary, so a fake subprocess.run stands in for chezmoi and git.
"""

import importlib.machinery
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parent.parent / "managed/dot_local/bin/executable_dotfiles"
_loader = importlib.machinery.SourceFileLoader("dotfiles", str(_SCRIPT))
_spec = importlib.util.spec_from_loader("dotfiles", _loader)
assert _spec is not None
dotfiles = importlib.util.module_from_spec(_spec)
_loader.exec_module(dotfiles)

URL = "https://git.example.invalid/dotfiles-work.git"


class _FakeTools:
    """Stand-in for chezmoi and git that records every mutating call.

    Calls name their source by the --source checkout, or "personal" without one.
    """

    def __init__(self, root: Path, data: dict[str, object]) -> None:
        self.root = root
        self.data = data
        self.data_after_init: dict[str, object] | None = None
        self.exit_codes: dict[str, int] = {}
        self.clone_files: dict[str, str] = {}
        self.clone_exit = 0
        self.calls: list[list[str]] = []

    def __call__(self, args, **_kwargs):
        args = list(args)
        if args == ["chezmoi", "source-path"]:
            return subprocess.CompletedProcess(args, 0, f"{self.root / 'managed'}\n", "")
        if args == ["chezmoi", "data", "--format", "json"]:
            return subprocess.CompletedProcess(args, 0, json.dumps(self.data), "")
        self.calls.append(args)
        if args[:2] == ["git", "clone"]:
            if self.clone_exit == 0:
                checkout = Path(args[3])
                (checkout / ".git").mkdir(parents=True)
                for name, text in self.clone_files.items():
                    (checkout / name).write_text(text)
            return subprocess.CompletedProcess(args, self.clone_exit)
        # chezmoi takes the last --source, so the fake does too.
        sources = [arg.removeprefix("--source=") for arg in args if arg.startswith("--source=")]
        source = Path(sources[-1]).name.removeprefix("managed-") if sources else "personal"
        if source == "personal" and args[1] == "init" and self.data_after_init is not None:
            self.data = self.data_after_init
        return subprocess.CompletedProcess(args, self.exit_codes.get(source, 0))


@pytest.fixture
def config_home(tmp_path, monkeypatch):
    config = tmp_path / "config"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config))
    return config


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    (root / "managed").mkdir(parents=True)
    return root


def checkout(repo: Path, name: str) -> Path:
    path = repo / f"managed-{name}"
    (path / ".git").mkdir(parents=True)
    return path


@pytest.fixture
def tools(repo, config_home, monkeypatch):
    del config_home
    fake = _FakeTools(repo, {"dotfiles_sources": {"work": URL}})
    monkeypatch.setattr(subprocess, "run", fake)
    return fake


def secondary(repo: Path, config_home: Path, name: str, *args: str) -> list[str]:
    return [
        "chezmoi",
        *args,
        f"--persistent-state={config_home / 'chezmoi' / f'chezmoistate-{name}.boltdb'}",
        f"--source={repo / f'managed-{name}'}",
    ]


def test_apply_runs_personal_then_each_secondary_with_its_own_source_and_state(
    tools, repo, config_home
):
    # "chezmoi --source <repo>/managed-<name> --persistent-state
    # ~/.config/chezmoi/chezmoistate-<name>.boltdb"; "personal first".
    checkout(repo, "work")

    assert dotfiles.main(["apply"]) == 0

    assert tools.calls == [["chezmoi", "apply"], secondary(repo, config_home, "work", "apply")]


def test_aggregate_verbs_forward_flags_to_every_source(tools, repo, config_home):
    # "Aggregate verbs init, update, apply, diff, status: forward flags (-n, -v, ...)".
    checkout(repo, "work")

    assert dotfiles.main(["apply", "-n", "--verbose", "--force"]) == 0

    assert tools.calls == [
        ["chezmoi", "apply", "-n", "--verbose", "--force"],
        secondary(repo, config_home, "work", "apply", "-n", "--verbose", "--force"),
    ]


@pytest.mark.parametrize("arg", ["~/.gitconfig", "--exclude=scripts", "-nv", "-Dnone"], ids=str)
def test_aggregate_verbs_reject_other_arguments(tools, repo, arg, capsys):
    # "reject positional target paths". Other flags may take values or differ by subcommand.
    checkout(repo, "work")

    assert dotfiles.main(["apply", "-n", arg, "--bad"]) == 2

    assert tools.calls == []
    err = capsys.readouterr().err
    assert f"got {arg!r}" in err
    assert "dotfiles <source>" in err


def test_secondaries_run_alphabetically_after_personal(tools, repo, config_home):
    # "run personal then secondaries alphabetically".
    tools.data = {"dotfiles_sources": {"work": URL, "alpha": URL}}
    checkout(repo, "work")
    checkout(repo, "alpha")

    assert dotfiles.main(["status"]) == 0

    assert tools.calls == [
        ["chezmoi", "status"],
        secondary(repo, config_home, "alpha", "status"),
        secondary(repo, config_home, "work", "status"),
    ]


@pytest.mark.parametrize("data", [{}, {"dotfiles_sources": {}}], ids=["no-key", "no-sources"])
def test_machine_without_secondary_sources_runs_personal_only(tools, data):
    tools.data = data

    assert dotfiles.main(["apply"]) == 0

    assert tools.calls == [["chezmoi", "apply"]]


def test_checkout_without_active_entry_is_skipped_with_a_warning(tools, repo, capsys):
    # "A source is active when its URL is non-empty." "Warn about a managed-* checkout with no
    # active entry and skip it."
    tools.data = {"dotfiles_sources": {"work": ""}}
    checkout(repo, "work")
    checkout(repo, "old")

    assert dotfiles.main(["apply"]) == 0

    assert tools.calls == [["chezmoi", "apply"]]
    err = capsys.readouterr().err
    assert "dotfiles: skipping managed-old: no active dotfiles_sources entry" in err
    assert "dotfiles: skipping managed-work: no active dotfiles_sources entry" in err


@pytest.mark.parametrize("verb", ["init", "update", "apply"])
def test_mutating_verb_stops_when_personal_fails(tools, repo, verb, capsys):
    # "init, update, apply: if personal fails, stop, run no secondary, exit nonzero".
    checkout(repo, "work")
    tools.exit_codes["personal"] = 1

    assert dotfiles.main([verb]) == 1

    assert tools.calls == [["chezmoi", verb]]
    assert capsys.readouterr().err.splitlines()[-1] == f"dotfiles: personal: {verb} failed (exit 1)"


def test_failed_personal_init_clones_nothing(tools):
    # "init, update, apply: if personal fails, stop, run no secondary".
    tools.exit_codes["personal"] = 1

    assert dotfiles.main(["init"]) == 1

    assert tools.calls == [["chezmoi", "init"]]


def test_failing_secondary_does_not_stop_the_others(tools, repo, config_home, capsys):
    # "A failing secondary does not stop the others." "Every run that had failures ends with one
    # summary line per failed source, such as `dotfiles: work: update failed (exit 1)`".
    tools.data = {"dotfiles_sources": {"work": URL, "alpha": URL}}
    checkout(repo, "work")
    checkout(repo, "alpha")
    tools.exit_codes["alpha"] = 3

    assert dotfiles.main(["update"]) == 1

    assert tools.calls == [
        ["chezmoi", "update"],
        secondary(repo, config_home, "alpha", "update"),
        secondary(repo, config_home, "work", "update"),
    ]
    assert capsys.readouterr().err.splitlines()[-1] == "dotfiles: alpha: update failed (exit 3)"


@pytest.mark.parametrize("verb", ["diff", "status"])
def test_read_only_verb_continues_past_personal_failure(tools, repo, config_home, verb, capsys):
    # "diff, status: read-only, so continue past any failure."
    checkout(repo, "work")
    tools.exit_codes["personal"] = 1
    tools.exit_codes["work"] = 1

    assert dotfiles.main([verb]) == 1

    assert tools.calls == [["chezmoi", verb], secondary(repo, config_home, "work", verb)]
    assert capsys.readouterr().err.splitlines()[-2:] == [
        f"dotfiles: personal: {verb} failed (exit 1)",
        f"dotfiles: work: {verb} failed (exit 1)",
    ]


@pytest.mark.parametrize("verb", ["apply", "diff", "status"])
def test_active_source_without_checkout_fails_and_points_at_init(tools, verb, capsys):
    assert dotfiles.main([verb]) == 1

    assert tools.calls == [["chezmoi", verb]]
    assert capsys.readouterr().err.splitlines()[-1] == (
        f"dotfiles: work: {verb} failed (not cloned; run dotfiles init)"
    )


@pytest.mark.parametrize("fmt", ["toml", "yaml", "json", "jsonc"])
def test_secondary_shipping_a_config_template_is_refused(tools, repo, fmt, capsys):
    # "refuse to run any verb or passthrough against a secondary source whose root contains
    # .chezmoi.<format>.tmpl (toml, yaml, json, jsonc), with an error naming the file."
    (checkout(repo, "work") / f".chezmoi.{fmt}.tmpl").write_text("")

    assert dotfiles.main(["apply"]) == 1

    assert tools.calls == [["chezmoi", "apply"]]
    err = capsys.readouterr().err
    assert f"managed-work/.chezmoi.{fmt}.tmpl" in err
    assert err.splitlines()[-1] == f"dotfiles: work: apply failed (ships .chezmoi.{fmt}.tmpl)"


def test_init_reads_sources_after_personal_init_then_clones_and_applies(tools, repo, config_home):
    # "run chezmoi init (no args; picks up new *Once prompts) ... Then for each active source
    # without <dir>/.git: git clone <url> <dir>, run the config-template guard, then
    # chezmoi --source <dir> --persistent-state <state> apply".
    tools.data = {}
    tools.data_after_init = {"dotfiles_sources": {"work": URL}}

    assert dotfiles.main(["init"]) == 0

    assert tools.calls == [
        ["chezmoi", "init"],
        ["git", "clone", URL, str(repo / "managed-work")],
        secondary(repo, config_home, "work", "apply"),
    ]


def test_init_is_idempotent(tools, repo):
    # "Idempotent: a second run prompts and clones nothing."
    checkout(repo, "work")

    assert dotfiles.main(["init"]) == 0

    assert tools.calls == [["chezmoi", "init"]]


def test_init_retries_a_clone_that_left_an_empty_directory(tools, repo):
    # "A failed chezmoi init clone leaves an empty directory; test for <dir>/.git".
    (repo / "managed-work").mkdir()

    assert dotfiles.main(["init"]) == 0

    assert ["git", "clone", URL, str(repo / "managed-work")] in tools.calls


def test_init_guards_a_fresh_clone_before_applying_it(tools, repo, capsys):
    # "Do not use chezmoi init --apply <url>: it would render a shipped config template before
    # the guard runs."
    tools.clone_files = {".chezmoi.toml.tmpl": ""}

    assert dotfiles.main(["init"]) == 1

    assert tools.calls == [["chezmoi", "init"], ["git", "clone", URL, str(repo / "managed-work")]]
    assert capsys.readouterr().err.splitlines()[-1] == (
        "dotfiles: work: init failed (ships .chezmoi.toml.tmpl)"
    )


def test_failed_clone_is_reported(tools, capsys):
    tools.clone_exit = 128

    assert dotfiles.main(["init"]) == 1

    assert capsys.readouterr().err.splitlines()[-1] == (
        "dotfiles: work: init failed (clone exit 128)"
    )


def test_update_clones_missing_sources_then_updates_every_source(tools, repo, config_home):
    # "update runs the clone step before updating."
    tools.data = {"dotfiles_sources": {"work": URL, "alpha": URL}}
    checkout(repo, "alpha")

    assert dotfiles.main(["update", "-v"]) == 0

    assert tools.calls == [
        ["chezmoi", "update", "-v"],
        secondary(repo, config_home, "alpha", "update", "-v"),
        ["git", "clone", URL, str(repo / "managed-work")],
        secondary(repo, config_home, "work", "update", "-v"),
    ]


def test_passthrough_sets_source_and_state_only(tools, repo, config_home):
    # "Passthrough dotfiles <name> <chezmoi args...>: sets --source and --persistent-state only.
    # Works for a present checkout even when unconfigured."
    tools.data = {}
    checkout(repo, "work")

    assert dotfiles.main(["work", "diff", "~/.config/fish/work/env.fish"]) == 0

    assert tools.calls == [
        secondary(repo, config_home, "work", "diff", "~/.config/fish/work/env.fish")
    ]


def test_passthrough_runs_the_config_template_guard(tools, repo, capsys):
    (checkout(repo, "work") / ".chezmoi.jsonc.tmpl").write_text("")

    assert dotfiles.main(["work", "apply"]) == 1

    assert tools.calls == []
    assert "managed-work/.chezmoi.jsonc.tmpl" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (["work", "purge"], "refusing purge"),
        (["work", "--config", "other.toml", "purge"], "refusing purge"),
        (["work", "init"], "use dotfiles init"),
        (["work", "-v", "init", "--purge"], "use dotfiles init"),
        (["work", "--config", "other.toml", "init"], "use dotfiles init"),
        (["work", "apply", "--", "--source=/elsewhere"], "refusing --"),
        (["work", "apply", "--init"], "refusing --init"),
        (["work", "apply", "--init=true"], "refusing --init"),
        (["personal", "apply"], "use chezmoi"),
        (["missing", "apply"], "no checkout at"),
        (["-x", "apply"], "invalid source name"),
        ([".hidden", "apply"], "invalid source name"),
        (["../managed-work", "apply"], "invalid source name"),
        (["work/../x", "apply"], "invalid source name"),
        (["work.x", "apply"], "invalid source name"),
        ([], "usage"),
    ],
    ids=[
        "purge",
        "purge-after-a-flag-value",
        "init",
        "init-after-a-flag",
        "init-after-a-flag-value",
        "end-of-flags",
        "init-flag",
        "init-flag-with-value",
        "personal",
        "missing-checkout",
        "leading-dash",
        "leading-dot",
        "escapes-the-repo",
        "escapes-after-a-valid-start",
        "invalid-tail",
        "no-arguments",
    ],
)
def test_passthrough_usage_errors(tools, repo, argv, message, capsys):
    # "Refuses purge with a clear error. Personal is not addressable (dotfiles personal is an
    # error; use chezmoi)." init would clone and prompt outside dotfiles init.
    checkout(repo, "work")

    assert dotfiles.main(argv) == 2

    assert tools.calls == []
    assert message in capsys.readouterr().err


@pytest.mark.parametrize("name", ["../x", "work/../x"])
def test_registry_name_that_escapes_the_repo_fails_that_source(tools, name, capsys):
    tools.data = {"dotfiles_sources": {name: URL}}

    assert dotfiles.main(["apply"]) == 1

    assert tools.calls == [["chezmoi", "apply"]]
    assert capsys.readouterr().err.splitlines()[-1] == (
        f"dotfiles: {name}: apply failed (invalid source name)"
    )


@pytest.mark.parametrize("flag", ["-h", "--help"])
def test_help_prints_usage(tools, flag, capsys):
    assert dotfiles.main([flag]) == 0

    assert tools.calls == []
    assert "usage: dotfiles" in capsys.readouterr().out


@pytest.mark.parametrize("flag", ["-n", "--dry-run"])
@pytest.mark.parametrize("verb", ["init", "update"])
def test_dry_run_skips_cloning(tools, verb, flag, capsys):
    assert dotfiles.main([verb, flag]) == 0

    assert tools.calls == [["chezmoi", verb, flag]]
    assert "dotfiles: work: dry run skips cloning managed-work" in capsys.readouterr().err


def test_init_forwards_flags_to_the_fresh_clone_apply(tools, repo, config_home):
    assert dotfiles.main(["init", "-v", "--force"]) == 0

    assert tools.calls == [
        ["chezmoi", "init", "-v", "--force"],
        ["git", "clone", URL, str(repo / "managed-work")],
        secondary(repo, config_home, "work", "apply", "-v", "--force"),
    ]


def test_passthrough_returns_chezmoi_exit_code(tools, repo):
    checkout(repo, "work")
    tools.exit_codes["work"] = 3

    assert dotfiles.main(["work", "apply"]) == 3


def test_missing_chezmoi_is_reported(monkeypatch, capsys):
    def missing(args, **_kwargs):
        raise FileNotFoundError(2, "No such file or directory", args[0])

    monkeypatch.setattr(subprocess, "run", missing)

    assert dotfiles.main(["apply"]) == 127

    assert capsys.readouterr().err.strip() == "dotfiles: chezmoi was not found on PATH"


def test_failed_registry_query_is_reported(tools, monkeypatch, capsys):
    def failing_data(args, **kwargs):
        if args[:2] == ["chezmoi", "data"]:
            if kwargs.get("check"):
                raise subprocess.CalledProcessError(1, args, "", "chezmoi: config error\n")
            return subprocess.CompletedProcess(args, 1, "", "chezmoi: config error\n")
        return tools(args, **kwargs)

    monkeypatch.setattr(subprocess, "run", failing_data)

    assert dotfiles.main(["apply"]) == 1

    assert capsys.readouterr().err.strip() == (
        "dotfiles: chezmoi data --format json failed: chezmoi: config error"
    )


def test_failed_apply_after_a_fresh_clone_points_at_apply(tools, capsys):
    # A rerun of init skips the existing checkout, so only apply recovers it.
    tools.exit_codes["work"] = 1

    assert dotfiles.main(["init"]) == 1

    assert capsys.readouterr().err.splitlines()[-1] == (
        "dotfiles: work: init failed (apply exit 1; fix it, then run dotfiles apply)"
    )


@pytest.mark.parametrize(
    "override",
    [["--source=/elsewhere"], ["-S", "/elsewhere"], ["--persistent-state=x.boltdb"]],
    ids=["long", "short", "state"],
)
def test_passthrough_source_and_state_outvote_a_user_override(tools, repo, config_home, override):
    # "sets --source and --persistent-state"; chezmoi takes the last value of a repeated flag.
    checkout(repo, "work")

    assert dotfiles.main(["work", *override, "apply"]) == 0

    assert tools.calls == [secondary(repo, config_home, "work", *override, "apply")]


def test_config_template_under_chezmoiroot_is_refused(tools, repo, capsys):
    # chezmoi reads the config template from the directory that .chezmoiroot names.
    source = checkout(repo, "work")
    (source / ".chezmoiroot").write_text("home\n")
    (source / "home").mkdir()
    (source / "home" / ".chezmoi.toml.tmpl").write_text("")

    assert dotfiles.main(["work", "apply"]) == 1

    assert tools.calls == []
    assert "managed-work/home/.chezmoi.toml.tmpl" in capsys.readouterr().err
