"""Port protocols (hexagonal boundary). Adapters live in `shell`; fakes live in tests."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from weight_tracker.core.trail import Event
from weight_tracker.core.types import Entry


class ClockPort(Protocol):
    """Driven external, non-deterministic port -- faked in acceptance tests (FakeClock)."""

    def now_utc(self) -> datetime:
        """Current UTC instant.

        The ONLY sanctioned uses: the future-date sanity bound on saves
        (server_utc_today + MAX_DEVICE_SKEW_DAYS), telemetry event timestamps,
        the /stats rolling KPI week, and bounding a claimed ?today= day frame.
        Read surfaces must NEVER derive a user-visible calendar day from this
        clock -- the device-local day is canonical (A5, extended from writes
        to reads by fix-device-day-reads) and arrives as request data."""
        ...


class EntryStorePort(Protocol):
    """Driven persistence port: durable entry upsert/read (the record)."""

    def probe(self) -> None:
        """Startup Earned-Trust probe. Raise on any failure; the app must then refuse to serve."""
        ...

    def upsert(self, entry: Entry, logged_at: str) -> None:
        """Durably hold `entry` for its day, replacing any previous entry for that day."""
        ...

    def all_entries(self) -> list[Entry]:
        """Every entry, newest first."""
        ...


class TrailPort(Protocol):
    """Driven persistence port for the trail (ADR-015): the append-only `events`
    table, written one row at a time and read whole. The one adapter is the
    SQLite store, which also serves `EntryStorePort` -- the trail lives in the
    same file as the record (DEVOPS Pre-Requisite 5), never a parallel table.
    Only `shell/trail.py` speaks to this port."""

    def append_event(self, ts: str, name: str, payload: str) -> None:
        """Append one event row: ISO-8601 UTC timestamp, on-trail name, JSON payload."""
        ...

    def all_events(self) -> list[Event]:
        """Every event on the trail, parsed, in append order."""
        ...
