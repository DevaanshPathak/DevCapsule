from __future__ import annotations

from datetime import UTC, datetime

from devcapsule.models import ContextCapsule
from devcapsule.storage.sqlite import get_capture, get_latest_capture, list_captures, save_capture


def test_sqlite_save_list_get_latest(tmp_path) -> None:
    db_path = tmp_path / "history.sqlite3"
    capsule = ContextCapsule(
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        repo_root="/tmp/demo",
        repo_name="demo",
        branch="main",
        focus="general",
        markdown="# DevCapsule Context\n",
        char_count=21,
    )

    capture_id = save_capture(capsule, db_path=db_path)
    assert capture_id == 1

    captures = list_captures(db_path=db_path)
    assert len(captures) == 1
    assert captures[0].repo_name == "demo"

    fetched = get_capture(capture_id, db_path=db_path)
    assert fetched is not None
    assert fetched.markdown.startswith("# DevCapsule")

    latest = get_latest_capture(db_path=db_path)
    assert latest is not None
    assert latest.id == capture_id
