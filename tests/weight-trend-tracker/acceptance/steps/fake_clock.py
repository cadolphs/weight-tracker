"""FakeClock -- the only faked port (driven external / non-deterministic).

Implements weight_tracker.ports.ClockPort. Manual advance enables midnight,
timezone-skew and 90-day-session scenarios.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta


class FakeClock:
    def __init__(self, now: datetime | None = None) -> None:
        self._now = now or datetime(2026, 7, 21, 6, 45, tzinfo=UTC)

    def now_utc(self) -> datetime:
        return self._now

    def set_today(self, day: date) -> None:
        """Morning of `day`, 06:45 UTC -- the canonical weigh-in moment."""
        self._now = datetime.combine(day, time(6, 45), tzinfo=UTC)

    def advance_days(self, days: int) -> None:
        self._now = self._now + timedelta(days=days)

    def today(self) -> date:
        return self._now.date()
