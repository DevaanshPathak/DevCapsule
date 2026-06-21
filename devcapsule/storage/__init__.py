"""SQLite storage API."""

from devcapsule.storage.sqlite import (
    ensure_database,
    get_capture,
    get_latest_capture,
    list_captures,
    save_capture,
)

__all__ = [
    "ensure_database",
    "get_capture",
    "get_latest_capture",
    "list_captures",
    "save_capture",
]
