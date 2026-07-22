"""System clock adapter -- RED scaffold (created by DISTILL)."""

from __future__ import annotations

from datetime import datetime

__SCAFFOLD__ = True


class SystemClock:
    def now_utc(self) -> datetime:
        raise AssertionError("Not yet implemented -- RED scaffold")

    def probe(self) -> None:
        """Startup sanity: year in [2026, 2100]."""
        raise AssertionError("Not yet implemented -- RED scaffold")
