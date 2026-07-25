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
from typing import Any


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
    durations = (payload.get("entry_ms") for payload in _payloads_since(db_path, name, since))
    return [int(duration) for duration in durations if duration is not None]


def backdated_saves_since(db_path: Path, name: str, since: date) -> int:
    """In-app repairs (KPI-8) carried by `name` events stamped on `since` or any
    later day: the saves the record itself calls backdated.

    A save dated away from the phone's own day is maintenance, not a morning --
    it contributes 0 KPI-1 speed samples and is counted here instead (ADR-011).
    The trail keeps ONE event per save (D-23), so the classification travels as a
    `backdated` flag on the entry.saved payload rather than a second event name;
    reading it is therefore a payload predicate, not a name count. Every save
    written before the flag existed carries no `backdated` word and is no repair.
    """
    return sum(1 for payload in _payloads_since(db_path, name, since) if payload.get("backdated"))


def _payloads_since(db_path: Path, name: str, since: date) -> list[dict[str, Any]]:
    """Every `name` payload stamped on `since` or any later day, parsed.

    ONE windowed payload read behind both payload-shaped KPIs above: the timing
    and the repair flag ride the SAME entry.saved event (D-23), so the two can
    never disagree about which saves fall inside the week. Private on purpose --
    the module's public surface is exactly the queries wired at the composition
    root by partial application.
    """
    with closing(sqlite3.connect(db_path)) as connection:
        rows = connection.execute(
            "SELECT payload FROM events WHERE name = ? AND ts >= ?",
            (name, since.isoformat()),
        ).fetchall()
    return [json.loads(payload) for (payload,) in rows]
