"""System clock adapter (production ClockPort implementation)."""

from __future__ import annotations

from datetime import datetime, timezone


class SystemClock:
    def now_utc(self) -> datetime:
        return datetime.now(timezone.utc)

    def probe(self) -> None:
        """Startup sanity: year in [2026, 2100]."""
        year = self.now_utc().year
        if not 2026 <= year <= 2100:
            raise RuntimeError(f"system clock reports implausible year {year}")
