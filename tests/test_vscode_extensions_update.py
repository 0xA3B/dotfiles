import copy
import email.message
import gzip
import http.client
import importlib.machinery
import importlib.util
import io
import json
import subprocess
import time
import urllib.error
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

_SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "managed"
    / "dot_local"
    / "bin"
    / "executable_vscode-extensions-update"
)
_loader = importlib.machinery.SourceFileLoader("vscode_extensions_update", str(_SCRIPT))
_spec = importlib.util.spec_from_loader("vscode_extensions_update", _loader)
assert _spec is not None
veu = importlib.util.module_from_spec(_spec)
_loader.exec_module(veu)

NOW = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)
# Marketplace extensionquery flags: IncludeVersions and IncludeVersionProperties.
INCLUDE_VERSIONS = 0x1
INCLUDE_VERSION_PROPERTIES = 0x10


def release(version, *, age_hours, platform=None, engine="^1.90.0", prerelease=False):
    """Build one Marketplace version entry as the extensionquery API returns it."""
    properties = [{"key": "Microsoft.VisualStudio.Code.Engine", "value": engine}]
    if prerelease:
        properties.append({"key": "Microsoft.VisualStudio.Code.PreRelease", "value": "true"})
    entry = {
        "version": version,
        "lastUpdated": (NOW - timedelta(hours=age_hours)).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "properties": properties,
    }
    if platform is not None:
        entry["targetPlatform"] = platform
    return entry


class _FakeResponse:
    def __init__(self, body, headers=None):
        self._body = body
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._body


class _FakeMarketplace:
    """Stand-in for urllib's urlopen that answers extensionquery requests.

    Like the real API, it returns versions and their properties only when the
    request's flags ask for them. A failure that is bytes is sent as a
    gzip-labeled body.
    """

    def __init__(self, extensions, failures=None, *, gzip_body=False):
        self.extensions = extensions
        self.failures = {ext_id: list(errors) for ext_id, errors in (failures or {}).items()}
        self.gzip_body = gzip_body

    def __call__(self, request, **_kwargs):
        query = json.loads(request.data)
        ext_id = query["filters"][0]["criteria"][0]["value"]
        pending = self.failures.get(ext_id)
        if pending:
            failure = pending.pop(0)
            if isinstance(failure, bytes):
                return _FakeResponse(failure, {"Content-Encoding": "gzip"})
            raise failure
        found = []
        if ext_id in self.extensions:
            publisher, name = ext_id.split(".", 1)
            extension = {"publisher": {"publisherName": publisher}, "extensionName": name}
            if query["flags"] & INCLUDE_VERSIONS:
                versions = copy.deepcopy(self.extensions[ext_id])
                if not query["flags"] & INCLUDE_VERSION_PROPERTIES:
                    for entry in versions:
                        entry.pop("properties", None)
                extension["versions"] = versions
            found = [extension]
        body = json.dumps({"results": [{"extensions": found}]}).encode()
        if self.gzip_body:
            return _FakeResponse(gzip.compress(body), {"Content-Encoding": "gzip"})
        return _FakeResponse(body)


class _FakeCode:
    """Stand-in for the VS Code CLI that tracks installed extension versions."""

    def __init__(self, installed, version="1.144.0", broken=(), architecture="arm64"):
        self._installed = dict(installed)
        self._version = version
        self._broken = set(broken)
        self._architecture = architecture

    def version(self):
        return self._version

    def architecture(self):
        return self._architecture

    def installed(self):
        return dict(self._installed)

    def install(self, ext_id, version):
        if ext_id in self._broken:
            return False
        self._installed[ext_id] = version
        return True


def http_error(status):
    # An empty body keeps HTTPError from opening a temporary file that is never closed.
    return urllib.error.HTTPError(
        veu.QUERY_URL, status, "error", email.message.Message(), io.BytesIO()
    )


def run(argv, *, installed, marketplace, failures=None, gzip_body=False, broken=()):
    code = _FakeCode(installed, broken=broken)
    status = veu.main(
        argv,
        code=code,
        opener=_FakeMarketplace(marketplace, failures, gzip_body=gzip_body),
        now=NOW,
        target_platform="darwin-arm64",
        sleep=lambda _seconds: None,
    )
    return status, code.installed()


@pytest.fixture
def new_york_clock(monkeypatch):
    """Render local times in a zone that differs from UTC."""
    monkeypatch.setenv("TZ", "America/New_York")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


def test_installs_newer_version_past_the_cooldown(capsys):
    status, installed = run(
        [],
        installed={"pub.ext": "1.0.0"},
        marketplace={"pub.ext": [release("1.1.0", age_hours=80), release("1.0.0", age_hours=900)]},
    )

    out = capsys.readouterr().out
    assert status == 0
    assert installed == {"pub.ext": "1.1.0"}
    assert "Updated pub.ext 1.0.0 -> 1.1.0" in out
    assert "Held" not in out


@pytest.mark.parametrize(("age_hours", "expected"), [(72, "1.1.0"), (71, "1.0.0")])
def test_cooldown_ends_exactly_72_hours_after_publication(age_hours, expected):
    _, installed = run(
        [],
        installed={"pub.ext": "1.0.0"},
        marketplace={"pub.ext": [release("1.1.0", age_hours=age_hours)]},
    )

    assert installed == {"pub.ext": expected}


@pytest.mark.usefixtures("new_york_clock")
def test_holds_newer_version_inside_the_cooldown_until_it_ages(capsys):
    status, installed = run(
        [],
        installed={"pub.ext": "1.0.0"},
        marketplace={"pub.ext": [release("1.1.0", age_hours=20), release("1.0.0", age_hours=900)]},
    )

    assert status == 0
    assert installed == {"pub.ext": "1.0.0"}
    # Published 2026-10-31 16:00 UTC; 72 hours later is 2026-11-03 16:00 UTC, which is
    # 11:00 EST after daylight saving time ends on 2026-11-01.
    assert "Held pub.ext 1.1.0 until 2026-11-03 11:00 EST" in capsys.readouterr().out


def test_installs_aged_version_and_reports_newer_held_version(capsys):
    status, installed = run(
        [],
        installed={"pub.ext": "1.0.0"},
        marketplace={
            "pub.ext": [
                release("1.2.0", age_hours=20),
                release("1.1.0", age_hours=80),
                release("1.0.0", age_hours=900),
            ]
        },
    )

    out = capsys.readouterr().out
    assert status == 0
    assert installed == {"pub.ext": "1.1.0"}
    assert "Updated pub.ext 1.0.0 -> 1.1.0" in out
    assert "Held pub.ext 1.2.0 until" in out
    assert "Held pub.ext 1.1.0" not in out


@pytest.mark.parametrize("platform", [None, "universal", "darwin-arm64"])
def test_accepts_versions_built_for_this_platform_or_any(platform):
    _, installed = run(
        [],
        installed={"pub.ext": "1.0.0"},
        marketplace={"pub.ext": [release("1.1.0", age_hours=80, platform=platform)]},
    )

    assert installed == {"pub.ext": "1.1.0"}


def test_ignores_versions_built_only_for_other_platforms():
    _, installed = run(
        [],
        installed={"pub.ext": "1.0.0"},
        marketplace={
            "pub.ext": [
                release("1.1.0", age_hours=80, platform="linux-x64"),
                release("1.1.0", age_hours=80, platform="darwin-x64"),
            ]
        },
    )

    assert installed == {"pub.ext": "1.0.0"}


@pytest.mark.parametrize("other_platform", ["linux-x64", None])
@pytest.mark.parametrize("platform_build_first", [True, False])
def test_ages_a_version_by_this_platforms_build(other_platform, platform_build_first):
    # The darwin-arm64 build of 1.1.0 landed two days after the other build.
    builds = [
        release("1.1.0", age_hours=20, platform="darwin-arm64"),
        release("1.1.0", age_hours=80, platform=other_platform),
    ]
    _, installed = run(
        [],
        installed={"pub.ext": "1.0.0"},
        marketplace={"pub.ext": builds if platform_build_first else builds[::-1]},
    )

    assert installed == {"pub.ext": "1.0.0"}


def test_skips_pre_release_versions():
    _, installed = run(
        [],
        installed={"pub.ext": "1.0.0"},
        marketplace={
            "pub.ext": [
                release("1.3.0", age_hours=80, prerelease=True),
                release("1.1.0", age_hours=100),
            ]
        },
    )

    assert installed == {"pub.ext": "1.1.0"}


@pytest.mark.parametrize("engine", ["^1.146.0", "^1.146.x", ">=1.145.0"])
def test_skips_versions_that_need_a_newer_vscode(engine):
    # _FakeCode reports VS Code 1.144.0.
    _, installed = run(
        [],
        installed={"pub.ext": "1.0.0"},
        marketplace={
            "pub.ext": [
                release("1.2.0", age_hours=80, engine=engine),
                release("1.1.0", age_hours=100, engine=">=1.144.0"),
            ]
        },
    )

    assert installed == {"pub.ext": "1.1.0"}


@pytest.mark.parametrize("engine", ["*", "^1.x.x", "1.90.x", "^0.10.x", "^1.90.0-insider"])
def test_accepts_every_engine_form_vscode_accepts(engine):
    status, installed = run(
        [],
        installed={"pub.ext": "1.0.0"},
        marketplace={"pub.ext": [release("1.1.0", age_hours=80, engine=engine)]},
    )

    assert status == 0
    assert installed == {"pub.ext": "1.1.0"}


@pytest.mark.usefixtures("new_york_clock")
def test_keeps_an_installed_version_newer_than_the_cooldown_allows(capsys):
    status, installed = run(
        [],
        installed={"pub.ext": "1.2.0"},
        marketplace={"pub.ext": [release("1.2.0", age_hours=20), release("1.1.0", age_hours=80)]},
    )

    assert status == 0
    assert installed == {"pub.ext": "1.2.0"}
    expected = "Kept pub.ext 1.2.0, which is inside the cooldown until 2026-11-03 11:00 EST"
    assert expected in capsys.readouterr().out


def test_reports_nothing_for_an_installed_version_past_the_cooldown(capsys):
    status, installed = run(
        [],
        installed={"pub.ext": "1.1.0"},
        marketplace={"pub.ext": [release("1.1.0", age_hours=80)]},
    )

    assert status == 0
    assert installed == {"pub.ext": "1.1.0"}
    assert capsys.readouterr().out == ""


def test_skip_cooldown_installs_the_newest_compatible_version_now():
    _, installed = run(
        ["--skip-cooldown", "Pub.Ext"],
        installed={"pub.ext": "1.0.0", "other.ext": "1.0.0"},
        marketplace={
            "pub.ext": [
                release("1.4.0", age_hours=1, engine="^1.146.0"),
                release("1.3.0", age_hours=1, prerelease=True),
                release("1.2.0", age_hours=1),
                release("1.1.0", age_hours=80),
            ],
            "other.ext": [release("2.0.0", age_hours=1)],
        },
    )

    assert installed == {"pub.ext": "1.2.0", "other.ext": "1.0.0"}


def test_skip_cooldown_rejects_an_extension_that_is_not_installed(capsys):
    with pytest.raises(SystemExit) as exit_info:
        run(["--skip-cooldown", "missing.ext"], installed={"pub.ext": "1.0.0"}, marketplace={})

    assert exit_info.value.code == 2
    assert "--skip-cooldown: missing.ext is not installed" in capsys.readouterr().err


def test_dry_run_reports_updates_without_installing(capsys):
    status, installed = run(
        ["--dry-run"],
        installed={"pub.ext": "1.0.0"},
        marketplace={"pub.ext": [release("1.1.0", age_hours=80)]},
    )

    out = capsys.readouterr().out
    assert status == 0
    assert installed == {"pub.ext": "1.0.0"}
    assert "Would update pub.ext 1.0.0 -> 1.1.0" in out
    assert "Reload" not in out


def test_reminds_to_reload_after_installing(capsys):
    run(
        [],
        installed={"pub.ext": "1.0.0"},
        marketplace={"pub.ext": [release("1.1.0", age_hours=80)]},
    )

    assert "Reload" in capsys.readouterr().out


@pytest.mark.parametrize(
    "failure",
    [
        http_error(503),
        http_error(429),
        urllib.error.URLError("connection reset"),
        TimeoutError("timed out"),
        http.client.IncompleteRead(b"partial", 100),
        gzip.compress(b'{"results": [{"extensions": []}]}' * 20)[:20],
    ],
    ids=["503", "429", "url-error", "timeout", "incomplete-read", "truncated-gzip"],
)
def test_retries_transient_failures(failure):
    status, installed = run(
        [],
        installed={"pub.ext": "1.0.0"},
        marketplace={"pub.ext": [release("1.1.0", age_hours=80)]},
        failures={"pub.ext": [failure, failure]},
    )

    assert status == 0
    assert installed == {"pub.ext": "1.1.0"}


def test_backs_off_between_retries():
    sleeps = []
    error = http.client.IncompleteRead(b"partial", 100)

    veu.main(
        [],
        code=_FakeCode({"pub.ext": "1.0.0"}),
        opener=_FakeMarketplace(
            {"pub.ext": [release("1.1.0", age_hours=80)]}, {"pub.ext": [error, error]}
        ),
        now=NOW,
        target_platform="darwin-arm64",
        sleep=sleeps.append,
    )

    assert sleeps == [1.0, 2.0]


def test_skips_an_extension_whose_query_keeps_failing_and_updates_the_rest(capsys):
    error = http.client.IncompleteRead(b"partial", 100)
    status, installed = run(
        [],
        installed={"bad.ext": "1.0.0", "pub.ext": "1.0.0"},
        marketplace={
            "bad.ext": [release("1.1.0", age_hours=80)],
            "pub.ext": [release("1.1.0", age_hours=80)],
        },
        failures={"bad.ext": [error, error, error]},
    )

    assert status == 1
    assert installed == {"bad.ext": "1.0.0", "pub.ext": "1.1.0"}
    assert "bad.ext" in capsys.readouterr().err


def test_does_not_retry_a_client_error():
    status, installed = run(
        [],
        installed={"pub.ext": "1.0.0"},
        marketplace={"pub.ext": [release("1.1.0", age_hours=80)]},
        failures={"pub.ext": [http_error(400)]},
    )

    assert status == 1
    assert installed == {"pub.ext": "1.0.0"}


def _without_last_updated(entry):
    del entry["lastUpdated"]


def _with_naive_last_updated(entry):
    entry["lastUpdated"] = "2026-10-28T12:00:00"


def _with_null_properties(entry):
    entry["properties"] = None


def _without_engine(entry):
    entry["properties"] = []


@pytest.mark.parametrize(
    "corrupt",
    [_without_last_updated, _with_naive_last_updated, _with_null_properties, _without_engine],
)
def test_skips_an_extension_with_malformed_version_data(capsys, corrupt):
    entry = release("1.1.0", age_hours=80)
    corrupt(entry)
    status, installed = run(
        [],
        installed={"pub.ext": "1.0.0", "other.ext": "1.0.0"},
        marketplace={
            "pub.ext": [entry, release("1.0.5", age_hours=100)],
            "other.ext": [release("1.1.0", age_hours=80)],
        },
    )

    assert status == 1
    assert installed == {"pub.ext": "1.0.0", "other.ext": "1.1.0"}
    assert "pub.ext" in capsys.readouterr().err


def test_ignores_version_strings_the_marketplace_no_longer_accepts():
    status, installed = run(
        [],
        installed={"pub.ext": "1.0.0"},
        marketplace={
            "pub.ext": [
                release("1.2.0-beta", age_hours=80),
                release("1.1.0", age_hours=80),
                release("0.1.0-beta", age_hours=900),
            ]
        },
    )

    assert status == 0
    assert installed == {"pub.ext": "1.1.0"}


def test_ignores_malformed_entries_older_than_the_installed_version():
    old_entry = release("0.9.0", age_hours=900)
    del old_entry["lastUpdated"]
    status, installed = run(
        [],
        installed={"pub.ext": "1.0.0"},
        marketplace={"pub.ext": [old_entry, release("1.1.0", age_hours=80)]},
    )

    assert status == 0
    assert installed == {"pub.ext": "1.1.0"}


def test_notes_an_extension_missing_from_the_marketplace(capsys):
    status, installed = run(
        [],
        installed={"local.vsix": "0.1.0", "pub.ext": "1.0.0"},
        marketplace={"pub.ext": [release("1.1.0", age_hours=80)]},
    )

    assert status == 0
    assert installed == {"local.vsix": "0.1.0", "pub.ext": "1.1.0"}
    assert "local.vsix" in capsys.readouterr().out


def test_reads_gzip_encoded_responses():
    _, installed = run(
        [],
        installed={"pub.ext": "1.0.0"},
        marketplace={"pub.ext": [release("1.1.0", age_hours=80)]},
        gzip_body=True,
    )

    assert installed == {"pub.ext": "1.1.0"}


def test_reports_a_failed_install(capsys):
    status, _ = run(
        [],
        installed={"pub.ext": "1.0.0"},
        marketplace={"pub.ext": [release("1.1.0", age_hours=80)]},
        broken={"pub.ext"},
    )

    captured = capsys.readouterr()
    assert status == 1
    assert "pub.ext" in captured.err
    assert "Reload" not in captured.out


def test_fails_when_the_code_cli_is_unavailable(monkeypatch, capsys):
    def missing_code(*_args, **_kwargs):
        raise FileNotFoundError(2, "No such file or directory", "code")

    monkeypatch.setattr(veu.subprocess, "run", missing_code)

    status = veu.main([], opener=_FakeMarketplace({}), now=NOW, target_platform="darwin-arm64")

    assert status == 1
    assert "cannot read the VS Code installation" in capsys.readouterr().err


def test_code_cli_reads_version_architecture_and_installed_extensions(monkeypatch):
    outputs = {
        "--version": "1.144.0\n2c33b50b16c472efe58357d1d2a8a5414bc23fbf\narm64\n",
        "--list-extensions": "Anthropic.claude-code@2.1.314\nmkhl.shfmt@1.5.2\n",
    }

    def fake_run(argv, **_kwargs):
        return subprocess.CompletedProcess(argv, 0, stdout=outputs[argv[1]], stderr="")

    monkeypatch.setattr(veu.subprocess, "run", fake_run)
    cli = veu.CodeCLI()

    assert cli.version() == "1.144.0"
    assert cli.architecture() == "arm64"
    assert cli.installed() == {"anthropic.claude-code": "2.1.314", "mkhl.shfmt": "1.5.2"}


@pytest.mark.parametrize(("returncode", "succeeded"), [(0, True), (1, False)])
def test_code_cli_installs_the_pinned_version(monkeypatch, capsys, returncode, succeeded):
    commands = []

    def fake_run(argv, **_kwargs):
        commands.append(argv)
        return subprocess.CompletedProcess(argv, returncode, stdout="", stderr="install output\n")

    monkeypatch.setattr(veu.subprocess, "run", fake_run)

    assert veu.CodeCLI().install("pub.ext", "1.1.0") is succeeded
    # Without @version, `code --install-extension` installs the newest release,
    # which would bypass the cooldown.
    assert commands == [["code", "--install-extension", "pub.ext@1.1.0"]]
    assert ("install output" in capsys.readouterr().err) is not succeeded


@pytest.mark.parametrize(
    ("system", "architecture", "expected"),
    [
        ("Darwin", "arm64", "darwin-arm64"),
        ("Darwin", "x64", "darwin-x64"),
        ("Linux", "x64", "linux-x64"),
        ("Linux", "arm64", "linux-arm64"),
    ],
)
def test_detects_the_target_platform_from_vscodes_architecture(
    monkeypatch, system, architecture, expected
):
    monkeypatch.setattr(veu.platform, "system", lambda: system)

    assert veu.detect_target_platform(architecture) == expected


@pytest.mark.parametrize(("system", "architecture"), [("Windows", "x64"), ("Darwin", "ia32")])
def test_rejects_an_unsupported_target_platform(monkeypatch, system, architecture):
    monkeypatch.setattr(veu.platform, "system", lambda: system)

    with pytest.raises(veu.MarketplaceError, match="unsupported VS Code platform"):
        veu.detect_target_platform(architecture)


def test_chooses_builds_for_the_architecture_vscode_reports(monkeypatch):
    # An x64 VS Code on Apple silicon runs x64 builds, whatever python3's architecture is.
    monkeypatch.setattr(veu.platform, "system", lambda: "Darwin")
    code = _FakeCode({"pub.ext": "1.0.0"}, architecture="x64")

    veu.main(
        [],
        code=code,
        opener=_FakeMarketplace(
            {
                "pub.ext": [
                    release("1.2.0", age_hours=80, platform="darwin-arm64"),
                    release("1.1.0", age_hours=80, platform="darwin-x64"),
                ]
            }
        ),
        now=NOW,
        sleep=lambda _seconds: None,
    )

    assert code.installed() == {"pub.ext": "1.1.0"}


@pytest.mark.parametrize(
    "version_output", ["", "1.144.0\n2c33b50b16c472efe58357d1d2a8a5414bc23fbf\n"]
)
def test_fails_when_code_version_output_is_incomplete(monkeypatch, capsys, version_output):
    def fake_run(argv, **_kwargs):
        return subprocess.CompletedProcess(argv, 0, stdout=version_output, stderr="")

    monkeypatch.setattr(veu.subprocess, "run", fake_run)

    status = veu.main([], opener=_FakeMarketplace({}), now=NOW)

    assert status == 1
    assert "cannot read the VS Code installation" in capsys.readouterr().err
