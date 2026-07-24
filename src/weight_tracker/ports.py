"""Port protocols (hexagonal boundary). Adapters live in `shell`; fakes live in tests."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

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
    """Driven persistence port: durable entry upsert/read plus the append-only event trail."""

    def probe(self) -> None:
        """Startup Earned-Trust probe. Raise on any failure; the app must then refuse to serve."""
        ...

    def upsert(self, entry: Entry, logged_at: str) -> None:
        """Durably hold `entry` for its day, replacing any previous entry for that day."""
        ...

    def all_entries(self) -> list[Entry]:
        """Every entry, newest first."""
        ...

    def append_event(self, ts: str, name: str, payload: str) -> None:
        """Append one telemetry event (KPI trail, append-only)."""
        ...

    def count_events(self, name: str) -> int:
        """Number of events recorded under `name`."""
        ...
