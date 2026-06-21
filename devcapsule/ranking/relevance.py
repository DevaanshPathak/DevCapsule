"""Context relevance ranking, truncation, and secret redaction."""

from __future__ import annotations

import re
from pathlib import Path

from devcapsule.config import DEPENDENCY_FILES, IMPORTANT_FILES, SENSITIVE_FILENAMES

TRUNCATION_NOTE = "[Truncated: content exceeded max context budget]"

PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----[\s\S]+?-----END [A-Z0-9 ]*PRIVATE KEY-----",
    re.MULTILINE,
)
AWS_ACCESS_KEY_RE = re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")
OPENAI_KEY_RE = re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")
GITHUB_TOKEN_RE = re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b")
GENERIC_SECRET_RE = re.compile(
    r"(?im)\b(api[_-]?key|access[_-]?token|auth[_-]?token|token|password|passwd|secret)"
    r"\b\s*[:=]\s*([\"']?)([^\s\"']{8,})(\2)"
)


def is_sensitive_path(path: str | Path) -> bool:
    """Return True when a path should never be captured."""

    candidate = Path(path)
    name = candidate.name.lower()
    if name in SENSITIVE_FILENAMES:
        return True
    return name.startswith(".env") and name != ".env.example"


def redact_secrets(text: str) -> str:
    """Redact common secret formats without raising on arbitrary text."""

    redacted = PRIVATE_KEY_RE.sub("[REDACTED]", text)
    redacted = AWS_ACCESS_KEY_RE.sub("[REDACTED]", redacted)
    redacted = OPENAI_KEY_RE.sub("[REDACTED]", redacted)
    redacted = GITHUB_TOKEN_RE.sub("[REDACTED]", redacted)

    def replace_assignment(match: re.Match[str]) -> str:
        return f"{match.group(1)}=[REDACTED]"

    return GENERIC_SECRET_RE.sub(replace_assignment, redacted)


def truncate_text(text: str, max_chars: int, note: str = TRUNCATION_NOTE) -> tuple[str, bool]:
    """Truncate text cleanly and include a visible note."""

    if max_chars <= 0:
        return note, True
    if len(text) <= max_chars:
        return text, False
    budget = max(0, max_chars - len(note) - 2)
    return f"{text[:budget].rstrip()}\n\n{note}", True


def language_for_path(path: str | Path) -> str:
    """Return a Markdown code fence language from a file path."""

    suffix = Path(path).suffix.lower()
    mapping = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "jsx",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".json": "json",
        ".toml": "toml",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".md": "markdown",
        ".sh": "bash",
        ".ps1": "powershell",
        ".sql": "sql",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".rb": "ruby",
        ".php": "php",
        ".cs": "csharp",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".swift": "swift",
        ".kt": "kotlin",
        ".kts": "kotlin",
    }
    return mapping.get(suffix, "")


def rank_paths(
    paths: list[Path],
    *,
    focus: str,
    modified_files: set[str],
    staged_files: set[str],
    diff_text: str,
    terminal_text: str,
) -> list[Path]:
    """Rank candidate files by likely relevance for AI context."""

    weighted: list[tuple[int, float, Path]] = []
    focus = focus.lower()
    for path in paths:
        normalized = path.as_posix()
        name = path.name
        score = 0
        if normalized in modified_files:
            score += 120
        if normalized in staged_files:
            score += 110
        if normalized in diff_text:
            score += 70
        if normalized in terminal_text or name in terminal_text:
            score += 60
        if name in DEPENDENCY_FILES:
            score += 45
        if name in IMPORTANT_FILES or name.lower().startswith("readme"):
            score += 35
        if focus == "debug":
            if name.startswith("test_") or "test" in path.parts or "log" in name.lower():
                score += 35
        elif focus == "pr":
            if normalized in modified_files or normalized in staged_files:
                score += 45
            if name.startswith("test_") or "test" in path.parts:
                score += 20
        elif focus == "explain":
            if name.lower().startswith("readme") or name in DEPENDENCY_FILES:
                score += 40
            if path.parent == Path("."):
                score += 15
        try:
            mtime = path.stat().st_mtime
        except OSError:
            mtime = 0.0
        weighted.append((score, mtime, path))

    weighted.sort(key=lambda item: (item[0], item[1], item[2].as_posix()), reverse=True)
    return [path for _, _, path in weighted]
