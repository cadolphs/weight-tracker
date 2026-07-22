"""Port protocols (hexagonal boundary). Adapters live in `shell`; fakes live in tests."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class ClockPort(Protocol):
    """Driven external, non-deterministic port -- faked in acceptance tests (FakeClock)."""

    def now_utc(self) -> datetime:
        """Current UTC instant. Used only for the future-date sanity bound and event timestamps."""
        ...
