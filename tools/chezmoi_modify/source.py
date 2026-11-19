"""Safe source-repository file reads for modify scripts."""

from __future__ import annotations

import json
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
        return _chezmoi("execute-template", "--source", str(source_dir), "--file", str(source_path))
    except ChezmoiModifyError as error:
        msg = f"source template could not be rendered: {error}"
        raise ChezmoiModifyError(msg) from error


def read_overlay_directory(modify_script: str) -> list[tuple[str, str]]:
    """Read the overlay directory of a modify script from every source, in apply order.

    ``modify_script`` is the script's path below CHEZMOI_SOURCE_DIR, as chezmoi passes it
    in CHEZMOI_SOURCE_FILE. Its overlay directory sits beside it and is named after its
    target with a ``.d`` suffix: ``modify_private_settings.json`` reads
    ``settings.json.d/``. The primary source comes first, then the same path in each
    active secondary source, alphabetically by name; within a source, overlays sort by
    file name, and hidden files are skipped. A ``.tmpl`` overlay renders with its own
    source as the template source. Returns ``(label, text)`` pairs, where a label names
    the source and the overlay's path.

    Raises instead of skipping when an active secondary source has no checkout or no
    overlay directory, or an overlay cannot be read or rendered, because skipping an
    overlay would drop the settings it supplies from the target. A secondary source that
    supplies nothing for a target keeps the directory with only hidden files in it.
    """
    primary = _source_dir()
    script_path = _source_path(modify_script, must_exist=False)
    overlay_directory = str(Path(modify_script).parent / _overlay_directory_name(script_path.name))

    sources = [("personal", primary), *_active_secondary_sources(primary)]
    overlays: list[tuple[str, str]] = []
    for name, root in sources:
        try:
            paths = sorted((root / overlay_directory).iterdir())
        except FileNotFoundError:
            if root == primary:
                continue
            msg = (
                f"active source {name} has no {overlay_directory}; if it supplies no overlays for"
                " this target, commit the directory with only a hidden placeholder such as .keep"
            )
            raise ChezmoiModifyError(msg) from None
        except OSError as error:
            msg = f"overlay directory {name}:{overlay_directory} could not be listed: {error}"
            raise ChezmoiModifyError(msg) from error
        for path in paths:
            if path.name.startswith("."):
                continue
            label = f"{name}:{overlay_directory}/{path.name}"
            overlays.append((label, _read_overlay(root, path, label)))
    return overlays


def _source_path(relative_path: str, *, must_exist: bool = True) -> Path:
    source_dir = _source_dir()
    requested_path = Path(relative_path)
    if requested_path.is_absolute():
        msg = f"source path must be relative: {relative_path}"
        raise ChezmoiModifyError(msg)

    source_path = (source_dir / requested_path).resolve()
    if not source_path.is_relative_to(source_dir):
        msg = f"source path resolves outside CHEZMOI_SOURCE_DIR: {relative_path}"
        raise ChezmoiModifyError(msg)
    if must_exist and not source_path.exists():
        msg = f"source file does not exist: {relative_path}"
        raise ChezmoiModifyError(msg)

    return source_path


def _source_dir() -> Path:
    chezmoi_source_dir = os.environ.get("CHEZMOI_SOURCE_DIR")
    if not chezmoi_source_dir:
        msg = "CHEZMOI_SOURCE_DIR is not set"
        raise ChezmoiModifyError(msg)
    return Path(chezmoi_source_dir).resolve()


# chezmoi source attribute prefixes that can precede a modify script's target name.
_ATTRIBUTE_PREFIXES = ("modify_", "encrypted_", "private_", "readonly_", "executable_")


def _overlay_directory_name(script_name: str) -> str:
    name = script_name.removesuffix(".tmpl")
    for prefix in _ATTRIBUTE_PREFIXES:
        name = name.removeprefix(prefix)
    return f"{name}.d"


def _active_secondary_sources(primary: Path) -> list[tuple[str, Path]]:
    """List active secondary sources the way the dotfiles wrapper does: a non-empty URL."""
    registry = json.loads(
        _chezmoi(
            "execute-template", "--source", str(primary), '{{ get . "dotfiles_sources" | toJson }}'
        )
    )
    sources: list[tuple[str, Path]] = []
    for name in sorted(registry or {}):
        if not registry[name]:
            continue
        checkout = primary.parent / f"managed-{name}"
        if not (checkout / ".git").exists():
            msg = f"active source {name} has no checkout at {checkout}; run dotfiles init"
            raise ChezmoiModifyError(msg)
        root_file = checkout / ".chezmoiroot"
        root = (
            checkout / root_file.read_text(encoding="utf-8").strip()
            if root_file.exists()
            else checkout
        )
        sources.append((name, root.resolve()))
    return sources


def _read_overlay(root: Path, path: Path, label: str) -> str:
    if not path.resolve().is_relative_to(root):
        msg = f"overlay {label} resolves outside its source"
        raise ChezmoiModifyError(msg)
    try:
        if path.suffix == ".tmpl":
            return _chezmoi("execute-template", "--source", str(root), "--file", str(path))
        return path.read_text(encoding="utf-8")
    except (OSError, ChezmoiModifyError) as error:
        msg = f"overlay {label} could not be read: {error}"
        raise ChezmoiModifyError(msg) from error


def _chezmoi(*args: str) -> str:
    """Run chezmoi with the binary and config of the chezmoi run that started this script."""
    executable = os.environ.get("CHEZMOI_EXECUTABLE") or "chezmoi"
    config_file = os.environ.get("CHEZMOI_CONFIG_FILE")
    config_args = ["--config", config_file] if config_file else []
    try:
        result = subprocess.run(  # noqa: S603
            [executable, *config_args, *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        msg = "chezmoi command is not available"
        raise ChezmoiModifyError(msg) from error
    except subprocess.CalledProcessError as error:
        raise ChezmoiModifyError(error.stderr.strip()) from error
    return result.stdout
