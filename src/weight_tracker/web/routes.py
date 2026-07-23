"""HTTP routes (driving adapters over the driving ports).

Route contract = `build_app` docstring in weight_tracker.composition (executable
spec). Dependencies arrive as function parameters (functional DI): the router is
built over the entry store port, the access gate, and the clock port.

Current scope: login, save-entry (confirmed and rejected paths, inline
messaging), history read-back, trend read-back (smoothed line, windowed
output, trend-view telemetry), graph page (trend default lens, Trend/Raw
toggle sharing the selected window), entry screen (instant typing,
yesterday anchor), PWA manifest + minimal service worker (app-shell cache
only, D-11), telemetry counts with the KPI-1 speed report.
"""

from __future__ import annotations

import json
import statistics
import sys
from collections.abc import Callable, Sequence
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from weight_tracker.core.types import (
    Entry,
    Rejected,
    RejectionReason,
    Saved,
    TimeScale,
    TrendPoint,
    entries_in_window,
    parse_time_scale,
    window_start,
)
from weight_tracker.core.validation import validate_entry_date, validate_weight
from weight_tracker.ports import ClockPort, EntryStorePort
from weight_tracker.shell.access_gate import (
    SESSION_COOKIE,
    SESSION_MAX_AGE_SECONDS,
    THROTTLED_MESSAGE,
    WRONG_PASSPHRASE_MESSAGE,
    AccessGate,
    Throttled,
    Unlocked,
    door_page,
    prefers_html,
)
from weight_tracker.shell.access_gate import (
    Rejected as PassphraseRejected,
)

ENTRY_SAVED_EVENT = "entry.saved"
TREND_VIEW_OPENED_EVENT = "trend.view.opened"

#: TrendProjection driving port: read-only, derived-never-stored (ADR-004) -- a pure
#: function of the FULL entry set, windowed on the output. Wired at the composition root.
TrendProjection = Callable[[Sequence[Entry], TimeScale, date], list[TrendPoint]]

#: Shell translation of the core's closed RejectionReason set into inline messages (C6b/C6c).
#: The core judges; the shell phrases. No validation logic lives here.
REJECTION_MESSAGES: dict[RejectionReason, str] = {
    RejectionReason.OUT_OF_RANGE: "The value must be between 30.0 and 250.0 kg.",
    RejectionReason.BAD_PRECISION: "The value is finer than the 0.1 kg scale.",
    RejectionReason.NOT_A_WEIGHT: "That is not a weight.",
    RejectionReason.MISSING_VALUE: "A weight is required.",
    RejectionReason.FUTURE_DATE: "Future dates cannot be logged.",
    RejectionReason.BAD_DATE: "The date is not recognisable.",
}


def time_scale_or_bad_request(raw_scale: str) -> TimeScale:
    """Shell translation of an unparseable ?scale= token into HTTP 400 (C6:
    hostile query input never 500s). Tokens are strict; the 400 message lists
    the valid scales for correction. The core parses; this shell phrases."""
    scale = parse_time_scale(raw_scale)
    if scale is None:
        valid_scales = ", ".join(known.value for known in TimeScale)
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scale {raw_scale!r}. Valid scales: {valid_scales}.",
        )
    return scale


def _rejected_save(rejected: Rejected, typed_value: str) -> dict[str, Any]:
    """Rejected-save response: closed reason, inline message, typed value kept for correction."""
    return {
        "outcome": "rejected",
        "reason": rejected.reason.value,
        "message": REJECTION_MESSAGES[rejected.reason],
        "echo": typed_value,
    }


_templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
_static_dir = Path(__file__).parent / "static"

#: PWA install manifest (D-11): enough for the tracker to offer itself for the
#: home screen; the paired service worker caches the app shell only.
PWA_MANIFEST: dict[str, Any] = {
    "name": "Weight Tracker",
    "short_name": "Weight",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#ffffff",
    "theme_color": "#111111",
    "icons": [{"src": "/static/icon.svg", "sizes": "any", "type": "image/svg+xml"}],
}


def weight_on(entries: Sequence[Entry], day: date) -> float | None:
    """The weight logged for `day`, if any -- read-only WeightHistory lookup
    (yesterday anchor degrades gracefully to None on the first morning)."""
    return next((entry.weight_kg for entry in entries if entry.day == day), None)


def speed_summary(samples: Sequence[int]) -> dict[str, Any]:
    """KPI-1 speed report over client-measured entry durations: median, p90, count.

    Pure summary of whatever window the caller selected; an empty window reports
    honest nulls rather than a pretended speed."""
    if not samples:
        return {"median_ms": None, "p90_ms": None, "sample_count": 0}
    ordered = sorted(samples)
    return {
        "median_ms": statistics.median(ordered),
        "p90_ms": _p90(ordered),
        "sample_count": len(ordered),
    }


def _p90(ordered_samples: Sequence[int]) -> float:
    """Worst-case-but-one duration: the 90th percentile (last decile boundary,
    inclusive method so it never extrapolates past the observed worst case)."""
    if len(ordered_samples) == 1:
        return float(ordered_samples[0])
    return float(statistics.quantiles(ordered_samples, n=10, method="inclusive")[-1])


def _kpi_week_start(today: date) -> date:
    """Rolling KPI week (/stats `trend_views_this_week`): exactly the 1W scale
    window -- the core's single pinned "last N days inclusive of today" rule
    applied to the event trail (no second copy of the calendar arithmetic)."""
    week_start = window_start(TimeScale.ONE_WEEK, today)
    return week_start if week_start is not None else today  # None is ALL-only, 1W is bounded


def _unlocked_response(wants_page: bool) -> Response:
    """Success has two faces: the browser is sent home to the entry screen (303
    See Other, so the form POST becomes a GET); API clients get the JSON receipt."""
    if wants_page:
        return RedirectResponse("/", status_code=303)
    return JSONResponse({"status": "unlocked"})


def _log_auth_event(name: str) -> None:
    """Structured auth trail: auth.login.{ok,rejected,rate_limited} (ADR-003)."""
    print(json.dumps({"event": name}), file=sys.stderr)


def build_router(
    *,
    store: EntryStorePort,
    gate: AccessGate,
    clock: ClockPort,
    trend_series_in: TrendProjection,
    count_events_since: Callable[[str, date], int],
    entry_ms_samples_since: Callable[[str, date], list[int]],
    replication_status: Callable[[], str],
) -> APIRouter:
    router = APIRouter()

    @router.post("/login")
    async def login(request: Request) -> Response:
        """The login door serves both clients: a browser form submit (Accept:
        text/html) is answered with pages -- 303 home on success, the door page
        re-rendered on rejection; API clients keep the JSON contract. The
        AccessGate judges; this route only phrases the verdict per client."""
        form = parse_qs((await request.body()).decode())
        passphrase = form.get("passphrase", [""])[0]
        wants_page = prefers_html(request)
        match gate.attempt_login(passphrase, now=clock.now_utc()):
            case Throttled():
                _log_auth_event("auth.login.rate_limited")
                if wants_page:
                    return door_page(request, rejection=THROTTLED_MESSAGE, status_code=429)
                return JSONResponse({"detail": "too many attempts"}, status_code=429)
            case PassphraseRejected():
                _log_auth_event("auth.login.rejected")
                if wants_page:
                    return door_page(request, rejection=WRONG_PASSPHRASE_MESSAGE, status_code=401)
                return JSONResponse({"detail": "wrong passphrase"}, status_code=401)
            case Unlocked(session_token=session_token):
                _log_auth_event("auth.login.ok")
                response = _unlocked_response(wants_page)
                response.set_cookie(
                    SESSION_COOKIE,
                    session_token,
                    max_age=SESSION_MAX_AGE_SECONDS,
                    httponly=True,
                    samesite="lax",
                )
                return response
        raise AssertionError("unreachable: LoginOutcome is a closed choice type")

    @router.get("/")
    def entry_screen(request: Request) -> Response:
        """Five-second entry screen: focused decimal field, yesterday's weight as
        the anchor beside the input (absent gracefully on the first morning)."""
        yesterday = clock.now_utc().date() - timedelta(days=1)
        return _templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"yesterday_kg": weight_on(store.all_entries(), yesterday)},
        )

    @router.get("/manifest.webmanifest")
    def manifest() -> JSONResponse:
        """PWA install manifest: the tracker offers itself for the home screen."""
        return JSONResponse(PWA_MANIFEST, media_type="application/manifest+json")

    @router.get("/sw.js")
    def service_worker() -> FileResponse:
        """Minimal service worker served at root scope so the app shell falls under
        it. App-shell cache only -- saves are never queued offline (D-11)."""
        return FileResponse(_static_dir / "sw.js", media_type="text/javascript")

    @router.post("/entries")
    async def save_entry(request: Request) -> dict[str, Any]:
        submitted = await request.json()
        typed_weight = str(submitted.get("weight", ""))
        weight_kg = validate_weight(typed_weight)
        if isinstance(weight_kg, Rejected):
            return _rejected_save(weight_kg, typed_value=typed_weight)
        day = validate_entry_date(
            str(submitted.get("date", "")), server_utc_today=clock.now_utc().date()
        )
        if isinstance(day, Rejected):
            return _rejected_save(day, typed_value=typed_weight)
        logged_at = clock.now_utc().isoformat()
        entry = Entry(day=day, weight_kg=weight_kg, entry_ms=submitted.get("entry_ms"))
        store.upsert(entry, logged_at=logged_at)
        store.append_event(
            ts=logged_at,
            name=ENTRY_SAVED_EVENT,
            payload=json.dumps({"date": day.isoformat(), "entry_ms": entry.entry_ms}),
        )
        saved = Saved(day=day, weight_kg=weight_kg)
        return {
            "outcome": "saved",
            "confirmation": saved.confirmation,
            "date": day.isoformat(),
            "weight_kg": weight_kg,
        }

    @router.get("/entries")
    def history(scale: str = "ALL") -> dict[str, Any]:
        selected_scale = time_scale_or_bad_request(scale)
        stored = store.all_entries()  # newest first
        shown = entries_in_window(stored, selected_scale, today=clock.now_utc().date())
        return {
            "entries": [
                {"date": entry.day.isoformat(), "weight_kg": entry.weight_kg} for entry in shown
            ],
            "invite_first_log": not stored,
        }

    @router.get("/trend")
    def trend(scale: str = "ALL") -> dict[str, Any]:
        """Smoothed trend line for the selected scale (full recompute per read, ADR-004).

        Every open is a KPI-3 engagement signal: one trend.view.opened event goes
        onto the append-only trail before the line is returned."""
        selected_scale = time_scale_or_bad_request(scale)
        opened_at = clock.now_utc()
        points = trend_series_in(store.all_entries(), selected_scale, opened_at.date())
        store.append_event(
            ts=opened_at.isoformat(),
            name=TREND_VIEW_OPENED_EVENT,
            payload=json.dumps({"scale": selected_scale.value}),
        )
        return {
            "points": [
                {"date": point.day.isoformat(), "trend_kg": point.trend_kg} for point in points
            ]
        }

    @router.get("/graph")
    def graph_page(request: Request, view: str = "trend", scale: str = "3M") -> Response:
        """Graph page (uPlot, vendored). Trend is the default lens on open (A4);
        view and scale round-trip through the query string, so toggling the lens
        never loses the chosen window. The core windows; this shell renders."""
        return _templates.TemplateResponse(
            request=request,
            name="graph.html",
            context={"view": view, "scale": time_scale_or_bad_request(scale).value},
        )

    @router.get("/static/{asset_name}")
    def static_asset(asset_name: str) -> FileResponse:
        """Vendored front-end assets (uPlot; no CDN). Single path segment only."""
        return FileResponse(_static_dir / asset_name)

    @router.get("/stats")
    def stats() -> dict[str, Any]:
        """KPI query surface. `speed` is the 7-day KPI-1 report; the five-second
        threshold is a weekly human judgment, never a gate here (DEVOPS H-003)."""
        kpi_week_start = _kpi_week_start(clock.now_utc().date())
        return {
            "entry_logged_count": store.count_events(ENTRY_SAVED_EVENT),
            "trend_view_opened_count": store.count_events(TREND_VIEW_OPENED_EVENT),
            "trend_views_this_week": count_events_since(TREND_VIEW_OPENED_EVENT, kpi_week_start),
            "speed": speed_summary(entry_ms_samples_since(ENTRY_SAVED_EVENT, kpi_week_start)),
        }

    @router.get("/healthz")
    def healthz() -> dict[str, str]:
        """Unauthenticated operational surface: status only, never record data.

        Serving at all means every startup probe passed (build_app refuses otherwise)."""
        return {
            "status": "ok",
            "startup_probe": "passed",
            "replication": replication_status(),
        }

    return router
