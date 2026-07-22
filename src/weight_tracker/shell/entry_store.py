"""SQLite EntryStore + TelemetryStore adapter -- RED scaffold (created by DISTILL).

Schema (ADR-002): entries(date TEXT PRIMARY KEY, weight_kg REAL, logged_at TEXT,
entry_ms INTEGER) + append-only events(id, ts, name, payload).
Pragmas: WAL + synchronous=FULL. Save is confirmed only after commit returns.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from weight_tracker.core.types import Entry

__SCAFFOLD__ = True


class SqliteEntryStore:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def probe(self) -> None:
        """Startup probe (Earned Trust, ADR-002): open, PRAGMA integrity_check, assert
        WAL + synchronous=FULL, sentinel write->fsync->readback. Raise on any failure."""
        raise AssertionError("Not yet implemented -- RED scaffold")

    def upsert(self, entry: Entry) -> None:
        raise AssertionError("Not yet implemented -- RED scaffold")

    def entries_between(self, start: date, end: date) -> list[Entry]:
        raise AssertionError("Not yet implemented -- RED scaffold")

    def all_entries(self) -> list[Entry]:
        raise AssertionError("Not yet implemented -- RED scaffold")

    def append_event(self, ts: str, name: str, payload: str) -> None:
        raise AssertionError("Not yet implemented -- RED scaffold")

    def count_events(self, name: str) -> int:
        raise AssertionError("Not yet implemented -- RED scaffold")
