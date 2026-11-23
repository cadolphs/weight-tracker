"""HTTP routes (driving adapters over the driving ports).

Route contract = `build_app` docstring in weight_tracker.composition (executable
spec). Dependencies arrive as function parameters (functional DI): the router is
built over the entry store port, the access gate, and the clock port.

Current scope: login, save-entry (confirmed and rejected paths, inline
messaging), history read-back, trend read-back (smoothed line, windowed
output, pure read per ADR-009), graph page (trend default lens, Trend/Raw
toggle sharing the selected window, one trend.study.opened per open),
entry screen (instant typing, date row above the field, one hint line,
ambient home.graph.shown delivery), PWA manifest + minimal service worker
(app-shell cache only,
D-11), and the trail's KPI report on /stats (ADR-015). Routes decide WHEN an
event is marked (ADR-009) and call the trail; the trail stamps, stores and
derives the report.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable, Sequence
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from weight_tracker.core.axis import y_axis_range
from weight_tracker.core.picture import Picture, trendless_picture_of
from weight_tracker.core.trail import EventName, parse_study_signal
from weight_tracker.core.trend import windowed_series
from weight_tracker.core.types import (
    Entry,
    Rejected,
    RejectionReason,
    Saved,
    TimeScale,
    entries_in_window,
    parse_time_scale,
)
from weight_tracker.core.validation import (
    bounded_day_frame,
    is_backdated,
    validate_entry_date,
    validate_weight,
)
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
from weight_tracker.shell.trail import Trail
from weight_tracker.web.views import (
    ENTRY_COLUMN_HEADINGS,
    axis_range_wire,
    complete_record_rows,
    entry_wire_pair,
    glance_display_text,
    recent_entries_payload,
    recent_entry_rows,
)

#: PictureProjection driving port (ADR-014): read-only, derived-never-stored -- ONE
#: pure function of the FULL entry set yielding everything the pages know about the
#: record. Wired at the composition root; the only fault-injection door the
#: acceptance composition uses.
PictureProjection = Callable[[Sequence[Entry]], Picture]

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


def day_frame_or_bad_request(claimed_today: str | None, server_utc_today: date) -> date:
    """Resolve the day framing a read window (A5 extended to reads).

    The phone claims its local day via ?today=; absent (curl/API compat), the
    server's own UTC day frames the window as before. A garbled claim is turned
    away with 400 (C6: total parse, precedent `parse_time_scale`). A parseable
    claim outside the plausible device window is clamped by the core's
    `bounded_day_frame` -- one copy of the calendar rule, shared with the
    backdated-save classifier (ADR-011): reads stay forgiving where saves stay
    strict, so a phone with a wildly wrong clock still receives a sensible,
    bounded window.
    """
    if claimed_today is None:
        return server_utc_today
    framed = bounded_day_frame(claimed_today, server_utc_today)
    if framed is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unrecognisable day {claimed_today!r}. Expected an ISO date (YYYY-MM-DD).",
        )
    return framed


def device_day_frame(claimed_today: object, server_utc_today: date) -> date:
    """Resolve the day a SAVE is judged against (ADR-011): the phone's own day.

    Saves are strict where reads are forgiving -- and here that asymmetry runs
    the other way round. `day_frame_or_bad_request` turns a garbled `?today=`
    away with 400 because a read window is the answer being asked for; a save's
    claim is only telemetry, and a telemetry concern must never cost an entry.
    So an absent claim (curl, every shipped API client) and a garbled one alike
    fall back to the server's UTC day, and this function never raises. A
    parseable claim is believed only as far as a real timezone could carry it --
    the core's `bounded_day_frame` clamps it -- so the one newly trusted input,
    a lying device clock, is contained by construction while the authoritative
    no-future rule still stands in front of it.
    """
    if not isinstance(claimed_today, str):
        return server_utc_today
    framed = bounded_day_frame(claimed_today, server_utc_today)
    return server_utc_today if framed is None else framed


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
    # Calm-theme palette alignment (ADR-007 §4): single-value colors matching the
    # light-scheme tokens in theme.css (Q4 resolved: no per-scheme meta juggling).
    "background_color": "#FAFAF8",
    "theme_color": "#1A1A1A",
    "icons": [{"src": "/static/icon.svg", "sizes": "any", "type": "image/svg+xml"}],
}


def _unlocked_response(wants_page: bool) -> Response:
    """Success has two faces: the browser is sent home to the entry screen (303
    See Other, so the form POST becomes a GET); API clients get the JSON receipt."""
    if wants_page:
        return RedirectResponse("/", status_code=303)
    return JSONResponse({"status": "unlocked"})


def _log_structured(entry: dict[str, Any]) -> None:
    """One structured line on stderr: the operational trail transport (ADR-003)."""
    print(json.dumps(entry), file=sys.stderr)


def _log_auth_event(name: str) -> None:
    """Structured auth trail: auth.login.{ok,rejected,rate_limited} (ADR-003)."""
    _log_structured({"event": name})


def _log_picture_degraded(failure: Exception) -> None:
    """Structured degrade trail (ADR-014): the picture failed, so the glance line
    is hidden and the lists render their raw column with empty trend cells
    (D12/A37) -- never silently."""
    _log_structured({"event": "picture.degraded", "error": str(failure)})


def _log_study_append_degraded(failure: Exception) -> None:
    """Structured degrade trail: a study mark could not be appended (Forge
    condition 3) -- the beacon still answers 2xx, fire-and-forget never
    becomes a client-visible fault, and the loss is never silent."""
    _log_structured({"event": "trend.study.append_degraded", "error": str(failure)})


def build_router(
    *,
    store: EntryStorePort,
    gate: AccessGate,
    clock: ClockPort,
    picture_of: PictureProjection,
    trail: Trail,
    replication_status: Callable[[], str],
) -> APIRouter:
    router = APIRouter()

    def picture_or_degrade(entries: Sequence[Entry]) -> Picture:
        """Shell containment, ONE boundary (ADR-014; D-13/D-34 unified): a failing
        picture degrades to the TRENDLESS picture -- no glance line on the render,
        null glance and null trend cells on the save, empty trend cells in every
        list -- while the raw record, the prefill map and the date row stand. The
        morning entry and the save are never blocked by the trend; the core is pure
        and exception-free by contract, so any raise here is an injected or
        infrastructure fault, logged and swallowed at this boundary."""
        try:
            return picture_of(entries)
        except Exception as failure:
            _log_picture_degraded(failure)
            return trendless_picture_of(entries)

    def deliver_glance(picture: Picture) -> str | None:
        """One glance delivery (D-14): the display text when a glance exists, paired
        with exactly one trend.glance.shown event; None (and no event) with no data
        or on a trendless picture. No per-day dedup -- KPI-5 pairing is computed
        at read time on /stats."""
        if picture.glance is None:
            return None
        trail.mark(EventName.TREND_GLANCE_SHOWN)
        return glance_display_text(picture.glance)

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
        the anchor beside the input (absent gracefully on the first morning), and
        the trend glance derived from the SAME fetched entry list (zero added I/O,
        D-13); a render with glance data is one counted delivery (D-14).

        The yesterday anchor is framed by the PHONE, not the server clock
        (fix-device-day-reads): the record's day-to-weight map rides inside the
        existing inline script, and the client resolves its own device-local
        yesterday against it. That same one map answers ANY stored day the
        picker lands on (ADR-010) -- one read, one map, no disagreement.

        The date row above the field is framed from both ends and by both
        parties (D-25): the phone sets where it opens and how far forward it
        reaches, because only it knows its own calendar day (A5); the server
        supplies how far BACK it reaches, from the same read -- the record's
        first day minus a year. All three are UX assist; the save path's
        no-future rule is untouched and still authoritative."""
        entries = store.all_entries()
        picture = picture_or_degrade(entries)
        if entries:
            # Ambient graph presence (ADR-009, KPI-7): a data-available-at-render
            # proxy, the glance precedent (Q3) -- entries exist, so the morning
            # picture is delivered, even if the client's series fetch later fails.
            # Per-delivery, no per-day dedup (D-14: pairing is computed on /stats).
            trail.mark(EventName.HOME_GRAPH_SHOWN)
        return _templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "record_weights": picture.record_weights,
                "earliest_pickable_day": picture.earliest_pickable_day,
                "entry_columns": ENTRY_COLUMN_HEADINGS,
                "recent_entries": recent_entry_rows(picture),
                "glance_text": deliver_glance(picture),
            },
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
        """Save one day's weight, and judge whether it was a morning or a repair.

        The picked day and the phone's own day arrive independently (`date` and
        the additive, optional `today`), so "a repair is never counted as a
        morning" is falsifiable at this boundary rather than trusted as a client
        convention (ADR-011). Order is load-bearing: the weight and the date are
        validated FIRST, so only accepted dates are ever classified and the
        server's no-future rule stays authoritative.
        """
        submitted = await request.json()
        typed_weight = str(submitted.get("weight", ""))
        weight_kg = validate_weight(typed_weight)
        if isinstance(weight_kg, Rejected):
            return _rejected_save(weight_kg, typed_value=typed_weight)
        server_utc_today = clock.now_utc().date()
        day = validate_entry_date(str(submitted.get("date", "")), server_utc_today=server_utc_today)
        if isinstance(day, Rejected):
            return _rejected_save(day, typed_value=typed_weight)
        backdated = is_backdated(day, device_day_frame(submitted.get("today"), server_utc_today))
        logged_at = clock.now_utc().isoformat()
        entry = Entry(
            day=day,
            weight_kg=weight_kg,
            # KPI-1 purity is STRUCTURAL, not a query rule: a repair carries no
            # timing at all, in the row or on the trail, so the report's null-skip
            # (`kpi_report`, ADR-015) yields it zero speed samples. "A slow
            # backfill dragged the weekly median" cannot be represented.
            entry_ms=None if backdated else submitted.get("entry_ms"),
        )
        store.upsert(entry, logged_at=logged_at)
        # ONE event per save (D-23): the verdict travels as a payload word, never
        # a second event name -- the repair counter reads it where the timing is
        # withheld, so the two KPIs can never disagree about the same save.
        trail.mark(
            EventName.ENTRY_SAVED,
            {"date": day.isoformat(), "entry_ms": entry.entry_ms, "backdated": backdated},
        )
        saved = Saved(day=day, weight_kg=weight_kg)
        # One picture of the refreshed record (ADR-014): the glance and the recent
        # hand-back below read the same smoothing, so they cannot disagree.
        picture = picture_or_degrade(store.all_entries())
        return {
            "outcome": "saved",
            "confirmation": saved.confirmation,
            "date": day.isoformat(),
            "weight_kg": weight_kg,
            # In-place refresh (D-13): the glance recomputed with today's entry rides
            # on the save response -- a route-level concern, never a port widening.
            "glance": deliver_glance(picture),
            # In-place list repaint (D-19, same read): the refreshed recent head.
            "recent": recent_entries_payload(picture),
        }

    @router.get("/entries")
    def history(scale: str = "ALL", today: str | None = None) -> dict[str, Any]:
        selected_scale = time_scale_or_bad_request(scale)
        stored = store.all_entries()  # newest first
        day_frame = day_frame_or_bad_request(today, clock.now_utc().date())
        shown = entries_in_window(stored, selected_scale, today=day_frame)
        return {
            "entries": [entry_wire_pair(entry) for entry in shown],
            "invite_first_log": not stored,
            # The honest axis over the exact windowed series served above (ADR-012).
            "y_range": axis_range_wire(y_axis_range([entry.weight_kg for entry in shown])),
        }

    @router.get("/trend")
    def trend(scale: str = "ALL", today: str | None = None) -> dict[str, Any]:
        """Smoothed trend line for the selected scale (full recompute per read, ADR-004).

        The window is framed by the phone's claimed day (?today=, validated and
        skew-bounded); event timestamps stay UTC by design. A PURE READ (ADR-009):
        the trend.view.opened emission is retired -- intent is recorded where it
        is expressed (/graph render, the study beacon), never inferred here.
        Historical trend.view.opened rows stay on the append-only trail.
        `y_range` is the honest axis over exactly these points (ADR-012)."""
        selected_scale = time_scale_or_bad_request(scale)
        day_frame = day_frame_or_bad_request(today, clock.now_utc().date())
        # No degrade boundary here on purpose: a broken series must not pretend to
        # answer (the chart's absent-area degrade is client-side, ADR-008), so the
        # picture is built directly and a failure surfaces as a failed read.
        points = windowed_series(picture_of(store.all_entries()).series, selected_scale, day_frame)
        return {
            "points": [
                {"date": point.day.isoformat(), "trend_kg": point.trend_kg} for point in points
            ],
            "y_range": axis_range_wire(y_axis_range([point.trend_kg for point in points])),
        }

    @router.get("/graph")
    def graph_page(request: Request, view: str = "trend", scale: str = "3M") -> Response:
        """Graph page (uPlot, vendored). Trend is the default lens on open (A4);
        view and scale round-trip through the query string, so toggling the lens
        never loses the chosen window. The core windows; this shell renders.

        A History-page open IS deliberate trend study (ADR-009, KPI-3): one
        trend.study.opened event per open, regardless of the ?view=/?scale= deep link.

        The complete record rides beneath the chart (US-012, D-17): server-rendered
        from the same newest-first all_entries() read the raw plot draws, ALWAYS
        the whole record regardless of the selected window; an empty record
        renders no list (the first-log invite stands alone, A16)."""
        trail.mark(EventName.TREND_STUDY_OPENED)
        recorded = store.all_entries()
        return _templates.TemplateResponse(
            request=request,
            name="graph.html",
            context={
                "view": view,
                "scale": time_scale_or_bad_request(scale).value,
                "entry_columns": ENTRY_COLUMN_HEADINGS,
                "history_rows": complete_record_rows(recorded, picture_or_degrade(recorded)),
            },
        )

    @router.post("/telemetry/trend-study")
    async def study_beacon(request: Request) -> Response:
        """Deliberate-study beacon (ADR-009, KPI-3): one explicit lens/scale tap
        on either graph surface, fire-and-forget, behind the AccessGate like
        every record route. The pure vocabulary gate judges the body; a signal
        speaking the closed vocabulary appends exactly one
        trend.study.interaction carrying the VALIDATED tokens only. Anything
        else -- unparseable, misshapen, unknown words -- is answered 400 with
        the trail untouched. A failing append is swallowed with a structured
        log (Forge condition 3): the beacon answers only 2xx or 400, never 500."""
        try:
            submitted = await request.json()
        except Exception:  # not JSON at all: a garbled signal, never a server error
            submitted = None
        signal = parse_study_signal(submitted)
        if signal is None:
            return JSONResponse({"detail": "unknown study vocabulary"}, status_code=400)
        try:
            trail.mark(EventName.TREND_STUDY_INTERACTION, signal)
        except Exception as failure:
            _log_study_append_degraded(failure)
        return Response(status_code=204)

    @router.get("/static/{asset_name}")
    def static_asset(asset_name: str) -> FileResponse:
        """Vendored front-end assets (uPlot; no CDN). Single path segment only."""
        return FileResponse(_static_dir / asset_name)

    @router.get("/stats")
    def stats() -> dict[str, Any]:
        """KPI query surface: the trail's weekly report (ADR-015). `speed` is the
        7-day KPI-1 report; the five-second threshold is a weekly human judgment,
        never a gate here (DEVOPS H-003)."""
        return trail.report()

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
