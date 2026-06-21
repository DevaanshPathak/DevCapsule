"""Environment collector."""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from pathlib import Path

from devcapsule.models import ContextSection, EnvironmentContext


class EnvironmentCollector:
    """Collect safe local environment details."""

    name = "environment"

    def __init__(self, cwd: Path | None = None) -> None:
        self.cwd = Path.cwd() if cwd is None else Path(cwd)

    def collect_context(self) -> EnvironmentContext:
        return EnvironmentContext(
            os=f"{platform.system()} {platform.release()}",
            python_version=platform.python_version(),
            node_version=self._version(["node", "--version"]),
            git_version=self._version(["git", "--version"]),
            cwd=str(self.cwd),
            virtualenv=self._virtualenv(),
        )

    def collect(self) -> ContextSection:
        context = self.collect_context()
        lines = [
            f"OS: {context.os}",
            f"Python: {context.python_version}",
            f"Node: {context.node_version or 'not found'}",
            f"Git: {context.git_version or 'not found'}",
            f"Working directory: {context.cwd}",
        ]
        if context.virtualenv:
            lines.append(f"Virtualenv: {context.virtualenv}")
        return ContextSection(title="Environment", content="\n".join(lines))

    def _version(self, args: list[str]) -> str | None:
        if shutil.which(args[0]) is None:
            return None
        try:
            completed = subprocess.run(
                args,
                cwd=str(self.cwd),
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if completed.returncode != 0:
            return None
        return completed.stdout.strip().splitlines()[0] if completed.stdout.strip() else None

    @staticmethod
    def _virtualenv() -> str | None:
        prefix = getattr(sys, "real_prefix", None)
        if prefix:
            return sys.prefix
        if sys.prefix != getattr(sys, "base_prefix", sys.prefix):
            return sys.prefix
        return None
