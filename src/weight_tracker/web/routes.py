"""HTTP routes (driving adapters over the driving ports).

Route contract = `build_app` docstring in weight_tracker.composition (executable
spec). Dependencies arrive as function parameters (functional DI): the router is
built over the entry store port, the access gate, and the clock port.

Current scope: login, save-entry (confirmed and rejected paths, inline
messaging), history read-back, trend read-back (smoothed line, windowed
output, pure read per ADR-009), graph page (trend default lens, Trend/Raw
toggle sharing the selected window, one trend.study.opened per open),
entry screen (instant typing, yesterday anchor, ambient home.graph.shown
delivery), PWA manifest + minimal service worker (app-shell cache only,
D-11), telemetry counts with the KPI-1 speed report.
"""

from __future__ import annotations

import json
import statistics
import sys
from collections.abc import Callable, Sequence
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from weight_tracker.core.glance import GlanceSummary, quantize_rate, rate_glyph
from weight_tracker.core.types import (
    Entry,
    Rejected,
    RejectionReason,
    Saved,
    TimeScale,
    TrendPoint,
    ViewMode,
    entries_in_window,
    parse_time_scale,
    window_start,
)
from weight_tracker.core.validation import (
    bounded_day_frame,
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

ENTRY_SAVED_EVENT = "entry.saved"
#: Emission RETIRED by ADR-009 (2026-07-24): GET /trend is a pure read. The name
#: remains so /stats can keep reading the frozen-historical rows on the trail.
TREND_VIEW_OPENED_EVENT = "trend.view.opened"
TREND_GLANCE_SHOWN_EVENT = "trend.glance.shown"
#: Intent telemetry (ADR-009): intent is recorded on intent-expressing surfaces,
#: never inferred on data reads. Ambient = the front page delivering the graph;
#: deliberate = a History-page open or an explicit lens/scale tap (beacon).
HOME_GRAPH_SHOWN_EVENT = "home.graph.shown"
TREND_STUDY_OPENED_EVENT = "trend.study.opened"
TREND_STUDY_INTERACTION_EVENT = "trend.study.interaction"

#: The study beacon's closed vocabulary (ADR-009): the ONLY words a signal may
#: speak. Surface/control name the two graph surfaces and their two explicit
#: controls; value tokens derive from the core's own lens and scale sets
#: (Mandate-12: reuse, no new enums). Anything else never reaches the trail.
STUDY_SURFACES = frozenset({"home", "history"})
STUDY_CONTROLS = frozenset({"lens", "scale"})
STUDY_VALUES = frozenset(lens.value for lens in ViewMode) | frozenset(
    scale.value for scale in TimeScale
)
STUDY_VOCABULARY: dict[str, frozenset[str]] = {
    "surface": STUDY_SURFACES,
    "control": STUDY_CONTROLS,
    "value": STUDY_VALUES,
}


def parse_study_signal(body: object) -> dict[str, str] | None:
    """Total parse of a beacon body against the closed vocabulary (ADR-009).

    Pure judgment, `parse_time_scale` precedent: the validated
    {surface, control, value} tokens when every field speaks the vocabulary;
    None for ANYTHING else -- wrong shape, unknown words, non-string values.
    Free text cannot survive this gate, so it can never reach the append-only
    trail (unbounded preservation). The core judges; the shell phrases 400."""
    if not isinstance(body, dict) or set(body) != set(STUDY_VOCABULARY):
        return None
    if any(
        not isinstance(body[field], str) or body[field] not in spoken
        for field, spoken in STUDY_VOCABULARY.items()
    ):
        return None
    return {field: body[field] for field in STUDY_VOCABULARY}


#: TrendProjection driving port: read-only, derived-never-stored (ADR-004) -- a pure
#: function of the FULL entry set, windowed on the output. Wired at the composition root.
TrendProjection = Callable[[Sequence[Entry], TimeScale, date], list[TrendPoint]]

#: GlanceProjection driving port: read-only, derived-never-stored (ADR-006) -- a pure
#: function of the FULL entry set. Wired at the composition root (D-13); the glance
#: path never touches GET /trend (KPI-3 separation is structural).
GlanceProjection = Callable[[Sequence[Entry]], GlanceSummary | None]

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


def glance_display_text(summary: GlanceSummary) -> str:
    """ADR-006 pinned display: `Trend: {value:.1f} kg` with the rate segment
    ` · {glyph}{abs:.2f} kg/week` (glyph directly prefixing the quantized
    magnitude) once the 7-day entry span is earned. The core judges the numbers;
    this shell only phrases them."""
    value_text = f"Trend: {summary.trend_kg:.1f} kg"
    if summary.rate_kg_per_week is None:
        return value_text
    quantized_rate = quantize_rate(summary.rate_kg_per_week)
    return f"{value_text} · {rate_glyph(quantized_rate)}{abs(quantized_rate):.2f} kg/week"


#: Recent entries embedded for the phone-side yesterday anchor: enough to cover
#: the device-local yesterday under any legitimate skew (server day +/-
#: MAX_DEVICE_SKEW_DAYS) plus today's own entry -- never the whole record.
RECENT_ANCHOR_ENTRIES = 4


def recent_weights_map(entries: Sequence[Entry]) -> dict[str, float]:
    """The latest few logged days as {iso_day: kg} for the entry screen's inline
    script, which resolves the DEVICE-local yesterday against it (A5 extended
    to reads) -- the server never guesses the phone's calendar frame."""
    return {entry.day.isoformat(): entry.weight_kg for entry in entries[:RECENT_ANCHOR_ENTRIES]}


#: The recent list's depth (US-011, A18): the last 7 ENTRIES, never days --
#: missing days are simply absent because entries, not calendar days, are sliced.
RECENT_LIST_ENTRIES = 7


def recent_head(entries: Sequence[Entry]) -> Sequence[Entry]:
    """THE newest-first seven-entry slice (D-18/D-19, 01-04's one slice): the
    front page's recent list and the save response's hand-back both read this
    single head, so the two surfaces cannot drift apart."""
    return entries[:RECENT_LIST_ENTRIES]


def entry_row_text(day: date, weight_kg: float) -> str:
    """The ONE row grammar every entries list speaks (A18, Mandate-12):
    'Fri 24 Jul — 82.2 kg' -- weekday, day without a leading zero, month, an em
    dash, the weight at the record's own 0.1 kg precision. The History page's
    complete list (US-012) reuses this exact function -- one formatting path."""
    return f"{day:%a} {day.day} {day:%b} — {weight_kg:.1f} kg"


def recent_entry_rows(entries: Sequence[Entry]) -> list[str]:
    """The last 7 entries as display rows, newest first: a pure slice of the
    newest-first all_entries() read the front page already performs (D-18,
    zero port changes). Fewer entries -> a shorter list; none -> no rows."""
    return [entry_row_text(entry.day, entry.weight_kg) for entry in recent_head(entries)]


def complete_record_rows(entries: Sequence[Entry]) -> list[str]:
    """The COMPLETE record as display rows, newest first (US-012, D-17): the
    whole all_entries() read, never windowed by the chart's selected scale.
    Same one row grammar as the front page's recent list (Mandate-12)."""
    return [entry_row_text(entry.day, entry.weight_kg) for entry in entries]


def entry_wire_pair(entry: Entry) -> dict[str, Any]:
    """The ONE {date, weight_kg} wire shape an entry travels as: the /entries
    read-back and the save's `recent` hand-back speak it from this single place
    (D-18 single source -- the two surfaces must tell the same story)."""
    return {"date": entry.day.isoformat(), "weight_kg": entry.weight_kg}


def recent_entries_payload(entries: Sequence[Entry]) -> list[dict[str, Any]]:
    """The save response's `recent` hand-back (D-19): the SAME newest-first
    seven-entry slice the front page renders (01-04's one slice), spoken as
    {date, weight_kg} wire pairs for the client's in-place list repaint --
    route-level enrichment on the glance/confirmation precedent, port untouched."""
    return [entry_wire_pair(entry) for entry in recent_head(entries)]


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


def _log_structured(entry: dict[str, Any]) -> None:
    """One structured line on stderr: the operational trail transport (ADR-003)."""
    print(json.dumps(entry), file=sys.stderr)


def _log_auth_event(name: str) -> None:
    """Structured auth trail: auth.login.{ok,rejected,rate_limited} (ADR-003)."""
    _log_structured({"event": name})


def _log_glance_degraded(failure: Exception) -> None:
    """Structured degrade trail: the glance failed and was hidden, never silently."""
    _log_structured({"event": "trend.glance.degraded", "error": str(failure)})


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
    trend_series_in: TrendProjection,
    glance_summary_of: GlanceProjection,
    count_events_since: Callable[[str, date], int],
    entry_ms_samples_since: Callable[[str, date], list[int]],
    replication_status: Callable[[], str],
) -> APIRouter:
    router = APIRouter()

    def glance_or_degrade(entries: Sequence[Entry]) -> GlanceSummary | None:
        """Shell containment (D-13): a failing glance projection degrades to no
        glance -- absent line on the render, null on the save -- on BOTH delivery
        surfaces. The morning entry and the save are never blocked by the trend;
        the core stays pure and exception-free by contract, so any raise here is
        an injected/infrastructure fault, logged and swallowed at this boundary."""
        try:
            return glance_summary_of(entries)
        except Exception as failure:
            _log_glance_degraded(failure)
            return None

    def deliver_glance(entries: Sequence[Entry]) -> str | None:
        """One glance delivery (D-14): the display text when a glance exists, paired
        with exactly one trend.glance.shown event; None (and no event) with no data
        or on a degraded computation. No per-day dedup -- KPI-5 pairing is computed
        at read time on /stats."""
        summary = glance_or_degrade(entries)
        if summary is None:
            return None
        store.append_event(
            ts=clock.now_utc().isoformat(), name=TREND_GLANCE_SHOWN_EVENT, payload="{}"
        )
        return glance_display_text(summary)

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
        (fix-device-day-reads): the recent-days map rides inside the existing
        inline script, and the client resolves its own device-local yesterday."""
        entries = store.all_entries()
        if entries:
            # Ambient graph presence (ADR-009, KPI-7): a data-available-at-render
            # proxy, the glance precedent (Q3) -- entries exist, so the morning
            # picture is delivered, even if the client's series fetch later fails.
            # Per-delivery, no per-day dedup (D-14: pairing is computed on /stats).
            store.append_event(
                ts=clock.now_utc().isoformat(), name=HOME_GRAPH_SHOWN_EVENT, payload="{}"
            )
        return _templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "recent_weights": recent_weights_map(entries),
                "recent_entries": recent_entry_rows(entries),
                "glance_text": deliver_glance(entries),
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
        refreshed = store.all_entries()  # newest first, the just-saved day on top
        return {
            "outcome": "saved",
            "confirmation": saved.confirmation,
            "date": day.isoformat(),
            "weight_kg": weight_kg,
            # In-place refresh (D-13): the glance recomputed with today's entry rides
            # on the save response -- a route-level concern, never a port widening.
            "glance": deliver_glance(refreshed),
            # In-place list repaint (D-19, same read): the refreshed recent head.
            "recent": recent_entries_payload(refreshed),
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
        }

    @router.get("/trend")
    def trend(scale: str = "ALL", today: str | None = None) -> dict[str, Any]:
        """Smoothed trend line for the selected scale (full recompute per read, ADR-004).

        The window is framed by the phone's claimed day (?today=, validated and
        skew-bounded); event timestamps stay UTC by design. A PURE READ (ADR-009):
        the trend.view.opened emission is retired -- intent is recorded where it
        is expressed (/graph render, the study beacon), never inferred here.
        Historical trend.view.opened rows stay on the append-only trail."""
        selected_scale = time_scale_or_bad_request(scale)
        day_frame = day_frame_or_bad_request(today, clock.now_utc().date())
        points = trend_series_in(store.all_entries(), selected_scale, day_frame)
        return {
            "points": [
                {"date": point.day.isoformat(), "trend_kg": point.trend_kg} for point in points
            ]
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
        store.append_event(
            ts=clock.now_utc().isoformat(), name=TREND_STUDY_OPENED_EVENT, payload="{}"
        )
        return _templates.TemplateResponse(
            request=request,
            name="graph.html",
            context={
                "view": view,
                "scale": time_scale_or_bad_request(scale).value,
                "history_rows": complete_record_rows(store.all_entries()),
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
            store.append_event(
                ts=clock.now_utc().isoformat(),
                name=TREND_STUDY_INTERACTION_EVENT,
                payload=json.dumps(signal),
            )
        except Exception as failure:
            _log_study_append_degraded(failure)
        return Response(status_code=204)

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
            # FROZEN-HISTORICAL (ADR-009 instrument switch, labeled per Forge
            # condition 2): the trend.view.opened emission retired 2026-07-24;
            # this counter reads the preserved pre-switch rows and can only age.
            # The live KPI-3 counter is trend_study_this_week below.
            "trend_view_opened_count": store.count_events(TREND_VIEW_OPENED_EVENT),
            # Ambient glance deliveries over the SAME rolling week as the deliberate
            # trend views beside it (KPI-3/KPI-5 separation read from the real trail);
            # historical seeding/backdated saves age out of the window by construction.
            "trend_glance_shown_count": count_events_since(
                TREND_GLANCE_SHOWN_EVENT, kpi_week_start
            ),
            "trend_views_this_week": count_events_since(TREND_VIEW_OPENED_EVENT, kpi_week_start),
            # KPI-3 live (ADR-009, Q2): raw rolling-week count of deliberate study --
            # History-page opens + explicit lens/scale taps -- same week frame as
            # trend_views_this_week; any session collapse is a read-time refinement.
            "trend_study_this_week": (
                count_events_since(TREND_STUDY_OPENED_EVENT, kpi_week_start)
                + count_events_since(TREND_STUDY_INTERACTION_EVENT, kpi_week_start)
            ),
            # KPI-7 (ADR-009): ambient morning-graph deliveries, same rolling week.
            "home_graph_shown_this_week": count_events_since(
                HOME_GRAPH_SHOWN_EVENT, kpi_week_start
            ),
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
