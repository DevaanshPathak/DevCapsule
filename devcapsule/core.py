"""Core capture orchestration."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from devcapsule.collectors.clipboard import ClipboardCollector
from devcapsule.collectors.environment import EnvironmentCollector
from devcapsule.collectors.git import GitCollector
from devcapsule.collectors.project import ProjectCollector
from devcapsule.collectors.terminal import TerminalCollector
from devcapsule.config import DEFAULT_MAX_CHARS, FOCUS_MODES
from devcapsule.formatter.markdown import format_context
from devcapsule.models import CaptureMetadata, ContextCapsule


def capture_context(
    *,
    focus: str = "general",
    max_chars: int = DEFAULT_MAX_CHARS,
    cwd: Path | None = None,
) -> ContextCapsule:
    """Capture the current project state as an AI-ready Markdown capsule."""

    focus = focus.lower()
    if focus not in FOCUS_MODES:
        allowed = ", ".join(sorted(FOCUS_MODES))
        raise ValueError(f"Unsupported focus mode {focus!r}. Expected one of: {allowed}")

    working_dir = (Path.cwd() if cwd is None else Path(cwd)).resolve()
    git = GitCollector(working_dir).collect_context()
    repo_root = Path(git.repo_root).resolve() if git.repo_root else working_dir
    terminal = TerminalCollector().collect_context()
    terminal_text = "\n".join(terminal.recent_commands)
    project = ProjectCollector(
        repo_root,
        focus=focus,
        modified_files=git.modified_files + git.untracked_files,
        staged_files=git.staged_files,
        diff_text=f"{git.diff}\n{git.staged_diff}",
        terminal_text=terminal_text,
    ).collect_context()
    clipboard = ClipboardCollector().collect_context()
    environment = EnvironmentCollector(working_dir).collect_context()

    metadata = CaptureMetadata(
        created_at=datetime.now(UTC),
        repo_root=str(repo_root),
        repo_name=git.repo_name or repo_root.name,
        branch=git.branch,
        focus=focus,
    )
    markdown, sections = format_context(
        metadata=metadata,
        git=git,
        project=project,
        terminal=terminal,
        clipboard=clipboard,
        environment=environment,
        max_chars=max_chars,
    )
    return ContextCapsule(
        created_at=metadata.created_at,
        repo_root=metadata.repo_root,
        repo_name=metadata.repo_name,
        branch=metadata.branch,
        focus=focus,
        sections=sections,
        markdown=markdown,
        char_count=len(markdown),
    )
