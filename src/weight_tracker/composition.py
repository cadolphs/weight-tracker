"""Production composition root.

Wire -> probe all driven adapters -> serve (brief.md). Any probe failure means the
app refuses to serve (`health.startup.refused`) rather than risk losing entries.

Acceptance tests build the app EXCLUSIVELY through this function (Pillar 3):
same wiring as production, with only the external/non-deterministic Clock injected.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Any

from fastapi import FastAPI

from weight_tracker.core.trend import trend_series_in
from weight_tracker.ports import ClockPort
from weight_tracker.shell.access_gate import AccessGate, install_access_gate
from weight_tracker.shell.entry_store import SqliteEntryStore, replication_status
from weight_tracker.shell.telemetry_store import count_events_since, entry_ms_samples_since
from weight_tracker.web.routes import build_router


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
                                         (emits trend_view_opened event, KPI-3)
        GET  /graph?view=...&scale=...   graph page (default view=trend A4; one-tap
                                         Trend/Raw toggle shares selected_time_scale)
        GET  /stats                      KPI query surface (entry speed, adherence, trend
                                         opens incl. trend_views_this_week rolling 7 days)
        GET  /healthz                    unauthenticated health/replication status
        GET  /manifest.webmanifest       PWA install manifest
        GET  /sw.js                      minimal service worker (app-shell cache only)
    """
    store = SqliteEntryStore(db_path)
    gate = AccessGate(passphrase_hash=passphrase_hash, session_signing_key=session_signing_key)
    # Additive-only migrations run BEFORE probing (DEVOPS 2a); a failed migration
    # refuses start exactly like a failed probe.
    _startup_action_or_refuse("entry_store", store.apply_migrations)
    _probe_all_or_refuse({"entry_store": store, "access_gate": gate, "clock": clock})
    app = FastAPI()
    install_access_gate(app, gate, clock)
    app.include_router(
        build_router(
            store=store,
            gate=gate,
            clock=clock,
            trend_series_in=trend_series_in,
            count_events_since=partial(count_events_since, db_path),
            entry_ms_samples_since=partial(entry_ms_samples_since, db_path),
            replication_status=lambda: replication_status(db_path),
        )
    )
    return app


def _probe_all_or_refuse(adapters: dict[str, Any]) -> None:
    """Run every adapter's startup probe; any failure refuses start (Earned Trust).

    Injected test fakes (e.g. FakeClock) carry no probe and are the injector's
    responsibility; every production driven adapter implements `probe()`.
    """
    for adapter_name, adapter in adapters.items():
        probe = getattr(adapter, "probe", None)
        if probe is None:
            continue
        _startup_action_or_refuse(adapter_name, probe)


def _startup_action_or_refuse(adapter_name: str, startup_action: Callable[[], None]) -> None:
    """Run one startup action (migration or probe); any failure = structured
    `health.startup.refused` log + StartupRefused (no traffic served)."""
    try:
        startup_action()
    except Exception as failure:
        _log_startup_refused(adapter_name, failure)
        raise StartupRefused(f"{adapter_name} probe failed: {failure}") from failure


def _log_startup_refused(adapter_name: str, failure: Exception) -> None:
    refusal = {"event": "health.startup.refused", "adapter": adapter_name, "error": str(failure)}
    probe_id: str | None = getattr(failure, "probe", None)
    if probe_id is not None:
        refusal["probe"] = probe_id
    print(json.dumps(refusal), file=sys.stderr)


class StartupRefused(Exception):
    """Raised when a driven-adapter startup probe fails: the app must not serve traffic."""
