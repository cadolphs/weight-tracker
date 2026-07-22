"""Read-side KPI telemetry queries (SQLite, same append-only events table).

The event trail lives in ONE place: the `events` table written through the
EntryStorePort (DEVOPS Pre-Requisite 5 -- never a parallel table). This module
adds the KPI query surface (/stats windowed counts) without widening the
entry-persistence port with read-model concerns. Functions, not classes:
dependencies arrive as parameters (functional DI), specialised by partial
application at the composition root.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path


def count_events_since(db_path: Path, name: str, since: date) -> int:
    """Events named `name` stamped on `since` or any later day.

    Event timestamps are ISO-8601 UTC strings, so the day boundary is the plain
    lexicographic comparison against the ISO date.
    """
    with closing(sqlite3.connect(db_path)) as connection:
        row = connection.execute(
            "SELECT COUNT(*) FROM events WHERE name = ? AND ts >= ?",
            (name, since.isoformat()),
        ).fetchone()
    return int(row[0])


def entry_ms_samples_since(db_path: Path, name: str, since: date) -> list[int]:
    """Client-measured entry durations (KPI-1) carried by `name` events stamped on
    `since` or any later day. Saves submitted without a timing carry a null
    entry_ms in the payload and are not samples."""
    with closing(sqlite3.connect(db_path)) as connection:
        rows = connection.execute(
            "SELECT payload FROM events WHERE name = ? AND ts >= ?",
            (name, since.isoformat()),
        ).fetchall()
    durations = (json.loads(payload).get("entry_ms") for (payload,) in rows)
    return [int(duration) for duration in durations if duration is not None]
