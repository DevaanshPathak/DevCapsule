"""Markdown formatter for AI-ready context capsules."""

from __future__ import annotations

from devcapsule.models import (
    CaptureMetadata,
    ClipboardContext,
    ContextSection,
    EnvironmentContext,
    FileContext,
    GitContext,
    ProjectContext,
    TerminalContext,
)
from devcapsule.ranking.relevance import truncate_text


def format_context(
    *,
    metadata: CaptureMetadata,
    git: GitContext,
    project: ProjectContext,
    terminal: TerminalContext,
    clipboard: ClipboardContext,
    environment: EnvironmentContext,
    max_chars: int,
) -> tuple[str, list[ContextSection]]:
    """Build Markdown and matching structured sections."""

    sections = [
        ContextSection(title="Metadata", content=_metadata_section(metadata)),
        ContextSection(title="Summary", content=_summary_section(metadata, git, project)),
        ContextSection(title="Git State", content=_git_section(git)),
        ContextSection(title="Project Structure", content=_project_structure_section(project)),
        ContextSection(title="Important Files", content=_files_section(project.important_files)),
        ContextSection(title="Relevant Source Files", content=_files_section(project.source_files)),
        ContextSection(title="Terminal Context", content=_terminal_section(terminal)),
        ContextSection(title="Clipboard Context", content=_clipboard_section(clipboard)),
        ContextSection(title="Environment", content=_environment_section(environment)),
        ContextSection(title="Suggested Prompt", content=_suggested_prompt(metadata.focus)),
    ]
    markdown = render_sections(sections, max_chars=max_chars)
    return markdown, sections


def render_sections(sections: list[ContextSection], *, max_chars: int) -> str:
    """Render sections into a single Markdown document."""

    parts = ["# DevCapsule Context"]
    for section in sections:
        parts.append(f"## {section.title}\n\n{section.content.strip()}")
    markdown = "\n\n".join(parts).strip() + "\n"
    if len(markdown) > max_chars:
        prompt_stub = (
            "\n\n## Suggested Prompt\n\n"
            "Context was truncated. Focus on the visible Git, terminal, and file context first.\n"
        )
        if max_chars > len(prompt_stub) + 80:
            markdown, _ = truncate_text(markdown, max_chars - len(prompt_stub))
            markdown = markdown.rstrip() + prompt_stub
        else:
            markdown, _ = truncate_text(markdown, max_chars)
    if len(markdown) > max_chars:
        markdown, _ = truncate_text(markdown, max_chars)
    return markdown


def _metadata_section(metadata: CaptureMetadata) -> str:
    return "\n".join(
        [
            f"- Created: {metadata.created_at.isoformat()}",
            f"- Repository: {metadata.repo_name or 'unknown'}",
            f"- Branch: {metadata.branch or 'unknown'}",
            f"- Working Directory: {metadata.repo_root or 'unknown'}",
            f"- Focus Mode: {metadata.focus}",
        ]
    )


def _summary_section(metadata: CaptureMetadata, git: GitContext, project: ProjectContext) -> str:
    changed_count = len(set(git.modified_files + git.staged_files + git.untracked_files))
    important_count = len(project.important_files)
    source_count = len(project.source_files)
    lines = [
        f"Repository `{metadata.repo_name or 'unknown'}` captured in `{metadata.focus}` mode.",
        f"Detected {changed_count} changed/untracked file(s), {important_count} important project file(s), and {source_count} ranked relevant source/config file(s).",
    ]
    if git.warnings or project.warnings:
        lines.append("")
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in [*git.warnings, *project.warnings])
    return "\n".join(lines)


def _git_section(git: GitContext) -> str:
    lines = [
        f"Repository root: {git.repo_root or 'not detected'}",
        f"Branch: {git.branch or 'unknown'}",
    ]
    lines.append("\nModified files:")
    lines.extend(_bullet_list(git.modified_files))
    lines.append("\nStaged files:")
    lines.extend(_bullet_list(git.staged_files))
    lines.append("\nUntracked files:")
    lines.extend(_bullet_list(git.untracked_files))
    lines.append("\nRecent commits:")
    lines.extend(_bullet_list(git.recent_commits))
    if git.diff:
        lines.append("\nGit diff:")
        lines.append(_code_block(git.diff, "diff"))
    if git.staged_diff:
        lines.append("\nStaged diff:")
        lines.append(_code_block(git.staged_diff, "diff"))
    if git.warnings:
        lines.append("\nWarnings:")
        lines.extend(f"- {warning}" for warning in git.warnings)
    return "\n".join(lines)


def _project_structure_section(project: ProjectContext) -> str:
    if not project.tree:
        return "No project tree captured."
    return _code_block("\n".join(project.tree), "text")


def _files_section(files: list[FileContext]) -> str:
    if not files:
        return "No files captured for this section."
    parts: list[str] = []
    for file in files:
        parts.append(f"### {file.path}")
        if file.purpose:
            parts.append(f"Purpose: {file.purpose}")
        if file.redacted:
            parts.append("Security: suspicious content was redacted.")
        if file.truncated:
            parts.append("Note: file content was truncated.")
        parts.append(_code_block(file.content, file.language))
    return "\n\n".join(parts)


def _terminal_section(terminal: TerminalContext) -> str:
    lines: list[str] = []
    if terminal.history_source:
        lines.append(f"History source: `{terminal.history_source}`")
    if terminal.recent_commands:
        lines.append("\nRecent commands:")
        lines.append(_code_block("\n".join(terminal.recent_commands), "bash"))
    else:
        lines.append("No recent shell history captured.")
    if terminal.warnings:
        lines.append("\nWarnings:")
        lines.extend(f"- {warning}" for warning in terminal.warnings)
    return "\n".join(lines)


def _clipboard_section(clipboard: ClipboardContext) -> str:
    lines: list[str] = []
    if clipboard.text:
        lines.append(_code_block(clipboard.text, "text"))
    else:
        lines.append("No clipboard text captured.")
    if clipboard.warnings:
        lines.append("\nWarnings:")
        lines.extend(f"- {warning}" for warning in clipboard.warnings)
    return "\n".join(lines)


def _environment_section(environment: EnvironmentContext) -> str:
    lines = [
        f"- OS: {environment.os}",
        f"- Python: {environment.python_version}",
        f"- Node: {environment.node_version or 'not found'}",
        f"- Git: {environment.git_version or 'not found'}",
        f"- Working Directory: {environment.cwd}",
        f"- Virtualenv: {environment.virtualenv or 'not active'}",
    ]
    if environment.warnings:
        lines.append("\nWarnings:")
        lines.extend(f"- {warning}" for warning in environment.warnings)
    return "\n".join(lines)


def _suggested_prompt(focus: str) -> str:
    prompts = {
        "debug": "Using the context above, help me debug this project. Focus on terminal commands, errors, changed files, and the Git diff first.",
        "pr": "Using the context above, help me review this project as a pull request. Focus on the Git diff, changed files, tests, and likely regressions.",
        "explain": "Using the context above, explain this project clearly. Focus on the project structure, README, dependency files, and key source files.",
        "general": "Using the context above, help me debug, explain, or review this project. Focus on the changed files and terminal output first.",
    }
    return prompts.get(focus, prompts["general"])


def _bullet_list(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items] if items else ["- None"]


def _code_block(content: str, language: str = "") -> str:
    fence = "```"
    safe_content = content.replace("```", "``\\`")
    return f"{fence}{language}\n{safe_content.rstrip()}\n{fence}"
