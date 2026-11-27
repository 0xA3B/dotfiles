"""Shared pytest fixtures."""

import os
import subprocess

import pytest

# The variables that tie a Git command to one repository, such as GIT_DIR and GIT_INDEX_FILE.
# Git sets some of them when it runs a hook, so the pre-push test run inherits them. Without this
# fixture, a test's `git init` in a temporary directory would reinitialize the repository being
# pushed instead.
_REPOSITORY_ENV_VARS = subprocess.run(
    ["git", "rev-parse", "--local-env-vars"],  # noqa: S607
    check=True,
    capture_output=True,
    text=True,
).stdout.split()


@pytest.fixture(autouse=True)
def _isolate_git_from_the_calling_repository(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in _REPOSITORY_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    for name in list(os.environ):
        if name.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")):
            monkeypatch.delenv(name)
