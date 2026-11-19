#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.14,<3.15"
# ///
"""Compose a JSONC target's overlay directory from every source and apply it.

A modify script uses this body through a one-line template that includes this file
by name, and chezmoi renders this file as a template, so it must not contain template
delimiters. The script's overlay directory holds the managed overlays:
``modify_private_settings.json.tmpl`` reads ``settings.json.d/`` beside it in the
primary source and in each active secondary source. Design:
docs/adr/0002-primary-source-composes-overlay-directories.md.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def add_helper_path() -> None:
    """Add the repo helper library to sys.path."""
    chezmoi_source_dir = os.environ.get("CHEZMOI_SOURCE_DIR")
    if chezmoi_source_dir is None:
        sys.exit("modify_jsonc_overlay_directory: CHEZMOI_SOURCE_DIR is not set")
    sys.path.insert(0, str(Path(chezmoi_source_dir).parent / "tools"))


add_helper_path()

from chezmoi_modify.exceptions import ChezmoiModifyError
from chezmoi_modify.jsonc import compose_jsonc_overlays, merge_jsonc_overlay
from chezmoi_modify.source import read_overlay_directory


def main() -> None:
    """Merge the composed overlays into the live target read from standard input."""
    modify_script = os.environ.get("CHEZMOI_SOURCE_FILE")
    if not modify_script:
        sys.exit("modify_jsonc_overlay_directory: CHEZMOI_SOURCE_FILE is not set")
    managed = compose_jsonc_overlays(read_overlay_directory(modify_script))
    # Array order across overlays is an artifact of composition, so a live array that
    # holds the same strings keeps its order and the file is not rewritten.
    result = merge_jsonc_overlay(
        sys.stdin.read(),
        managed,
        unordered_string_arrays=True,
        ensure_ascii=False,
    )
    for diagnostic in result.diagnostics:
        print(f"{diagnostic.severity}: {diagnostic.message}", file=sys.stderr)
    sys.stdout.write(result.text)


if __name__ == "__main__":
    try:
        main()
    except ChezmoiModifyError as error:
        sys.exit(f"{os.environ.get('CHEZMOI_SOURCE_FILE', 'modify script')}: {error}")
