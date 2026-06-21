"""Configuration constants for DevCapsule."""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_MAX_CHARS = 30_000
DEFAULT_DIFF_CHARS = 12_000
DEFAULT_FILE_CHARS = 6_000
DEFAULT_TREE_ENTRIES = 240
DEFAULT_HISTORY_LIMIT = 20

FOCUS_MODES = {"debug", "pr", "explain", "general"}

HISTORY_DB_ENV = "DEVCAPSULE_DB_PATH"
DEFAULT_HISTORY_DB_PATH = Path.home() / ".devcapsule" / "history.sqlite3"

IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "venv",
    ".venv",
    "dist",
    "build",
    "__pycache__",
    ".cache",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".next",
    ".turbo",
    "target",
    "coverage",
    ".idea",
    ".vscode",
}

IMPORTANT_FILES = {
    "README.md",
    "README.rst",
    "README.txt",
    "pyproject.toml",
    "package.json",
    "requirements.txt",
    "requirements-dev.txt",
    "Pipfile",
    "poetry.lock",
    "uv.lock",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "Dockerfile",
    "docker-compose.yml",
    "compose.yml",
    ".env.example",
    "Makefile",
    "tox.ini",
    "mypy.ini",
    "ruff.toml",
}

DEPENDENCY_FILES = {
    "pyproject.toml",
    "package.json",
    "requirements.txt",
    "requirements-dev.txt",
    "Pipfile",
    "poetry.lock",
    "uv.lock",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
}

SENSITIVE_FILENAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    ".env.test",
    "id_rsa",
    "id_ed25519",
    "id_dsa",
    "id_ecdsa",
}

SOURCE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".cs",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".swift",
    ".kt",
    ".kts",
    ".scala",
    ".sh",
    ".ps1",
    ".sql",
    ".md",
    ".toml",
    ".yaml",
    ".yml",
    ".json",
    ".ini",
}


def get_history_db_path() -> Path:
    """Return the configured SQLite history path."""

    configured = os.environ.get(HISTORY_DB_ENV)
    if configured:
        return Path(configured).expanduser()
    return DEFAULT_HISTORY_DB_PATH
