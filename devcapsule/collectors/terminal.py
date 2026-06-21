"""Recent shell history collector."""

from __future__ import annotations

import os
from pathlib import Path

from devcapsule.config import DEFAULT_HISTORY_LIMIT
from devcapsule.models import ContextSection, TerminalContext
from devcapsule.ranking.relevance import redact_secrets, truncate_text


class TerminalCollector:
    """Collect recent commands from common local shell history files."""

    name = "terminal"

    def __init__(self, limit: int = DEFAULT_HISTORY_LIMIT) -> None:
        self.limit = limit

    def collect_context(self) -> TerminalContext:
        for path in self._candidate_history_files():
            if not path.is_file():
                continue
            commands = self._read_commands(path)
            if commands:
                return TerminalContext(recent_commands=commands[-self.limit :], history_source=str(path))
        return TerminalContext(warnings=["No supported shell history file was found."])

    def collect(self) -> ContextSection:
        context = self.collect_context()
        if context.recent_commands:
            content = "\n".join(f"- `{command}`" for command in context.recent_commands)
        else:
            content = "No recent terminal history captured."
        if context.warnings:
            content += "\n\n" + "\n".join(f"- {warning}" for warning in context.warnings)
        return ContextSection(title="Terminal Context", content=content, warnings=context.warnings)

    def _candidate_history_files(self) -> list[Path]:
        home = Path.home()
        candidates: list[Path] = []
        histfile = os.environ.get("HISTFILE")
        if histfile:
            candidates.append(Path(histfile).expanduser())
        candidates.extend(
            [
                home / ".bash_history",
                home / ".zsh_history",
                home / ".local" / "share" / "fish" / "fish_history",
                home
                / "AppData"
                / "Roaming"
                / "Microsoft"
                / "Windows"
                / "PowerShell"
                / "PSReadLine"
                / "ConsoleHost_history.txt",
            ]
        )
        return candidates

    def _read_commands(self, path: Path) -> list[str]:
        try:
            with path.open("rb") as handle:
                handle.seek(0, os.SEEK_END)
                size = handle.tell()
                handle.seek(max(0, size - 64_000))
                data = handle.read()
        except OSError:
            return []
        text = data.decode("utf-8", errors="replace")
        commands: list[str] = []
        if path.name == "fish_history":
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("- cmd:"):
                    commands.append(stripped.removeprefix("- cmd:").strip())
        else:
            for line in text.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith(": ") and ";" in stripped:
                    stripped = stripped.split(";", 1)[1]
                commands.append(stripped)
        cleaned: list[str] = []
        for command in commands:
            redacted = redact_secrets(command)
            redacted, _ = truncate_text(redacted, 500)
            if redacted:
                cleaned.append(redacted)
        return cleaned
