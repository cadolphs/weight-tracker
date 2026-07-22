"""Production composition root -- RED scaffold (created by DISTILL).

Wire -> probe all driven adapters -> serve (brief.md). Any probe failure means the
app refuses to serve (`health.startup.refused`) rather than risk losing entries.

Acceptance tests build the app EXCLUSIVELY through this function (Pillar 3):
same wiring as production, with only the external/non-deterministic Clock injected.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from weight_tracker.ports import ClockPort

__SCAFFOLD__ = True


def build_app(
    db_path: Path,
    clock: ClockPort,
    passphrase_hash: str,
    session_signing_key: str,
) -> Any:
    """Build the production ASGI app (FastAPI).

    - Opens/creates the SQLite store at db_path (WAL, synchronous=FULL) and runs its
      startup probe; probe failure => raise StartupRefused (no traffic served).
    - Wires AccessGate (argon2 passphrase verify, signed 90-day HttpOnly cookie,
      rate-limited login) around all routes except /login and /healthz.
    - Routes (driving adapters over the driving ports):
        POST /login                      AccessGate
        GET  /                           entry screen (today preselected, focused decimal
                                         field, yesterday reference)
        POST /entries                    WeightLogging.record_or_replace(date, kg, entry_ms)
        GET  /entries?scale=...          WeightHistory.entries_in(window)
        GET  /trend?scale=...            TrendProjection.trend_series_in(window)
                                         (emits trend_view_opened event)
        GET  /graph?view=...&scale=...   graph page (default view=trend, A4)
        GET  /stats                      KPI query surface (entry speed, adherence, trend opens)
        GET  /healthz                    unauthenticated health/replication status
        GET  /manifest.webmanifest       PWA install manifest
    """
    raise AssertionError("Not yet implemented -- RED scaffold")


class StartupRefused(Exception):
    """Raised when a driven-adapter startup probe fails: the app must not serve traffic."""
