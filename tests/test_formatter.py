from __future__ import annotations

from datetime import UTC, datetime

from devcapsule.formatter.markdown import format_context
from devcapsule.models import (
    CaptureMetadata,
    ClipboardContext,
    EnvironmentContext,
    FileContext,
    GitContext,
    ProjectContext,
    TerminalContext,
)
from devcapsule.ranking.relevance import redact_secrets


def test_markdown_formatter_includes_expected_sections() -> None:
    metadata = CaptureMetadata(
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        repo_root="/tmp/demo",
        repo_name="demo",
        branch="main",
        focus="debug",
    )
    markdown, sections = format_context(
        metadata=metadata,
        git=GitContext(repo_root="/tmp/demo", repo_name="demo", branch="main", modified_files=["app.py"]),
        project=ProjectContext(
            repo_root="/tmp/demo",
            tree=["app.py", "pyproject.toml"],
            important_files=[
                FileContext(path="pyproject.toml", content="[project]\nname='demo'", language="toml")
            ],
        ),
        terminal=TerminalContext(recent_commands=["pytest"], history_source="/tmp/history"),
        clipboard=ClipboardContext(text="failed test", available=True),
        environment=EnvironmentContext(os="Linux", python_version="3.12.4", cwd="/tmp/demo"),
        max_chars=30_000,
    )

    assert "# DevCapsule Context" in markdown
    assert "## Git State" in markdown
    assert "## Suggested Prompt" in markdown
    assert "help me debug" in markdown
    assert [section.title for section in sections][:3] == ["Metadata", "Summary", "Git State"]


def test_markdown_formatter_respects_max_chars() -> None:
    metadata = CaptureMetadata(
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        repo_root="/tmp/demo",
        repo_name="demo",
        branch="main",
        focus="general",
    )
    markdown, _ = format_context(
        metadata=metadata,
        git=GitContext(repo_root="/tmp/demo", repo_name="demo", branch="main", diff="x" * 5000),
        project=ProjectContext(repo_root="/tmp/demo", tree=["app.py"]),
        terminal=TerminalContext(),
        clipboard=ClipboardContext(),
        environment=EnvironmentContext(os="Linux", python_version="3.12.4", cwd="/tmp/demo"),
        max_chars=1000,
    )

    assert len(markdown) <= 1000
    assert "[Truncated:" in markdown


def test_secret_redaction_common_patterns() -> None:
    text = """
OPENAI_API_KEY=sk-proj-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
password = supersecretvalue
AWS_ACCESS_KEY_ID=AKIAABCDEFGHIJKLMNOP
"""
    redacted = redact_secrets(text)
    assert "sk-proj-" not in redacted
    assert "supersecretvalue" not in redacted
    assert "AKIAABCDEFGHIJKLMNOP" not in redacted
    assert "[REDACTED]" in redacted
