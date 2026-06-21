"""Pydantic data models used by DevCapsule."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ContextSection(BaseModel):
    """A named Markdown-ready section of captured context."""

    title: str
    content: str
    kind: str = "general"
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FileContext(BaseModel):
    """Captured content and metadata for a single file."""

    path: str
    purpose: str = ""
    content: str = ""
    language: str = ""
    truncated: bool = False
    redacted: bool = False
    char_count: int = 0


class GitContext(BaseModel):
    """Git repository state."""

    repo_root: str | None = None
    repo_name: str | None = None
    branch: str | None = None
    modified_files: list[str] = Field(default_factory=list)
    staged_files: list[str] = Field(default_factory=list)
    untracked_files: list[str] = Field(default_factory=list)
    recent_commits: list[str] = Field(default_factory=list)
    diff: str = ""
    staged_diff: str = ""
    warnings: list[str] = Field(default_factory=list)


class ProjectContext(BaseModel):
    """Project structure and selected relevant files."""

    repo_root: str
    tree: list[str] = Field(default_factory=list)
    important_files: list[FileContext] = Field(default_factory=list)
    source_files: list[FileContext] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class TerminalContext(BaseModel):
    """Recent local shell history."""

    recent_commands: list[str] = Field(default_factory=list)
    history_source: str | None = None
    warnings: list[str] = Field(default_factory=list)


class ClipboardContext(BaseModel):
    """Local clipboard content, if accessible."""

    text: str = ""
    available: bool = False
    warnings: list[str] = Field(default_factory=list)


class EnvironmentContext(BaseModel):
    """Local environment details."""

    os: str
    python_version: str
    node_version: str | None = None
    git_version: str | None = None
    cwd: str
    virtualenv: str | None = None
    warnings: list[str] = Field(default_factory=list)


class CaptureMetadata(BaseModel):
    """Storage-friendly capture summary."""

    id: int | None = None
    created_at: datetime
    repo_root: str | None = None
    repo_name: str | None = None
    branch: str | None = None
    focus: str
    char_count: int = 0


class ContextCapsule(BaseModel):
    """A complete AI-ready context capsule."""

    id: int | None = None
    created_at: datetime
    repo_root: str | None = None
    repo_name: str | None = None
    branch: str | None = None
    focus: str
    sections: list[ContextSection] = Field(default_factory=list)
    markdown: str
    char_count: int = 0
