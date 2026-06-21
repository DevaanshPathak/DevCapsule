"""SQLite-backed local capture history."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from devcapsule.config import get_history_db_path
from devcapsule.models import CaptureMetadata, ContextCapsule

SCHEMA = """
CREATE TABLE IF NOT EXISTS captures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    repo_root TEXT,
    repo_name TEXT,
    branch TEXT,
    focus TEXT NOT NULL,
    markdown TEXT NOT NULL,
    char_count INTEGER NOT NULL
);
"""


def ensure_database(db_path: Path | None = None) -> Path:
    """Create the local SQLite database if needed."""

    path = db_path or get_history_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute(SCHEMA)
        connection.commit()
    return path


def save_capture(capsule: ContextCapsule, db_path: Path | None = None) -> int:
    """Save a capture and return its assigned ID."""

    path = ensure_database(db_path)
    with sqlite3.connect(path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO captures (
                created_at, repo_root, repo_name, branch, focus, markdown, char_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                capsule.created_at.isoformat(),
                capsule.repo_root,
                capsule.repo_name,
                capsule.branch,
                capsule.focus,
                capsule.markdown,
                capsule.char_count,
            ),
        )
        connection.commit()
        if cursor.lastrowid is None:
            raise RuntimeError("SQLite did not return a capture ID")
        return cursor.lastrowid


def get_capture(id: int, db_path: Path | None = None) -> ContextCapsule | None:
    """Return a capture by ID, if it exists."""

    path = ensure_database(db_path)
    with sqlite3.connect(path) as connection:
        row = connection.execute(
            """
            SELECT id, created_at, repo_root, repo_name, branch, focus, markdown, char_count
            FROM captures
            WHERE id = ?
            """,
            (id,),
        ).fetchone()
    if row is None:
        return None
    return _row_to_capsule(row)


def get_latest_capture(db_path: Path | None = None) -> ContextCapsule | None:
    """Return the most recent capture."""

    path = ensure_database(db_path)
    with sqlite3.connect(path) as connection:
        row = connection.execute(
            """
            SELECT id, created_at, repo_root, repo_name, branch, focus, markdown, char_count
            FROM captures
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
    if row is None:
        return None
    return _row_to_capsule(row)


def list_captures(limit: int = 20, db_path: Path | None = None) -> list[CaptureMetadata]:
    """List recent capture metadata."""

    path = ensure_database(db_path)
    with sqlite3.connect(path) as connection:
        rows = connection.execute(
            """
            SELECT id, created_at, repo_root, repo_name, branch, focus, char_count
            FROM captures
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [
        CaptureMetadata(
            id=row[0],
            created_at=datetime.fromisoformat(row[1]),
            repo_root=row[2],
            repo_name=row[3],
            branch=row[4],
            focus=row[5],
            char_count=row[6],
        )
        for row in rows
    ]


def _row_to_capsule(row: Sequence[Any]) -> ContextCapsule:
    return ContextCapsule(
        id=int(cast(int, row[0])),
        created_at=datetime.fromisoformat(str(row[1])),
        repo_root=str(row[2]) if row[2] is not None else None,
        repo_name=str(row[3]) if row[3] is not None else None,
        branch=str(row[4]) if row[4] is not None else None,
        focus=str(row[5]),
        markdown=str(row[6]),
        char_count=int(cast(int, row[7])),
    )
