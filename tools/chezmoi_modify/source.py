"""Safe source-repository file reads for modify scripts."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from chezmoi_modify.exceptions import ChezmoiModifyError


def read_source_text(relative_path: str) -> str:
    """Read a UTF-8 file below CHEZMOI_SOURCE_DIR."""
    return _source_path(relative_path).read_text(encoding="utf-8")


def read_source_template_text(relative_path: str) -> str:
    """Render a chezmoi template file below CHEZMOI_SOURCE_DIR."""
    source_dir = _source_dir()
    source_path = _source_path(relative_path)
    try:
        result = subprocess.run(  # noqa: S603
            [  # noqa: S607
                "chezmoi",
                "execute-template",
                "--source",
                str(source_dir),
                "--file",
                str(source_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        msg = "chezmoi command is not available to render source template"
        raise ChezmoiModifyError(msg) from error
    except subprocess.CalledProcessError as error:
        msg = f"source template could not be rendered: {error.stderr.strip()}"
        raise ChezmoiModifyError(msg) from error
    return result.stdout


def _source_path(relative_path: str) -> Path:
    source_dir = _source_dir()
    requested_path = Path(relative_path)
    if requested_path.is_absolute():
        msg = f"source path must be relative: {relative_path}"
        raise ChezmoiModifyError(msg)

    source_path = (source_dir / requested_path).resolve()
    if not source_path.is_relative_to(source_dir):
        msg = f"source path resolves outside CHEZMOI_SOURCE_DIR: {relative_path}"
        raise ChezmoiModifyError(msg)
    if not source_path.exists():
        msg = f"source file does not exist: {relative_path}"
        raise ChezmoiModifyError(msg)

    return source_path


def _source_dir() -> Path:
    chezmoi_source_dir = os.environ.get("CHEZMOI_SOURCE_DIR")
    if not chezmoi_source_dir:
        msg = "CHEZMOI_SOURCE_DIR is not set"
        raise ChezmoiModifyError(msg)
    return Path(chezmoi_source_dir).resolve()
