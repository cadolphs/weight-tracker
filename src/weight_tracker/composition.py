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
from pathlib import Path
from typing import Any

from fastapi import FastAPI

from weight_tracker.core.picture import picture_of as production_picture_of
from weight_tracker.ports import ClockPort
from weight_tracker.shell.access_gate import AccessGate, install_access_gate
from weight_tracker.shell.entry_store import SqliteEntryStore, replication_status
from weight_tracker.shell.trail import Trail
from weight_tracker.web.routes import PictureProjection, build_router


def build_app(
    db_path: Path,
    clock: ClockPort,
    passphrase_hash: str,
    session_signing_key: str,
    *,
    picture_of: PictureProjection = production_picture_of,
) -> Any:
    """Build the production ASGI app (FastAPI).

    `picture_of` is the ONE fault-injection door (ADR-014): production passes
    nothing and gets the core's picture; the acceptance composition passes a
    raising callable to exercise the degrade boundary through the seam that owns
    it. It is a door, never a fake -- Pillar 3 ("only the Clock is injected")
    still describes every adapter.

    - Opens/creates the SQLite store at db_path (WAL, synchronous=FULL) and runs its
      startup probe; probe failure => raise StartupRefused (no traffic served).
    - Wires AccessGate (argon2 passphrase verify, signed 90-day HttpOnly cookie,
      rate-limited login) around all routes except /login and /healthz.
    - Routes (driving adapters over the driving ports):
        POST /login                      AccessGate
        GET  /                           entry screen (date row above the focused decimal
                                         field, ONE hint line carrying the yesterday anchor
                                         / edit / gap states, trend glance line -- all from
                                         the same single fetched entry list; render with
                                         glance data emits trend_glance_shown, D-13/D-14)
        POST /entries                    WeightLogging.record_or_replace(date, kg, entry_ms,
                                         today?) -- `today` is the phone's own day: additive,
                                         optional, backward-compatible; absent or garbled falls
                                         back to the server's UTC day and NEVER 400s (a telemetry
                                         concern may not cost an entry). A save whose date is not
                                         the claimed day is a REPAIR, not a morning (ADR-011):
                                         its entry_ms is withheld as NULL -- zero KPI-1 speed
                                         samples via the shipped null-skip -- and its entry.saved
                                         payload carries "backdated": true for the KPI-8 count.
                                         Response shape unchanged.
                                         (saved responses carry "glance" display text for the
                                         in-place refresh; delivery emits trend_glance_shown)
        GET  /entries?scale=...          WeightHistory.entries_in(window)
        GET  /trend?scale=...            TrendProjection: the picture's series, windowed
                                         (a PURE READ since ADR-009: the trend_view_opened
                                         emission is retired -- deliberate study is counted
                                         on /graph opens and the study beacon)
        GET  /graph?view=...&scale=...   graph page (default view=trend A4; one-tap
                                         Trend/Raw toggle shares selected_time_scale)
        GET  /stats                      the trail's KPI report (ADR-015): one pure
                                         derivation over the whole trail -- entry speed,
                                         trend opens incl. trend_views_this_week rolling
                                         7 days, backdated_saves_this_week (in-app
                                         repairs, KPI-8) over that same rolling week
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
            picture_of=picture_of,
            # The trail (ADR-015): the same SQLite file is its one driven adapter.
            trail=Trail(store=store, clock=clock),
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
        raise StartupRefused(f"{adapter_name} refused startup: {failure}") from failure


def _log_startup_refused(adapter_name: str, failure: Exception) -> None:
    refusal = {"event": "health.startup.refused", "adapter": adapter_name, "error": str(failure)}
    probe_id: str | None = getattr(failure, "probe", None)
    if probe_id is not None:
        refusal["probe"] = probe_id
    print(json.dumps(refusal), file=sys.stderr)


class StartupRefused(Exception):
    """Raised when a driven-adapter startup probe fails: the app must not serve traffic."""
