"""Diagnostic result types returned by merge helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Diagnostic:
    """A warning or error produced while applying a managed overlay."""

    severity: Literal["warning", "error"]
    message: str


@dataclass(frozen=True)
class MergeResult:
    """Text produced by a merge helper plus any non-fatal diagnostics."""

    text: str
    diagnostics: tuple[Diagnostic, ...] = ()
