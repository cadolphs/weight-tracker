"""SQLite EntryStore + TelemetryStore adapter.

Schema (ADR-002): entries(date TEXT PRIMARY KEY, weight_kg REAL, logged_at TEXT,
entry_ms INTEGER) + append-only events(id, ts, name, payload).
Pragmas: WAL + synchronous=FULL. Save is confirmed only after commit returns.
"""

from __future__ import annotations

import sqlite3
import uuid
from contextlib import closing
from datetime import date
from pathlib import Path

from weight_tracker.core.types import Entry

_LYING_FILESYSTEMS = frozenset({"tmpfs", "ramfs", "overlay", "overlayfs"})

_SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS entries (
        date TEXT PRIMARY KEY,
        weight_kg REAL NOT NULL,
        logged_at TEXT,
        entry_ms INTEGER
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT NOT NULL,
        name TEXT NOT NULL,
        payload TEXT NOT NULL
    )
    """,
)


def replication_status(db_path: Path) -> str:
    """Replication signal for /healthz: Litestream keeps its generations directory
    beside the record; where it is absent (local runs, no sidecar) the honest
    answer is n/a rather than a pretended lag figure."""
    litestream_dir = db_path.parent / f".{db_path.name}-litestream"
    return "active" if litestream_dir.exists() else "n/a"


def _filesystem_type_of(path: Path) -> str | None:
    """Filesystem type holding `path`, or None where it cannot be determined (no /proc)."""
    try:
        mount_lines = Path("/proc/mounts").read_text().splitlines()
    except OSError:
        return None
    longest_mount_point, filesystem_type = "", None
    for line in mount_lines:
        fields = line.split()
        if len(fields) < 3:
            continue
        mount_point, mounted_type = fields[1], fields[2]
        if str(path).startswith(mount_point) and len(mount_point) >= len(longest_mount_point):
            longest_mount_point, filesystem_type = mount_point, mounted_type
    return filesystem_type


class SqliteEntryStore:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        return connection

    def probe(self) -> None:
        """Startup probe (Earned Trust, ADR-002): open, PRAGMA integrity_check, assert
        WAL + synchronous=FULL, sentinel write->fsync->readback, statfs != tmpfs.
        Raise on any failure."""
        filesystem_type = _filesystem_type_of(self._db_path.parent)
        if filesystem_type in _LYING_FILESYSTEMS:
            raise RuntimeError(
                f"record home is on {filesystem_type}: fsync cannot be trusted there"
            )
        with closing(self._connect()) as connection:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise RuntimeError(f"integrity_check failed: {integrity}")
            journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
            if str(journal_mode).lower() != "wal":
                raise RuntimeError(f"journal_mode is {journal_mode!r}, WAL required")
            synchronous = connection.execute("PRAGMA synchronous").fetchone()[0]
            if synchronous != 2:  # 2 == FULL
                raise RuntimeError(f"synchronous is {synchronous!r}, FULL (2) required")
            for statement in _SCHEMA:
                connection.execute(statement)
            self._sentinel_roundtrip(connection)

    @staticmethod
    def _sentinel_roundtrip(connection: sqlite3.Connection) -> None:
        """Sentinel write -> fsync (synchronous=FULL commit + WAL checkpoint) -> readback."""
        sentinel_token = uuid.uuid4().hex
        connection.execute("CREATE TABLE IF NOT EXISTS probe_sentinel (token TEXT NOT NULL)")
        connection.execute("DELETE FROM probe_sentinel")
        connection.execute("INSERT INTO probe_sentinel (token) VALUES (?)", (sentinel_token,))
        connection.commit()
        connection.execute("PRAGMA wal_checkpoint(FULL)")
        read_back = connection.execute("SELECT token FROM probe_sentinel").fetchone()
        if read_back is None or read_back[0] != sentinel_token:
            raise RuntimeError("sentinel write did not read back: store cannot be trusted")

    def upsert(self, entry: Entry, logged_at: str) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT INTO entries (date, weight_kg, logged_at, entry_ms)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    weight_kg = excluded.weight_kg,
                    logged_at = excluded.logged_at,
                    entry_ms = excluded.entry_ms
                """,
                (entry.day.isoformat(), entry.weight_kg, logged_at, entry.entry_ms),
            )
            connection.commit()

    def entries_between(self, start: date, end: date) -> list[Entry]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT date, weight_kg, entry_ms FROM entries"
                " WHERE date BETWEEN ? AND ? ORDER BY date DESC",
                (start.isoformat(), end.isoformat()),
            ).fetchall()
        return [_entry_from_row(row) for row in rows]

    def all_entries(self) -> list[Entry]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT date, weight_kg, entry_ms FROM entries ORDER BY date DESC"
            ).fetchall()
        return [_entry_from_row(row) for row in rows]

    def append_event(self, ts: str, name: str, payload: str) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                "INSERT INTO events (ts, name, payload) VALUES (?, ?, ?)", (ts, name, payload)
            )
            connection.commit()

    def count_events(self, name: str) -> int:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT COUNT(*) FROM events WHERE name = ?", (name,)
            ).fetchone()
        return int(row[0])


def _entry_from_row(row: tuple[str, float, int | None]) -> Entry:
    return Entry(day=date.fromisoformat(row[0]), weight_kg=row[1], entry_ms=row[2])
