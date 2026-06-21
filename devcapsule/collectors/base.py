"""Base collector protocol."""

from __future__ import annotations

from typing import Protocol

from devcapsule.models import ContextSection


class Collector(Protocol):
    """Protocol implemented by all collectors."""

    name: str

    def collect(self) -> ContextSection:
        """Collect context as a Markdown-ready section."""


def warning_section(title: str, message: str, *, kind: str = "warning") -> ContextSection:
    """Build a warning section without raising from a collector."""

    return ContextSection(title=title, content=message, kind=kind, warnings=[message])
