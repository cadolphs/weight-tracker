"""Tier A acceptance composition facade -- production composition root, typed services.

Pillar 3: the SUT is built EXCLUSIVELY via `weight_tracker.composition.build_app`
(production wiring). Real SQLite on tmp_path (prod pragmas); the ONLY fake is the
Clock (driven external / non-deterministic). Session-age checks in AccessGate are
judged against the injected clock (testability contract for the 90-day scenarios).

Mandate-12: all assertion/business logic for steps lives HERE (single source of
truth); step bodies delegate in <=2 statements. Mandate 8: every mutating flow is
asserted with `assert_state_delta` over a port-exposed universe:

    record.entries                  -- (iso_date, weight_kg) pairs via WeightHistory
    telemetry.entry_logged_count    -- via the KPI query surface
    telemetry.trend_view_opened_count

HTTP surface contract (executable spec for DELIVER -- see build_app docstring):
    POST /login {passphrase}                 -> 200 + session cookie | 401 | 429 (throttled)
    GET  /entries?scale=<1W|1M|3M|6M|1Y|ALL> -> {"entries":[{"date","weight_kg"}...newest first],
                                                 "invite_first_log": bool}
    POST /entries {date, weight, entry_ms?,
                   today?}                   -> {"outcome":"saved","confirmation":...,
                                                 "date","weight_kg"}
                                              (`today` = the phone's own day, ADR-011:
                                               additive, optional, backward-compatible;
                                               absent/garbled falls back to the server's
                                               UTC day and NEVER 400s. A save whose date
                                               is not the claimed day is BACKDATED: its
                                               entry_ms is withheld (0 KPI-1 samples) and
                                               its entry.saved payload carries
                                               "backdated": true)
                                              | {"outcome":"rejected",
                                                 "reason":<RejectionReason value>,
                                                 "echo":<raw input>}   (401 when locked)
    GET  /trend?scale=...                    -> {"points":[{"date","trend_kg"}...]}
                                                (pure read, ADR-009 -- no event)
    GET  /graph?view=trend|raw&scale=...     -> HTML with data-view=... data-scale=...
                                                (+1 trend.study.opened per open)
    GET  /                                   -> entry screen HTML (autofocus, inputmode="decimal",
                                                "yesterday: X kg" when it exists)
    GET  /stats                              -> {"entry_logged_count","trend_view_opened_count",
                                                 "trend_views_this_week" (both frozen-historical
                                                 since ADR-009), "trend_study_this_week",
                                                 "home_graph_shown_this_week",
                                                 "backdated_saves_this_week" (KPI-8 repairs),
                                                 "speed":{"median_ms","p90_ms","sample_count"}}
    GET  /healthz                            -> 200 {"status":"ok",...} without auth
    GET  /manifest.webmanifest               -> 200 PWA manifest
"""

from __future__ import annotations

import json
import os
import re
import stat
import time
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from argon2 import PasswordHasher
from domain_types import (
    CONTRAST_CONTRACT,
    GARBLED_DAY_CLAIM,
    MIN_CONTRAST_RATIO,
    TEST_PASSPHRASE,
    ColorScheme,
    ContrastClass,
    DayClaim,
    RateDisposition,
    RejectionReason,
    Screen,
    TimeScale,
    TrendDirection,
    ViewMode,
    contrast_ratio,
    dark_override_names,
    day_label,
    hex_colors_in,
    parse_day,
    scheme_token_maps,
)
from fake_clock import FakeClock
from state_delta import assert_state_delta, set_to, unchanged

from weight_tracker.composition import StartupRefused, build_app
from weight_tracker.core.trend import trend_series
from weight_tracker.core.types import Entry

UNIVERSE = {
    "record.entries",
    "telemetry.entry_logged_count",
    "telemetry.trend_view_opened_count",
}

#: Glance-aware universe (US-007). The three shared slots stay untouched for the
#: pre-existing scenarios (their universes are their own declared promises); the
#: glance scenarios additionally track the glance-delivery counter.
GLANCE_UNIVERSE = UNIVERSE | {"telemetry.trend_glance_shown_count"}

#: /stats key for glance deliveries (grammar: `trend.view.opened` -> trend_view_opened_count).
GLANCE_COUNT_KEY = "trend_glance_shown_count"

WRONG_PASSPHRASE = "not-the-passphrase"
SESSION_SIGNING_KEY = "test-session-signing-key"


class TrackerComposition:
    """One production app instance per scenario, plus typed services over it."""

    def __init__(self, db_path: Path, fake_clock: FakeClock) -> None:
        self.db_path = db_path
        self.fake_clock = fake_clock
        self.device_day: date | None = None  # phone-local day override (timezone skew)
        self.passphrase_hash = PasswordHasher().hash(TEST_PASSPHRASE)
        self._app: Any = None
        self._actor: Any = None
        self._observer: Any = None
        self.access = AccessService(self)
        self.logging = LoggingService(self)
        self.history = HistoryService(self)
        self.trend = TrendService(self)
        self.graph = GraphService(self)
        self.screen = ScreenService(self)
        self.stats = StatsService(self)
        self.health = HealthService(self)
        self.system = SystemService(self)
        self.clock = ClockService(self)
        self.glance = GlanceService(self)
        self.theme = ThemeService(self)
        self.day_frame = DayFrameService(self)
        self.home_graph = HomeGraphService(self)
        self.recent_list = RecentListService(self)
        self.history_record = HistoryRecordService(self)
        self.study = StudyService(self)
        self.dated_entry = DatedEntryService(self)

    # -- composition root (lazy: nothing is built until first use) ----------------

    def _build(self) -> Any:
        if self._app is None:
            self._app = build_app(
                db_path=self.db_path,
                clock=self.fake_clock,
                passphrase_hash=self.passphrase_hash,
                session_signing_key=SESSION_SIGNING_KEY,
            )
        return self._app

    def actor(self) -> Any:
        from fastapi.testclient import TestClient

        if self._actor is None:
            self._actor = TestClient(self._build(), raise_server_exceptions=True)
        return self._actor

    def observer(self) -> Any:
        """Separate authed session used only for universe capture / read-back."""
        from fastapi.testclient import TestClient

        if self._observer is None:
            self._observer = TestClient(self._build(), raise_server_exceptions=True)
            resp = self._observer.post("/login", data={"passphrase": TEST_PASSPHRASE})
            assert resp.status_code in (200, 303), f"observer login failed: {resp.status_code}"
        return self._observer

    def capture_universe(self) -> dict[str, Any]:
        obs = self.observer()
        entries = obs.get("/entries", params={"scale": TimeScale.ALL.value}).json()["entries"]
        stats = obs.get("/stats").json()
        return {
            "record.entries": tuple((e["date"], e["weight_kg"]) for e in entries),
            "telemetry.entry_logged_count": stats["entry_logged_count"],
            "telemetry.trend_view_opened_count": stats["trend_view_opened_count"],
        }

    def resolve_day(self, spec: str) -> date:
        if spec == "today":
            return self.device_day or self.fake_clock.today()
        if spec == "yesterday":
            return (self.device_day or self.fake_clock.today()) - timedelta(days=1)
        return parse_day(spec)


class _Service:
    def __init__(self, comp: TrackerComposition) -> None:
        self.comp = comp


class ClockService(_Service):
    def set_today(self, day: date) -> None:
        self.comp.fake_clock.set_today(day)

    def set_device_day(self, day: date) -> None:
        self.comp.device_day = day

    def days_pass(self, days: int) -> None:
        self.comp.fake_clock.advance_days(days)


#: Browser-flavored navigation: what the phone sends when Clemens taps the icon.
BROWSER_HTML = {"accept": "text/html"}


class AccessService(_Service):
    def visit_in_browser(self) -> Any:
        """A human page navigation (HTML-accepting GET of the app root)."""
        return self.comp.actor().get("/", headers=BROWSER_HTML)

    def enter_passphrase_at_door(self, passphrase: str) -> Any:
        """Submit the door's form the way a browser would: HTML-accepting, redirects followed."""
        return self.comp.actor().post(
            "/login",
            data={"passphrase": passphrase},
            headers=BROWSER_HTML,
            follow_redirects=True,
        )

    def assert_passphrase_door(self, ctx: SimpleNamespace) -> None:
        resp = ctx.response
        assert resp.headers.get("content-type", "").startswith("text/html"), (
            "a locked browser visit must be met by the passphrase door page, "
            f"not {resp.headers.get('content-type')!r}: {resp.text[:120]!r}"
        )
        assert 'action="/login"' in resp.text and 'name="passphrase"' in resp.text, (
            "the door page must hold a passphrase form that submits to the login door"
        )

    def assert_landed_on_entry_screen(self, ctx: SimpleNamespace) -> None:
        assert ctx.response.request.url.path == "/", (
            "after the right passphrase the browser must land on the entry screen, "
            f"but stayed at {ctx.response.request.url.path!r}"
        )
        self.comp.screen.assert_ready_for_typing(ctx)

    def assert_door_rejection(self, ctx: SimpleNamespace) -> None:
        self.assert_passphrase_door(ctx)
        assert "wrong passphrase" in ctx.response.text.lower(), (
            "the door must show a visible, polite rejection after a wrong passphrase"
        )

    def unlock(self) -> Any:
        resp = self.comp.actor().post("/login", data={"passphrase": TEST_PASSPHRASE})
        assert resp.status_code in (200, 303), f"unlock failed: {resp.status_code}"
        return resp

    def try_passphrase(self, passphrase: str, times: int = 1) -> Any:
        resp = None
        for _ in range(times):
            resp = self.comp.actor().post("/login", data={"passphrase": passphrase})
        return resp

    def open_record(self) -> Any:
        return self.comp.actor().get("/entries", params={"scale": TimeScale.ALL.value})

    def assert_record_open(self) -> None:
        resp = self.open_record()
        assert resp.status_code == 200, f"record not open: {resp.status_code}"
        assert "entries" in resp.json()

    def assert_record_hidden(self) -> None:
        resp = self.open_record()
        assert resp.status_code == 401, (
            f"record must stay hidden without a valid unlock, got {resp.status_code}"
        )

    def assert_save_turned_away(self, ctx: SimpleNamespace) -> None:
        assert ctx.response.status_code == 401, (
            f"a locked tracker must turn the save away, got {ctx.response.status_code}"
        )

    def assert_throttled(self, ctx: SimpleNamespace) -> None:
        assert ctx.response.status_code == 429, (
            f"expected throttling after repeated wrong guesses, got {ctx.response.status_code}"
        )
        retry = self.comp.actor().post("/login", data={"passphrase": TEST_PASSPHRASE})
        assert retry.status_code == 429, "even the right passphrase must wait while throttled"

    def assert_prompted_again(self, ctx: SimpleNamespace) -> None:
        assert ctx.response.status_code == 401, (
            f"an expired unlock must ask for the passphrase again, got {ctx.response.status_code}"
        )


class LoggingService(_Service):
    def record(self, day_spec: str, raw_weight: str, entry_ms: int | None = None) -> Any:
        payload: dict[str, Any] = {
            "date": self.comp.resolve_day(day_spec).isoformat(),
            "weight": raw_weight,
        }
        if entry_ms is not None:
            payload["entry_ms"] = entry_ms
        return self.comp.actor().post("/entries", json=payload)

    def record_raw_date(self, raw_date: str, raw_weight: str) -> Any:
        return self.comp.actor().post("/entries", json={"date": raw_date, "weight": raw_weight})

    def record_next_morning(self, ctx: SimpleNamespace, raw_weight: str) -> Any:
        """Advance to the next morning, capture the universe, then log."""
        self.comp.clock.days_pass(1)
        ctx.before, ctx.raw_input = self.comp.capture_universe(), raw_weight
        return self.record("today", raw_weight)

    # -- saves as the PHONE makes them (entry-date-picker, ADR-011) ---------------

    def _save(
        self,
        day: date,
        raw_weight: str,
        *,
        entry_ms: int | None = None,
        claim: DayClaim = DayClaim.DEVICE_DAY,
    ) -> Any:
        """One save carrying the picked date AND, optionally, the phone's own day.

        The `today` claim is what makes the backdated rule falsifiable at the HTTP
        boundary (ADR-011): the suite composes the two days independently, so a
        classifier that trusted client omission instead would be caught here."""
        payload: dict[str, Any] = {"date": day.isoformat(), "weight": raw_weight}
        if entry_ms is not None:
            payload["entry_ms"] = entry_ms
        if claim is DayClaim.DEVICE_DAY:
            payload["today"] = self.comp.resolve_day("today").isoformat()
        elif claim is DayClaim.GARBLED:
            payload["today"] = GARBLED_DAY_CLAIM
        return self.comp.actor().post("/entries", json=payload)

    def backfill(self, day: date, raw_weight: str, entry_ms: int | None = None) -> Any:
        """A repair from the date row: a past day picked while the phone lives today."""
        return self._save(day, raw_weight, entry_ms=entry_ms)

    def correct(self, day: date, kg: float) -> Any:
        return self._save(day, f"{kg:.1f}")

    def log_today(self, raw_weight: str, entry_ms: int | None = None) -> Any:
        """The default morning: the picked day IS the phone's day (zero date-row taps)."""
        return self._save(self.comp.resolve_day("today"), raw_weight, entry_ms=entry_ms)

    def save_with_claim(self, day: date, raw_weight: str, claim: DayClaim) -> Any:
        return self._save(day, raw_weight, claim=claim)

    # -- seeding (always through the driving port, never the store) ---------------

    def seed(
        self,
        day: date,
        kg: float,
        entry_ms: int | None = None,
        *,
        as_its_own_morning: bool = False,
    ) -> None:
        payload: dict[str, Any] = {"date": day.isoformat(), "weight": f"{kg:.1f}"}
        if entry_ms is not None:
            payload["entry_ms"] = entry_ms
        if as_its_own_morning:
            payload["today"] = day.isoformat()
        resp = self.comp.observer().post("/entries", json=payload)
        assert resp.status_code == 200 and resp.json()["outcome"] == "saved", (
            f"seeding {day} = {kg} failed: {resp.status_code} {resp.text[:200]}"
        )

    def seed_steady(self, kg: float, start: date, end: date) -> None:
        for offset in range((end - start).days + 1):
            self.seed(start + timedelta(days=offset), kg)

    def seed_daily(self, start: date, end: date) -> None:
        for offset in range((end - start).days + 1):
            day = start + timedelta(days=offset)
            self.seed(day, round(82.0 + (((day.toordinal() * 7) % 21) - 10) / 10, 1))

    def seed_weekly_decline(self, from_kg: float, per_week: float, start: date, end: date) -> None:
        for offset in range((end - start).days + 1):
            day = start + timedelta(days=offset)
            self.seed(day, round(from_kg - per_week * ((day - start).days // 7 + 1), 1))

    def seed_weekly_change(self, from_kg: float, per_week: float, start: date, end: date) -> None:
        """Signed weekly drift (US-007 direction seeds): negative per_week falls, positive rises."""
        for offset in range((end - start).days + 1):
            day = start + timedelta(days=offset)
            self.seed(day, round(from_kg + per_week * ((day - start).days // 7 + 1), 1))

    def seed_timed_week(self, end: date) -> list[int]:
        """A week of real MORNINGS -- each one logged on the day it happened.

        RENEGOTIATED at DISTILL of entry-date-picker (ADR-011, never silent):
        a morning is a SAME-DAY save. Seeding the whole week in one instant was
        indistinguishable from seven repairs once saves are classified at write
        time, and would strip six of the seven timings out of the KPI-1 report --
        loudly (milestone-5 asserts sample_count == 7), never silently. The clock
        therefore walks the week and each save claims its own day, which is what
        actually happened on the phone."""
        timings = [4200, 3900, 5100, 4400, 4800, 6900, 4100]
        for offset, ms in enumerate(timings):
            morning = end - timedelta(days=6 - offset)
            self.comp.clock.set_today(morning)
            self.seed(morning, 82.4, entry_ms=ms, as_its_own_morning=True)
        self.comp.clock.set_today(end)
        return timings

    def assert_absent(self, day: date) -> None:
        entries = self.comp.capture_universe()["record.entries"]
        assert day.isoformat() not in {d for d, _ in entries}, f"{day} unexpectedly has an entry"

    # -- outcome assertions (state-delta, Mandate 8) ------------------------------

    def assert_confirmation(self, ctx: SimpleNamespace, text: str) -> None:
        body = ctx.response.json()
        assert body["outcome"] == "saved", f"expected a save, got {body}"
        assert body["confirmation"] == text, f"expected {text!r}, got {body['confirmation']!r}"

    def assert_day_holds(self, ctx: SimpleNamespace, day_spec: str, kg: float) -> None:
        day = self.comp.resolve_day(day_spec).isoformat()
        after = self.comp.capture_universe()
        record = {d: w for d, w in after["record.entries"]}
        assert record.get(day) == kg, (
            f"expected {day} to hold {kg} kg, record shows {record.get(day)}"
        )
        assert list(record).count(day) == 1
        if getattr(ctx, "before", None) is None:
            return  # observation without a captured mutation (e.g. after a restart)
        expected_entries = tuple(
            sorted(({d: w for d, w in ctx.before["record.entries"]} | {day: kg}).items())
        )
        after = {**after, "record.entries": tuple(sorted(after["record.entries"]))}
        assert_state_delta(
            before={**ctx.before, "record.entries": tuple(sorted(ctx.before["record.entries"]))},
            after=after,
            universe=UNIVERSE,
            expected={
                "record.entries": set_to(expected_entries),
                "telemetry.entry_logged_count": set_to(
                    ctx.before["telemetry.entry_logged_count"] + 1
                ),
                "telemetry.trend_view_opened_count": unchanged(),
            },
        )

    def assert_top_of_history(self, day_spec: str, kg: float) -> None:
        day = self.comp.resolve_day(day_spec).isoformat()
        top = (
            self.comp.observer()
            .get("/entries", params={"scale": TimeScale.ALL.value})
            .json()["entries"][0]
        )
        assert (top["date"], top["weight_kg"]) == (day, kg), (
            f"expected {day} = {kg} at the top of history, got {top}"
        )

    def assert_rejected(self, ctx: SimpleNamespace, reason: RejectionReason) -> None:
        body = ctx.response.json()
        assert body["outcome"] == "rejected", f"expected a rejection, got {body}"
        assert body["reason"] == reason.value, (
            f"expected reason {reason.value!r}, got {body['reason']!r}"
        )
        assert body["reason"] in {r.value for r in RejectionReason}, "reason outside the closed set"

    def assert_nothing_stored(self, ctx: SimpleNamespace) -> None:
        assert_state_delta(
            before=ctx.before,
            after=self.comp.capture_universe(),
            universe=UNIVERSE,
            expected={},  # fail-closed: EVERYTHING must be unchanged
        )

    def assert_record_preserved(self, ctx: SimpleNamespace) -> None:
        """Entries identical; the telemetry trail may have recorded the (re-)save."""
        assert_state_delta(
            before=ctx.before,
            after=self.comp.capture_universe(),
            universe=UNIVERSE,
            expected={
                "record.entries": unchanged(),
                "telemetry.entry_logged_count": set_to(
                    ctx.before["telemetry.entry_logged_count"] + 1
                ),
                "telemetry.trend_view_opened_count": unchanged(),
            },
        )

    def assert_input_kept(self, ctx: SimpleNamespace) -> None:
        assert ctx.response.json().get("echo") == ctx.raw_input, (
            "the typed value must be echoed back for correction"
        )


class HistoryService(_Service):
    def open(self, scale: TimeScale) -> Any:
        return self.comp.actor().get("/entries", params={"scale": scale.value})

    def open_timed(self, scale: TimeScale, ctx: SimpleNamespace) -> Any:
        started = time.monotonic()
        resp = self.comp.actor().get("/entries", params={"scale": scale.value})
        ctx.elapsed_ms = (time.monotonic() - started) * 1000
        return resp

    def _dates(self, ctx: SimpleNamespace) -> list[str]:
        return [e["date"] for e in ctx.response.json()["entries"]]

    def assert_only_between(self, ctx: SimpleNamespace, start: date, end: date) -> None:
        dates = self._dates(ctx)
        assert dates, "expected entries to be shown"
        outside = [d for d in dates if not (start.isoformat() <= d <= end.isoformat())]
        assert not outside, f"entries outside the window {start}..{end}: {outside}"
        assert start.isoformat() in dates, f"window edge {start} missing (seeded daily)"

    def assert_spans(self, ctx: SimpleNamespace, start: date, end: date) -> None:
        dates = self._dates(ctx)
        assert min(dates) == start.isoformat() and max(dates) == end.isoformat(), (
            f"expected history spanning {start}..{end}, got {min(dates)}..{max(dates)}"
        )

    def assert_gap(self, ctx: SimpleNamespace, start: date, end: date) -> None:
        dates = set(self._dates(ctx))
        offending = [
            (start + timedelta(days=o)).isoformat()
            for o in range((end - start).days + 1)
            if (start + timedelta(days=o)).isoformat() in dates
        ]
        assert not offending, f"gap days must show no entries, found: {offending}"

    def assert_invite(self, ctx: SimpleNamespace) -> None:
        body = ctx.response.json()
        assert body["entries"] == [] and body["invite_first_log"] is True, (
            "an empty record must invite the first log"
        )

    def assert_exactly_one(self, ctx: SimpleNamespace) -> None:
        assert len(ctx.response.json()["entries"]) == 1, "expected exactly one entry shown"

    def assert_ready_within(self, ctx: SimpleNamespace, budget_ms: int) -> None:
        assert ctx.response.status_code == 200
        assert ctx.elapsed_ms <= budget_ms, (
            f"history took {ctx.elapsed_ms:.0f} ms, budget {budget_ms} ms"
        )


class TrendService(_Service):
    def _series(self, scale: TimeScale) -> list[tuple[str, float]]:
        resp = self.comp.actor().get("/trend", params={"scale": scale.value})
        assert resp.status_code == 200, f"trend not available: {resp.status_code}"
        return [(p["date"], p["trend_kg"]) for p in resp.json()["points"]]

    def open(self, scale: TimeScale, ctx: SimpleNamespace) -> None:
        # Pinned inherited-AT amendment (graph-first-home, ADR-009 -- feature-delta
        # Renegotiations #2): "opening the trend" is a History-page visit. The page
        # open is the deliberate KPI-3 signal (milestone-4 engagement scenarios);
        # the series fetch beneath it is a pure read. Scenario wording unchanged.
        page = self.comp.actor().get("/graph", params={"scale": scale.value})
        assert page.status_code == 200, f"the trend page did not open: {page.status_code}"
        ctx.trend_scale = scale
        ctx.trend = self._series(scale)

    def note(self, scale: TimeScale, ctx: SimpleNamespace) -> None:
        ctx.noted_scale = scale
        ctx.noted_trend = dict(self._series(scale))

    def assert_max_shift(self, ctx: SimpleNamespace, limit_kg: float) -> None:
        current = dict(self._series(ctx.noted_scale))
        common = set(current) & set(ctx.noted_trend)
        assert common, "no overlapping trend days to compare"
        worst = max(abs(current[d] - ctx.noted_trend[d]) for d in common)
        assert worst <= limit_kg + 1e-9, (
            f"trend moved {worst:.3f} kg somewhere; the limit is {limit_kg} kg"
        )

    def assert_max_daily_step(self, ctx: SimpleNamespace, limit_kg: float) -> None:
        series = sorted(ctx.trend)
        steps = [(abs(b[1] - a[1]), a[0], b[0]) for a, b in zip(series, series[1:], strict=False)]
        worst = max(steps)
        assert worst[0] <= limit_kg + 1e-9, (
            f"trend steps {worst[0]:.3f} kg between {worst[1]} and {worst[2]}; limit {limit_kg} kg"
        )

    def assert_covers_every_day(self, ctx: SimpleNamespace, start: date, end: date) -> None:
        days = {d for d, _ in ctx.trend}
        missing = [
            (start + timedelta(days=o)).isoformat()
            for o in range((end - start).days + 1)
            if (start + timedelta(days=o)).isoformat() not in days
        ]
        assert not missing, f"trend must cover every day on the grid; missing {missing}"

    def assert_decline_within(self, ctx: SimpleNamespace, onset: date, days: int) -> None:
        series = dict(ctx.trend)
        at_onset = series[onset.isoformat()]
        within = series[(onset + timedelta(days=days)).isoformat()]
        assert within < at_onset - 0.05, (
            f"decline not visible within {days} days: trend {at_onset:.2f} -> {within:.2f}"
        )

    def assert_no_dip_at(self, ctx: SimpleNamespace, day: date) -> None:
        series = dict(self._series(ctx.noted_scale))
        mid = series[day.isoformat()]
        around = (
            series[(day - timedelta(days=1)).isoformat()]
            + series[(day + timedelta(days=1)).isoformat()]
        ) / 2
        assert abs(mid - around) <= 0.05, (
            f"trend still dips at {day}: {mid:.2f} vs neighbours {around:.2f}"
        )

    def assert_identical_reloads(self, ctx: SimpleNamespace) -> None:
        assert self._series(ctx.trend_scale) == ctx.trend == self._series(ctx.trend_scale), (
            "the same entry set must render an identical trend line on every load"
        )

    def assert_begins_at(self, ctx: SimpleNamespace, day: date) -> None:
        assert ctx.trend, "trend must be available from the very first entry"
        assert min(d for d, _ in ctx.trend) == day.isoformat(), (
            f"trend must begin at {day}, begins at {min(d for d, _ in ctx.trend)}"
        )


class GraphService(_Service):
    def open(self, view: ViewMode | None = None, scale: TimeScale | None = None) -> Any:
        params: dict[str, str] = {}
        if view is not None:
            params["view"] = view.value
        if scale is not None:
            params["scale"] = scale.value
        return self.comp.actor().get("/graph", params=params)

    def switch(self, ctx: SimpleNamespace, view: ViewMode) -> Any:
        return self.open(view=view, scale=ctx.graph_scale)

    def assert_view_at(self, ctx: SimpleNamespace, view: ViewMode, scale: TimeScale) -> None:
        html = ctx.response.text
        assert f'data-view="{view.value}"' in html, f"expected the {view.value} view"
        assert f'data-scale="{scale.value}"' in html, f"expected the {scale.value} window preserved"

    def assert_default_is_trend(self, ctx: SimpleNamespace) -> None:
        assert 'data-view="trend"' in ctx.response.text, "the trend must be the default lens"


#: Render source (entry-date-picker, ADR-010/D-21): the WHOLE record as
#: {iso_day: kg} inside the entry screen's one inline script. CONSCIOUS
#: RENEGOTIATION of the map-const name (R-1a, never silent): ONE map answers
#: both the yesterday anchor and the edit prefill, so the two can never
#: disagree. The transitional `recentWeights` alias retired with the rename it
#: carried; a page carrying no map at all still fails on the missing VALUE via
#: the paragraph fallback below.
RECORD_WEIGHTS_MAP = re.compile(r"const recordWeights = (\{[^;]*\});")
#: Pre-fix render source: the server-rendered anchor paragraph. Kept as fallback
#: so the skew regression fails on the wrong VALUE shown, not on a missing marker.
SERVER_RENDERED_YESTERDAY = re.compile(r"yesterday: (\d+\.\d) kg")


def embedded_weights(html: str) -> dict[str, float] | None:
    """The day-to-weight map the entry screen hands the phone, or None if the
    page carries no map at all (pre-fix render)."""
    found = RECORD_WEIGHTS_MAP.search(html)
    return dict(json.loads(found.group(1))) if found is not None else None


class ScreenService(_Service):
    def open_entry(self) -> Any:
        return self.comp.actor().get("/")

    def open_entry_timed(self, ctx: SimpleNamespace) -> Any:
        started = time.monotonic()
        resp = self.comp.actor().get("/")
        ctx.elapsed_ms = (time.monotonic() - started) * 1000
        return resp

    def assert_ready_within(self, ctx: SimpleNamespace, budget_ms: int) -> None:
        assert ctx.response.status_code == 200
        assert ctx.elapsed_ms <= budget_ms, (
            f"the entry screen took {ctx.elapsed_ms:.0f} ms, budget {budget_ms} ms"
        )

    def assert_ready_for_typing(self, ctx: SimpleNamespace) -> None:
        html = ctx.response.text
        assert "autofocus" in html, "the weight field must be focused on open"
        assert 'inputmode="decimal"' in html, "a decimal keypad must come up"

    def shown_yesterday_kg(self, ctx: SimpleNamespace) -> float | None:
        """The yesterday anchor as the phone SHOWS it. Post-fix pages embed a
        recent-days map and render client-side: emulate that exact lookup with
        the DEVICE-local yesterday (device_day preferred over the server clock
        via resolve_day -- at the skew moment the two diverge). Pre-fix pages
        carried a server-rendered paragraph: read it, so the regression fails
        on the wrong value shown, never on a missing marker."""
        embedded = embedded_weights(ctx.response.text)
        if embedded is not None:
            return embedded.get(self.comp.resolve_day("yesterday").isoformat())
        line = SERVER_RENDERED_YESTERDAY.search(ctx.response.text)
        return float(line.group(1)) if line is not None else None

    def assert_yesterday(self, ctx: SimpleNamespace, kg: float) -> None:
        shown = self.shown_yesterday_kg(ctx)
        assert shown == kg, (
            f"expected yesterday's anchor to read {kg:.1f} kg beside the input, "
            f"the screen shows {shown}"
        )

    def assert_no_yesterday(self, ctx: SimpleNamespace) -> None:
        assert self.shown_yesterday_kg(ctx) is None, (
            "no yesterday reference must be shown on the first morning"
        )

    def open_manifest(self) -> Any:
        return self.comp.actor().get("/manifest.webmanifest")

    def assert_installable(self, ctx: SimpleNamespace) -> None:
        assert ctx.response.status_code == 200, "the install manifest must be served"
        assert "name" in ctx.response.json(), "the manifest must name the tracker"


class StatsService(_Service):
    def open_speed(self) -> Any:
        return self.comp.actor().get("/stats")

    def assert_speed_report(self, ctx: SimpleNamespace, timings: list[int]) -> None:
        import statistics

        speed = ctx.response.json()["speed"]
        assert speed["sample_count"] == len(timings)
        assert speed["median_ms"] == statistics.median(timings)
        assert max(timings) >= speed["p90_ms"] >= speed["median_ms"], (
            f"p90 must sit between median and worst case, got {speed}"
        )

    def assert_speed_report_empty(self, ctx: SimpleNamespace) -> None:
        speed = ctx.response.json()["speed"]
        assert speed == {"median_ms": None, "p90_ms": None, "sample_count": 0}, (
            f"an untimed record must make no speed claims (honest nulls), got {speed}"
        )

    def assert_trend_views_this_week(self, n: int) -> None:
        # Pinned inherited-AT amendment (graph-first-home, ADR-009): KPI-3's home
        # moved -- the weekly deliberate count now reads trend_study_this_week
        # (STUDY_COUNT_KEY); trend_views_this_week stays served but frozen-historical.
        body = self.comp.observer().get("/stats").json()
        assert body[STUDY_COUNT_KEY] == n, (
            f"expected {n} deliberate trend stud(y/ies) counted this week, "
            f"got {body[STUDY_COUNT_KEY]}"
        )


class HealthService(_Service):
    def check_unauthenticated(self) -> Any:
        from fastapi.testclient import TestClient

        return TestClient(self.comp._build(), raise_server_exceptions=True).get("/healthz")

    def assert_healthy(self, ctx: SimpleNamespace) -> None:
        assert ctx.response.status_code == 200, "health must be visible without the passphrase"
        assert ctx.response.json()["status"] == "ok"


class SystemService(_Service):
    def ensure_fresh(self) -> None:
        assert not self.comp.db_path.exists(), "expected an empty record to start from"

    def restart(self) -> None:
        """Recreate the app over the SAME record file (durability contract)."""
        cookies = dict(self.comp._actor.cookies) if self.comp._actor is not None else {}
        self.comp._app = None
        self.comp._actor = None
        self.comp._observer = None
        for name, value in cookies.items():
            self.comp.actor().cookies.set(name, value)

    def make_home_unwritable(self) -> None:
        os.chmod(self.comp.db_path.parent, stat.S_IRUSR | stat.S_IXUSR)

    def try_start(self, ctx: SimpleNamespace) -> None:
        try:
            self.comp._build()
            ctx.refusal = None
        except StartupRefused as refusal:
            ctx.refusal = refusal

    def assert_refused(self, ctx: SimpleNamespace) -> None:
        assert ctx.refusal is not None, (
            "the tracker must refuse to open when the record cannot be stored safely"
        )


#: The one neutral glance element (identical markup for ↓ / ↑ / → -- information,
#: never judgment): `<p id="trend-glance">Trend: 82.3 kg · ↓0.25 kg/week</p>`.
GLANCE_LINE = re.compile(r'<p id="trend-glance">([^<]*)</p>')
NEUTRAL_GLANCE_OPENING = '<p id="trend-glance">'


class GlanceService(_Service):
    """Glance summary on the entry screen (US-007, ADR-006, D-13/D-14).

    DELIVER-facing HTTP contract (executable spec):
        GET  /        -> when a glance exists, the HTML holds exactly the neutral element
                         above (no direction-dependent class/style; rate part absent below
                         the 7-day ENTRY span; element absent with no data or on failure);
                         each render delivering data appends one `trend.glance.shown` event.
        POST /entries -> SAVED responses gain `"glance": "<display text>" | null`
                         (null = degraded -- the save never blocks on the trend); a
                         delivery with data appends one `trend.glance.shown`. REJECTED
                         responses carry NO glance field and append nothing.
        GET  /stats   -> gains `"trend_glance_shown_count"` (glance deliveries over the
                         same rolling 7-day window as trend_views_this_week, KPI-3/5
                         separation).
        GET  /trend   -> a PURE READ since ADR-009 (graph-first-home): the
                         trend.view.opened emission is retired; deliberate study
                         is counted on /graph opens (KPI-3 separation stays
                         structural -- the glance never touches either).

    Oracle: the shipped pure `trend_series` (OUT-5-verified) plus the ADR-006 PINNED
    display expressions encoded verbatim below (they ARE the spec, not a re-derivation):
    value = series END at 0.1 kg; rate = `series[-1] - series[-8]` iff entry span >= 7
    days; quantize `round(rate / 0.05) * 0.05` (built-in round as pinned); glyph from
    the ROUNDED sign, magnitude displayed as abs with two decimals. The glance must
    equal the graph line's own end and trailing-week change for the same entries
    (single-source AC); after a save BOTH revise together (RTS co-revision) -- these
    oracles judge the CURRENT pair's coherence, never prior renderings.
    """

    # -- oracle -------------------------------------------------------------------

    def _entries(self) -> list[Entry]:
        shown = self.comp.observer().get("/entries", params={"scale": TimeScale.ALL.value})
        return [
            Entry(day=date.fromisoformat(e["date"]), weight_kg=e["weight_kg"])
            for e in shown.json()["entries"]
        ]

    @staticmethod
    def _pinned_rate_text(rate_kg_per_week: float) -> str:
        quantized = round(rate_kg_per_week / 0.05) * 0.05  # ADR-006 pinned expression
        glyph = "↓" if quantized < 0 else ("↑" if quantized > 0 else "→")
        return f"{glyph}{abs(quantized):.2f} kg/week"

    def expected_text(self) -> str | None:
        entries = self._entries()
        series = trend_series(entries)
        if not series:
            return None
        value_text = f"Trend: {series[-1].trend_kg:.1f} kg"
        span_days = (max(e.day for e in entries) - min(e.day for e in entries)).days
        if span_days < 7:
            return value_text
        rate = series[-1].trend_kg - series[-8].trend_kg
        return f"{value_text} · {self._pinned_rate_text(rate)}"

    def _shown_line(self, ctx: SimpleNamespace) -> str:
        """The CURRENT glance line: the rendered element on an entry-screen response,
        or -- after a save -- the line the saved response carried for the in-place
        refresh (already oracle-checked and remembered as ctx.glance_text)."""
        found = GLANCE_LINE.search(ctx.response.text)
        if found is not None:
            return found.group(1).strip()
        delivered = getattr(ctx, "glance_text", None)
        assert delivered is not None, "expected the glance line on the entry screen, none shown"
        return delivered

    # -- universe (Mandate 8; glance-aware superset of the shared capture) ---------

    def capture(self) -> dict[str, Any]:
        stats = self.comp.observer().get("/stats").json()
        assert GLANCE_COUNT_KEY in stats, (
            f"the stats page must report glance deliveries ({GLANCE_COUNT_KEY!r}), "
            f"got {sorted(stats)}"
        )
        return {
            **self.comp.capture_universe(),
            "telemetry.trend_glance_shown_count": stats[GLANCE_COUNT_KEY],
        }

    # -- journey moves (Given-flavored: observe, then remember the state) ----------

    def seed_recent(self, direction: TrendDirection) -> None:
        """Two weeks of entries ending yesterday: falling, rising, or dead steady."""
        end = self.comp.resolve_day("yesterday")
        start = end - timedelta(days=14)
        if direction is TrendDirection.STEADY:
            self.comp.logging.seed_steady(82.0, start, end)
        else:
            per_week = -0.5 if direction is TrendDirection.FALLING else 0.5
            self.comp.logging.seed_weekly_change(82.5, per_week, start, end)

    def shows_now(self, ctx: SimpleNamespace) -> None:
        ctx.response = self.comp.screen.open_entry()
        self.assert_line_matches(ctx)
        ctx.glance_before = self.capture()

    def saw_no_line(self, ctx: SimpleNamespace) -> None:
        ctx.response = self.comp.screen.open_entry()
        self.comp.screen.assert_ready_for_typing(ctx)
        assert GLANCE_LINE.search(ctx.response.text) is None, (
            "an empty record must show no trend line"
        )
        ctx.glance_before = self.capture()

    def break_computation(self, monkeypatch: Any) -> None:
        """Inject a failing glance callable, then restart so the wiring picks it up.

        All plausible bindings are patched (module of definition + composition/route
        rebinding sites) so the injection holds regardless of the crafter's import style.
        """

        def failing_glance(*_args: Any, **_kwargs: Any) -> Any:
            raise RuntimeError("glance computation failed (injected fault)")

        for target in (
            "weight_tracker.core.glance.glance",
            "weight_tracker.composition.glance",
            "weight_tracker.web.routes.glance",
        ):
            monkeypatch.setattr(target, failing_glance, raising=False)
        self.comp.system.restart()

    def deliver_mornings(self, mornings: int) -> None:
        for _ in range(mornings):
            self.comp.clock.days_pass(1)
            self.comp.actor().get("/")

    def study_trend(self, times: int) -> None:
        # Pinned inherited-AT amendment (graph-first-home, ADR-009 -- pinned on the
        # milestone-6 scenario itself): deliberate study redirects from the retired
        # GET /trend emission to History-page opens. Wording unchanged, never silent.
        for _ in range(times):
            self.comp.actor().get("/graph", params={"scale": TimeScale.ONE_MONTH.value})

    # -- outcome assertions --------------------------------------------------------

    def assert_line_matches(self, ctx: SimpleNamespace) -> None:
        expected = self.expected_text()
        assert expected is not None, "oracle bug: glance asserted on a record with no trend"
        ctx.glance_text = self._shown_line(ctx)
        assert ctx.glance_text == expected, (
            f"glance line reads {ctx.glance_text!r}, the entry record demands {expected!r}"
        )

    def assert_no_line(self, ctx: SimpleNamespace) -> None:
        assert GLANCE_LINE.search(ctx.response.text) is None, (
            "the trend line must be absent, not shown broken"
        )

    def assert_value_shown(self, ctx: SimpleNamespace) -> None:
        assert self._shown_line(ctx).startswith("Trend: "), "expected a glanced trend value"

    def assert_value_fragment(self, ctx: SimpleNamespace, text: str) -> None:
        line = self._shown_line(ctx)
        assert f"Trend: {text}" in line, f"expected the trend to read {text!r}, line: {line!r}"

    def assert_rate_fragment(self, ctx: SimpleNamespace, text: str) -> None:
        line = self._shown_line(ctx)
        assert text in line, f"expected the weekly rate {text!r}, line: {line!r}"

    def assert_glyph(self, ctx: SimpleNamespace, glyph: str) -> None:
        line = self._shown_line(ctx)
        assert glyph in line, f"expected the direction glyph {glyph!r}, line: {line!r}"

    def assert_neutral_styling(self, ctx: SimpleNamespace) -> None:
        assert NEUTRAL_GLANCE_OPENING in ctx.response.text, (
            "every direction must wear the one neutral glance element -- no "
            "direction-dependent class, style, or color"
        )

    def assert_rate_disposition(self, ctx: SimpleNamespace, disposition: RateDisposition) -> None:
        line = self._shown_line(ctx)
        if disposition is RateDisposition.SHOWN:
            assert "kg/week" in line, f"a >=7-day span has earned its rate, line: {line!r}"
        else:
            assert "kg/week" not in line, (
                f"a rate on a young record is noise dressed as insight, line: {line!r}"
            )

    def assert_value_and_rate_shown(self, ctx: SimpleNamespace) -> None:
        self.assert_value_shown(ctx)
        self.assert_rate_disposition(ctx, RateDisposition.SHOWN)

    def _series_over_the_wire(self) -> list[tuple[str, float]]:
        resp = self.comp.observer().get("/trend", params={"scale": TimeScale.ALL.value})
        assert resp.status_code == 200, f"trend not available: {resp.status_code}"
        return [(p["date"], p["trend_kg"]) for p in resp.json()["points"]]

    def assert_matches_graph_line_end(self, ctx: SimpleNamespace) -> None:
        """Single-source AC (journey step 1<->3): glanced value == the graph line's END."""
        line_end_kg = self._series_over_the_wire()[-1][1]
        self.assert_value_fragment(ctx, f"{line_end_kg:.1f} kg")

    def assert_rate_is_trailing_week_change(self, ctx: SimpleNamespace) -> None:
        """RTS co-revision oracle: the CURRENT pair coheres -- displayed rate == the
        displayed line's own trailing-7-day net change (never prior renderings)."""
        series = self._series_over_the_wire()
        self.assert_rate_fragment(ctx, self._pinned_rate_text(series[-1][1] - series[-8][1]))

    def _glance_from_save(self, ctx: SimpleNamespace) -> Any:
        body = ctx.response.json()
        assert "glance" in body, (
            f"a saved response must carry the glance for the in-place refresh, got {sorted(body)}"
        )
        return body["glance"]

    def _assert_saved_delivery_delta(self, ctx: SimpleNamespace) -> None:
        body = ctx.response.json()
        expected_entries = tuple(
            sorted(
                (
                    {d: w for d, w in ctx.glance_before["record.entries"]}
                    | {body["date"]: body["weight_kg"]}
                ).items()
            )
        )
        after = self.capture()
        assert_state_delta(
            before={
                **ctx.glance_before,
                "record.entries": tuple(sorted(ctx.glance_before["record.entries"])),
            },
            after={**after, "record.entries": tuple(sorted(after["record.entries"]))},
            universe=GLANCE_UNIVERSE,
            expected={
                "record.entries": set_to(expected_entries),
                "telemetry.entry_logged_count": set_to(
                    ctx.glance_before["telemetry.entry_logged_count"] + 1
                ),
                "telemetry.trend_glance_shown_count": set_to(
                    ctx.glance_before["telemetry.trend_glance_shown_count"] + 1
                ),
                "telemetry.trend_view_opened_count": unchanged(),
            },
        )

    def assert_refreshed_by_save(self, ctx: SimpleNamespace) -> None:
        shown = self._glance_from_save(ctx)
        expected = self.expected_text()
        assert shown == expected and expected is not None, (
            f"the refreshed glance reads {shown!r}, today's record demands {expected!r}"
        )
        ctx.glance_text = shown
        self._assert_saved_delivery_delta(ctx)

    def assert_first_glance(self, ctx: SimpleNamespace, kg: float) -> None:
        shown = self._glance_from_save(ctx)
        assert shown == f"Trend: {kg:.1f} kg", (
            f"the very first entry must glance as its own trend with no rate, got {shown!r}"
        )

    def assert_delivery_recorded(self, ctx: SimpleNamespace) -> None:
        self._assert_saved_delivery_delta(ctx)

    def assert_no_glance_on_save(self, ctx: SimpleNamespace) -> None:
        assert self._glance_from_save(ctx) is None, (
            "a failing trend must degrade the save's glance to null, never block the save"
        )

    def assert_no_glance_for_rejection(self, ctx: SimpleNamespace) -> None:
        assert "glance" not in ctx.response.json(), "a rejected save carries no glance"
        assert_state_delta(
            before=ctx.glance_before,
            after=self.capture(),
            universe=GLANCE_UNIVERSE,
            expected={},  # fail-closed: nothing changed, not even the glance trail
        )

    def assert_delivered_times(self, times: int) -> None:
        delivered = self.capture()["telemetry.trend_glance_shown_count"]
        assert delivered == times, f"expected {times} glance deliveries, counted {delivered}"


# ---------------------------------------------------------------- calm visual theme

#: The one new artifact of calm-visual-theme, served by the EXISTING static route.
THEME_ASSET_PATH = "/static/theme.css"
#: DISCUSS D9 / G-5 pin: total added CSS budget, uncompressed.
THEME_BUDGET_BYTES = 10 * 1024
#: Global comfortable-touch promise (DISCUSS: >= 44 px everywhere, door rule promoted).
TOUCH_TARGET_RULE = re.compile(r"min-height:\s*44px")
#: Pressed-beyond-color promise (US-009): the aria-pressed state is styled in its own right.
PRESSED_STATE_RULE = re.compile(r'\[aria-pressed="true"\]')
#: Reaching beyond the tracker's own walls (G-5: zero external requests).
OTHER_ORIGIN_MARKS = ("http://", "https://", 'src="//', 'href="//', "url(//", "@import")
#: Shell assets carrying no personal data (ADR-003 threat model protects the
#: RECORD): the door's clothes and the PWA shell stay reachable while locked.
OPEN_SHELL_ASSETS = (THEME_ASSET_PATH, "/manifest.webmanifest", "/sw.js")

#: G-5 script clause as consciously renegotiated by graph-first-home (2026-07-24):
#: the ONLY script sources the morning screen may carry -- same-origin, vendored.
SANCTIONED_ENTRY_SCRIPTS = frozenset({"/static/uplot.iife.min.js", "/static/graph.js"})


class ThemeService(_Service):
    """Theme delivery + G-4/G-5 verification (US-008/US-009, ADR-007, Q1/Q6).

    The theme is a pure static asset with an EMPTY mutation universe (DESIGN):
    every method here is a read-only probe, so no state-delta applies (Mandate 8
    is carried by the reused logging/glance steps in the same scenarios). The
    contrast checker below is the AUTHORITATIVE G-4 instrument: WCAG
    relative-luminance arithmetic (pure, in domain_types) over the hex tokens
    the served asset actually declares -- pinned to required RATIOS, never to
    hex values, so one-hex-step nudges (Q6) stay green."""

    def _authed_probe(self) -> Any:
        """Tolerant authed client: server faults become status codes, never raises,
        so a missing asset fails a 200-assertion (RED) instead of erroring (BROKEN)."""
        from fastapi.testclient import TestClient

        if getattr(self, "_probe", None) is None:
            self._probe = TestClient(self.comp._build(), raise_server_exceptions=False)
            resp = self._probe.post("/login", data={"passphrase": TEST_PASSPHRASE})
            assert resp.status_code in (200, 303), f"probe login failed: {resp.status_code}"
        return self._probe

    def _locked_browser(self) -> Any:
        """A fresh cookie-less browser navigation: what a locked visitor sees."""
        from fastapi.testclient import TestClient

        return TestClient(self.comp._build(), raise_server_exceptions=False)

    def _page_html(self, screen: Screen) -> str:
        if screen is Screen.DOOR:
            resp = self._locked_browser().get("/", headers=BROWSER_HTML)
        else:
            path = {Screen.ENTRY: "/", Screen.GRAPH: "/graph"}[screen]
            resp = self._authed_probe().get(path, headers=BROWSER_HTML)
        ctx_ok = resp.status_code in (200, 401)  # the door answers 401 with its page
        assert ctx_ok, f"the {screen.value} did not open: {resp.status_code}"
        return resp.text

    def _theme_css(self, ctx: SimpleNamespace) -> str:
        if getattr(ctx, "theme_css", None) is None:
            self.fetch_delivered(ctx)
        return ctx.theme_css

    # -- wearing / delivery -------------------------------------------------

    def assert_screen_wears_theme(self, ctx: SimpleNamespace, screen: Screen) -> None:
        html = self._page_html(screen)
        assert THEME_ASSET_PATH in html and "stylesheet" in html, (
            f"the {screen.value} must wear the calm theme "
            f"(a stylesheet link to {THEME_ASSET_PATH}), but its page carries none"
        )

    def fetch_delivered(self, ctx: SimpleNamespace) -> None:
        """Fetch the theme from the tracker itself; THE RED anchor while it is unbuilt."""
        resp = self._authed_probe().get(THEME_ASSET_PATH)
        assert resp.status_code == 200, (
            f"the calm theme must be delivered by the tracker itself at {THEME_ASSET_PATH}, "
            f"got {resp.status_code}"
        )
        ctx.theme_css, ctx.theme_bytes = resp.text, len(resp.content)

    def assert_shell_assets_open_while_locked(self, ctx: SimpleNamespace) -> None:
        """US-008 regression: a cookie-less browser still receives the shell
        assets (theme, manifest, service worker) -- they carry no personal data
        (ADR-003), so the door arrives dressed while the record stays locked."""
        locked = self._locked_browser()
        answers = {asset: locked.get(asset) for asset in OPEN_SHELL_ASSETS}
        refused = {a: r.status_code for a, r in answers.items() if r.status_code != 200}
        assert not refused, (
            "shell assets carry no personal data and must dress the door even "
            f"while the record is locked, but the gate refused: {refused}"
        )
        ctx.theme_css = answers[THEME_ASSET_PATH].text
        assert "{" in ctx.theme_css and "--" in ctx.theme_css, (
            "the locked visitor must receive the stylesheet itself, "
            f"not a substitute body: {ctx.theme_css[:120]!r}"
        )

    def assert_dressed_for_both_lights(self, ctx: SimpleNamespace) -> None:
        appearances = scheme_token_maps(self._theme_css(ctx))
        for scheme in ColorScheme:
            missing = {"--bg", "--text"} - appearances[scheme].keys()
            assert not missing, (
                f"the theme must define a {scheme.value} appearance "
                f"(page and ink colors), missing {sorted(missing)}"
            )

    def examine_appearances(self, ctx: SimpleNamespace) -> None:
        ctx.appearances = scheme_token_maps(self._theme_css(ctx))

    # -- G-4: the contrast contract ------------------------------------------

    def assert_contrast_class_holds(
        self, ctx: SimpleNamespace, contrast_class: ContrastClass
    ) -> None:
        required = MIN_CONTRAST_RATIO[contrast_class]
        complaints = [
            f"{pairing.label} in {scheme.value}: {self._pairing_verdict(ctx, scheme, pairing)}"
            for scheme in ColorScheme
            for pairing in CONTRAST_CONTRACT
            if pairing.contrast_class is contrast_class
            and self._pairing_verdict(ctx, scheme, pairing) is not None
        ]
        assert not complaints, (
            f"every {contrast_class.value} pairing must reach {required}:1 "
            f"in both lights (G-4), but:\n  " + "\n  ".join(complaints)
        )

    def _pairing_verdict(self, ctx: SimpleNamespace, scheme: ColorScheme, pairing) -> str | None:
        tokens = ctx.appearances[scheme]
        if pairing.ink not in tokens or pairing.surface not in tokens:
            return f"colors {pairing.ink}/{pairing.surface} are not declared"
        ratio = contrast_ratio(tokens[pairing.ink], tokens[pairing.surface])
        required = MIN_CONTRAST_RATIO[pairing.contrast_class]
        return None if ratio >= required else f"{ratio:.2f}:1 falls short of {required}:1"

    def assert_dim_light_answers_daylight(self, ctx: SimpleNamespace) -> None:
        contract_names = {p.ink for p in CONTRAST_CONTRACT} | {p.surface for p in CONTRAST_CONTRACT}
        declared = ctx.appearances[ColorScheme.DAYLIGHT].keys() & contract_names
        unanswered = declared - dark_override_names(self._theme_css(ctx))
        assert not unanswered, (
            "every color the daylight appearance names must be answered in dim light "
            f"(or 06:45 gets the flashbang back), unanswered: {sorted(unanswered)}"
        )

    # -- G-5: the cost of the look --------------------------------------------

    def tally_cost(self, ctx: SimpleNamespace) -> None:
        self.fetch_delivered(ctx)
        ctx.dressed_pages = {screen: self._page_html(screen) for screen in Screen}

    def assert_budget_kept(self, ctx: SimpleNamespace, kilobytes: int) -> None:
        assert ctx.theme_bytes <= kilobytes * 1024, (
            f"the whole look must weigh no more than {kilobytes} KB uncompressed (G-5), "
            f"but weighs {ctx.theme_bytes} bytes"
        )

    def assert_self_contained(self, ctx: SimpleNamespace) -> None:
        documents = {"the theme itself": ctx.theme_css} | {
            f"the {screen.value}": html for screen, html in ctx.dressed_pages.items()
        }
        reaching = {
            name: mark
            for name, doc in documents.items()
            for mark in OTHER_ORIGIN_MARKS
            if mark in doc
        }
        assert not reaching, (
            f"no screen may reach beyond the tracker's own walls (G-5), but: {reaching}"
        )

    def assert_entry_moving_parts_own(self, ctx: SimpleNamespace) -> None:
        """G-5 script clause, CONSCIOUSLY renegotiated 2026-07-24 (graph-first-home
        DISTILL, per the ADR-008 disclosure and the DISCUSS System-Constraints flag):
        the literal "0 new entry-screen scripts" count cannot survive a front-page
        graph; the surviving intent -- zero external origins, no third-party cost --
        is pinned as: exactly one inline script plus, at most, the two SAME-ORIGIN
        vendored chart scripts. Never a silent deletion."""
        entry_html = ctx.dressed_pages[Screen.ENTRY]
        sources = re.findall(r'<script[^>]*\bsrc="([^"]+)"', entry_html)
        foreign = [src for src in sources if src not in SANCTIONED_ENTRY_SCRIPTS]
        inline_count = entry_html.count("<script") - len(sources)
        assert inline_count == 1 and not foreign, (
            "every moving part on the morning screen must be the tracker's own "
            "(G-5 as renegotiated: one inline script + sanctioned same-origin chart "
            f"scripts only), found {inline_count} inline and foreign sources {foreign}"
        )

    # -- structural promises carried by the asset ------------------------------

    def assert_touch_comfort_promised(self, ctx: SimpleNamespace) -> None:
        assert TOUCH_TARGET_RULE.search(self._theme_css(ctx)), (
            "the theme must promise comfortable touch targets everywhere "
            "(the door's 44px rule, now global)"
        )

    def assert_pressed_beyond_color(self, ctx: SimpleNamespace) -> None:
        assert PRESSED_STATE_RULE.search(self._theme_css(ctx)), (
            "the pressed control must be promised a look of its own beyond color "
            "(a styled pressed state in the theme)"
        )

    def assert_chart_single_palette(self, ctx: SimpleNamespace) -> None:
        hardcoded = hex_colors_in(self._page_html(Screen.GRAPH))
        assert not hardcoded, (
            "the chart must draw every line from the tracker's single palette; "
            f"the graph page still carries its own colors: {hardcoded}"
        )

    # -- progressive enhancement (US-008 domain example 3) ---------------------

    def break_delivery(self, monkeypatch: Any) -> None:
        """The theme goes missing: the static shelf is emptied for this scenario."""
        from weight_tracker.web import routes

        bare_shelf = self.comp.db_path.parent / "bare-static-shelf"
        bare_shelf.mkdir(exist_ok=True)
        monkeypatch.setattr(routes, "_static_dir", bare_shelf)

    def assert_morning_still_ready(self, ctx: SimpleNamespace) -> None:
        probe = SimpleNamespace(response=self.comp.screen.open_entry())
        assert probe.response.status_code == 200, "the morning screen must still open"
        self.comp.screen.assert_ready_for_typing(probe)


# ---------------------------------------------------------------- device-day frame


class DayFrameService(_Service):
    """Client-authoritative day frame on READ surfaces (fix-device-day-reads).

    Regression oracle contract (NON-TAUTOLOGICAL): every expected day derives
    from the phone's declared day (composition.device_day), never from
    fake_clock.today() -- at the 02:00-UTC skew moment the two diverge, and
    borrowing the server clock would make the oracle agree with the bug.
    """

    def evening_skew(self, utc_day: date, device_day: date) -> None:
        """02:00 UTC on `utc_day` while the phone still lives `device_day`."""
        assert utc_day == device_day + timedelta(days=1), (
            "skew frame: the UTC day must sit exactly one day ahead of the phone"
        )
        self.comp.fake_clock.set_small_hours_utc(utc_day)
        self.comp.clock.set_device_day(device_day)

    def _device_day(self) -> date:
        day = self.comp.device_day
        assert day is not None, "day-frame scenarios must declare the phone's day"
        return day

    # -- journey moves (the phone always claims its own day, as graph.html does) ---

    def open_history(self, scale: TimeScale) -> Any:
        return self.comp.actor().get(
            "/entries", params={"scale": scale.value, "today": self._device_day().isoformat()}
        )

    def open_trend(self, scale: TimeScale, ctx: SimpleNamespace) -> None:
        resp = self.comp.actor().get(
            "/trend", params={"scale": scale.value, "today": self._device_day().isoformat()}
        )
        assert resp.status_code == 200, f"trend not available: {resp.status_code}"
        ctx.trend = [(p["date"], p["trend_kg"]) for p in resp.json()["points"]]

    def ask_with_claimed_day(self, lens: str, claimed_day: str) -> Any:
        path = {"raw": "/entries", "trend": "/trend"}[lens]
        return self.comp.actor().get(
            path, params={"scale": TimeScale.ONE_WEEK.value, "today": claimed_day}
        )

    # -- outcome assertions ---------------------------------------------------------

    def assert_anchor_names(self, ctx: SimpleNamespace, day: date, kg: float) -> None:
        assert day == self._device_day() - timedelta(days=1), (
            "scenario frame: the named day must be the phone's own yesterday"
        )
        shown = self.comp.screen.shown_yesterday_kg(ctx)
        assert shown == kg, (
            f"at the skew moment the yesterday anchor must name {day}'s {kg:.1f} kg "
            f"(the phone's yesterday), but the screen shows {shown} -- "
            "the server clock framed the day"
        )

    def assert_trend_spans_exactly(self, ctx: SimpleNamespace, start: date, end: date) -> None:
        expected = [
            (start + timedelta(days=offset)).isoformat() for offset in range((end - start).days + 1)
        ]
        days = sorted(day for day, _ in ctx.trend)
        assert days == expected, (
            f"the 1W trend must span exactly {start}..{end} in the phone's frame, got "
            f"{days[0] if days else '-'}..{days[-1] if days else '-'} ({len(days)} days)"
        )

    def assert_garbled_day_refused(self, ctx: SimpleNamespace) -> None:
        assert ctx.response.status_code == 400, (
            "a garbled day claim must be turned away with 400 (C6: parse totally, "
            f"never a silent ignore, never a 500), got {ctx.response.status_code}"
        )


# ---------------------------------------------------------------- graph-first home

#: Executable markup contract for graph-first-home (US-010/011/012, DISTILL 2026-07-24):
#: the front-page graph mounts at id="home-graph" carrying data-view/data-scale
#: exactly like the History page's #graph-page; the recent list is a server-rendered
#: <ul id="recent-entries"> of "Fri 24 Jul — 82.2 kg" rows; the History page's
#: complete record is <ul id="history-entries"> speaking the same row grammar.
HOME_GRAPH_MOUNT = re.compile(r'<[a-z]+[^>]*id="home-graph"[^>]*>')
RECENT_LIST_BLOCK = re.compile(r'<ul id="recent-entries".*?</ul>', re.S)
HISTORY_LIST_BLOCK = re.compile(r'<ul id="history-entries".*?</ul>', re.S)
LIST_ROW = re.compile(r"<li[^>]*>\s*([^<]+?)\s*</li>")
TOUCH_AFFORDANCE = re.compile(r"<(a|button|input|form|select|textarea)\b")

#: ADR-009 intent-telemetry read surface (DISTILL contract; Q2 resolved: raw
#: rolling-week event counts over the SAME week frame as trend_views_this_week,
#: no read-time session collapse). Deliberate = trend.study.opened +
#: trend.study.interaction; ambient = home.graph.shown deliveries.
STUDY_COUNT_KEY = "trend_study_this_week"
AMBIENT_COUNT_KEY = "home_graph_shown_this_week"
BEACON_PATH = "/telemetry/trend-study"
GRAPH_MODULE_PATH = "/static/graph.js"
ALL_SCALE_WINDOWS = ("1W", "1M", "3M", "6M", "1Y", "ALL")


def entry_row_text(day: date, kg: float) -> str:
    """The one row grammar every entries list speaks (A18): 'Fri 24 Jul — 82.2 kg'.

    Its day half is `day_label` (D-24), so this oracle cannot fork a second
    calendar wording any more than the production side can -- and it stays an
    INDEPENDENT re-derivation: nothing here imports the server's own formatter."""
    return f"{day_label(day)} — {kg:.1f} kg"


class HomeGraphService(_Service):
    """Front-page ambient graph (US-010, ADR-008): served mount + full controls +
    defaults, driven by the same shared engine and the same telemetry-free data
    reads as the History page. Client paint itself is structural (one extracted
    module, D-15) and verified at DELIVER dogfood -- the glance/theme precedent."""

    def _today_iso(self) -> str:
        return (self.comp.device_day or self.comp.fake_clock.today()).isoformat()

    def _ambient_points(self) -> list[dict[str, Any]]:
        resp = self.comp.observer().get(
            "/trend", params={"scale": TimeScale.THREE_MONTHS.value, "today": self._today_iso()}
        )
        assert resp.status_code == 200, f"the morning series read failed: {resp.status_code}"
        return resp.json()["points"]

    # -- served shape ---------------------------------------------------------

    def assert_curve_above_form(self, ctx: SimpleNamespace) -> None:
        html = ctx.response.text
        mount = HOME_GRAPH_MOUNT.search(html)
        assert mount, "the front page must offer the trend graph (a #home-graph mount)"
        assert mount.start() < html.index("<form"), (
            "the graph must sit ABOVE the entry form (D6/D7)"
        )

    def assert_full_controls(self, ctx: SimpleNamespace) -> None:
        html = ctx.response.text
        for lens in ('data-lens="trend"', 'data-lens="raw"'):
            assert lens in html, f"the graph must offer the full lens toggle, missing {lens}"
        missing = [w for w in ALL_SCALE_WINDOWS if f'data-window="{w}"' not in html]
        assert not missing, f"the scale picker must offer every window (D7), missing {missing}"

    def assert_opens_at_defaults(self, ctx: SimpleNamespace, scale: TimeScale) -> None:
        mount = HOME_GRAPH_MOUNT.search(ctx.response.text)
        assert mount, "the front page must offer the trend graph (a #home-graph mount)"
        for state in ('data-view="trend"', f'data-scale="{scale.value}"'):
            assert state in mount.group(0), (
                f"the front-page graph must open at the ambient defaults (A17/D-20), "
                f"missing {state} on the mount: {mount.group(0)}"
            )

    def assert_shared_engine(self, ctx: SimpleNamespace) -> None:
        surfaces = {"front page": ctx.response.text, "History page": self.comp.graph.open().text}
        missing = [name for name, html in surfaces.items() if GRAPH_MODULE_PATH not in html]
        assert not missing, (
            f"both surfaces must drive the ONE shared graph module (ADR-008), missing on: {missing}"
        )
        served = self.comp.actor().get(GRAPH_MODULE_PATH)
        assert served.status_code == 200, (
            f"the shared graph module must be delivered by the tracker itself, "
            f"got {served.status_code}"
        )

    def assert_absent(self, ctx: SimpleNamespace) -> None:
        assert not HOME_GRAPH_MOUNT.search(ctx.response.text), (
            "an empty record must keep the front page simple -- no graph area (A18 kin)"
        )

    def assert_no_focus_theft(self, ctx: SimpleNamespace) -> None:
        html = ctx.response.text
        assert html.count("autofocus") == 1, (
            "exactly one autofocus belongs on the morning screen: the weight field (Q4)"
        )
        weight_field = re.search(r'<input[^>]*id="weight"[^>]*>', html)
        assert weight_field and "autofocus" in weight_field.group(0), (
            "the weight field must keep the morning focus (D6: keypad-cover accepted, "
            "focus theft is not)"
        )
        assert "tabindex" not in html, "no element may reorder the morning focus (Q4)"

    # -- in-place repaint (A15/D-19) ------------------------------------------

    def note_series_end(self, ctx: SimpleNamespace) -> None:
        ctx.series_end = self._ambient_points()[-1]["date"]

    def assert_series_includes_today(self, ctx: SimpleNamespace) -> None:
        last = self._ambient_points()[-1]["date"]
        assert last == self._today_iso(), (
            f"the refreshed morning picture must include today's entry, the line ends at {last}"
        )

    # -- fault injection (no new driven adapters => degrade paths, DESIGN) ----

    def break_series(self, monkeypatch: Any) -> None:
        """The trend series computation fails: the graph data reads must degrade
        (absent area client-side) while entry, save, and confirmation are untouched."""

        def failing_series(*_args: Any, **_kwargs: Any) -> Any:
            raise RuntimeError("injected trend-series failure (acceptance fault injection)")

        for target in (
            "weight_tracker.core.trend.trend_series",
            "weight_tracker.web.routes.trend_series_in",
            "weight_tracker.composition.trend_series",
        ):
            monkeypatch.setattr(target, failing_series, raising=False)
        self.comp.system.restart()

    def series_read_admits_trouble(self, ctx: SimpleNamespace) -> None:
        before = self.comp.study.trail_counts()
        troubled = False
        try:
            resp = self.comp.actor().get("/trend", params={"scale": "3M"})
            troubled = resp.status_code >= 400
        except Exception:
            troubled = True
        assert troubled, "a broken series must not pretend to answer"
        assert self.comp.study.trail_counts() == before, (
            "a failed series read must leave no mark on the trail (pure read, D-16)"
        )


class RecentListService(_Service):
    """Last-7 entries list (US-011, A18/D9): server-rendered, display-only,
    entries not days, gaps simply absent; refreshed on the save response (D-19)."""

    def _rows(self, html: str) -> list[str]:
        block = RECENT_LIST_BLOCK.search(html)
        assert block, "the front page must carry the recent-entries list (#recent-entries)"
        return [match.group(1).strip() for match in LIST_ROW.finditer(block.group(0))]

    def _stored_rows(self, limit: int = 7) -> list[str]:
        entries = self.comp.observer().get("/entries", params={"scale": "ALL"}).json()["entries"]
        return [
            entry_row_text(date.fromisoformat(e["date"]), e["weight_kg"]) for e in entries[:limit]
        ]

    def assert_last_seven(self, ctx: SimpleNamespace) -> None:
        rows = self._rows(ctx.response.text)
        expected = self._stored_rows()
        assert rows == expected, (
            f"the recent list must show the last 7 ENTRIES newest first (A18), "
            f"expected {expected}, shown {rows}"
        )

    def assert_begins_with(self, ctx: SimpleNamespace, text: str) -> None:
        rows = self._rows(ctx.response.text)
        assert rows and rows[0] == text, (
            f"the recent list must begin with {text!r}, it begins with "
            f"{rows[0] if rows else 'nothing'!r}"
        )

    def screen_begins_with(self, ctx: SimpleNamespace, text: str) -> None:
        probe = SimpleNamespace(response=self.comp.screen.open_entry())
        self.assert_begins_with(probe, text)

    def assert_day_absent(self, ctx: SimpleNamespace, day: date) -> None:
        rows = self._rows(ctx.response.text)
        marker = day_label(day)
        offenders = [row for row in rows if marker in row or "0.0 kg" in row]
        assert not offenders, (
            f"a missed day must be simply absent -- no zero, no placeholder (A18), "
            f"but the list carries {offenders}"
        )

    def assert_exactly(self, ctx: SimpleNamespace, count: int) -> None:
        rows = self._rows(ctx.response.text)
        expected = self._stored_rows(limit=count)
        assert rows == expected and len(rows) == count, (
            f"a young record must show exactly its {count} entries, shown {rows}"
        )

    def assert_none(self, ctx: SimpleNamespace) -> None:
        assert not RECENT_LIST_BLOCK.search(ctx.response.text), (
            "an empty record must show no recent list at all (A18)"
        )

    def assert_display_only(self, ctx: SimpleNamespace) -> None:
        block = RECENT_LIST_BLOCK.search(ctx.response.text)
        assert block, "the front page must carry the recent-entries list (#recent-entries)"
        touched = TOUCH_AFFORDANCE.search(block.group(0))
        assert not touched, (
            f"looking is not touching (D9): the recent list must offer no affordances, "
            f"found <{touched.group(1)}>"
        )

    def assert_values_match_store(self, ctx: SimpleNamespace) -> None:
        rows = self._rows(ctx.response.text)
        expected = self._stored_rows(limit=len(rows))
        assert rows == expected, (
            f"every recent value must equal the stored entry for its day "
            f"(single source), expected {expected}, shown {rows}"
        )

    def assert_save_response_top(self, ctx: SimpleNamespace) -> None:
        payload = ctx.response.json()
        recent = payload.get("recent")
        assert recent is not None, (
            "the save response must hand back the refreshed recent list (`recent`, D-19)"
        )
        today = self.comp.resolve_day("today").isoformat()
        assert recent and recent[0]["date"] == today and len(recent) <= 7, (
            f"the refreshed recent list must carry today's save on top "
            f"(<=7 entries, newest first), got {recent}"
        )


class HistoryRecordService(_Service):
    """Complete record on the History page (US-012, D-17): server-rendered from
    the same all-entries read the raw plot draws, ALWAYS the whole record
    regardless of the chart's window; /graph behaviors preserved (A16)."""

    def open_timed(self, ctx: SimpleNamespace) -> Any:
        started = time.monotonic()
        resp = self.comp.actor().get("/graph")
        ctx.elapsed_ms = (time.monotonic() - started) * 1000
        return resp

    def _rows(self, html: str) -> list[str]:
        block = HISTORY_LIST_BLOCK.search(html)
        assert block, "the History page must carry the complete record (#history-entries)"
        return [match.group(1).strip() for match in LIST_ROW.finditer(block.group(0))]

    def _all_stored_rows(self) -> list[str]:
        entries = self.comp.observer().get("/entries", params={"scale": "ALL"}).json()["entries"]
        return [entry_row_text(date.fromisoformat(e["date"]), e["weight_kg"]) for e in entries]

    def assert_complete_newest_first(self, ctx: SimpleNamespace) -> None:
        html = ctx.response.text
        rows = self._rows(html)
        expected = self._all_stored_rows()
        assert rows == expected, (
            f"the complete record must list every stored entry newest first "
            f"({len(expected)} entries), the page lists {len(rows)}"
        )
        assert html.index('id="chart"') < html.index('id="history-entries"'), (
            "the complete record belongs BENEATH the graph (D8)"
        )

    def assert_days_absent(self, ctx: SimpleNamespace, start: date, end: date) -> None:
        rows = self._rows(ctx.response.text)
        gap_days = [start + timedelta(days=offset) for offset in range((end - start).days + 1)]
        offenders = [row for row in rows for day in gap_days if day_label(day) in row]
        assert not offenders, (
            f"days without an entry must be absent from the list exactly as they are "
            f"gaps in the plot, but the list carries {offenders}"
        )

    def assert_matches_raw_plot(self, ctx: SimpleNamespace) -> None:
        rows = self._rows(ctx.response.text)
        plotted = self._all_stored_rows()  # the raw plot draws from the same /entries read
        assert rows == plotted, (
            f"the list and the plot must tell the same story (single source, D-18): "
            f"list {len(rows)} rows vs stored {len(plotted)} entries"
        )

    def assert_back_link(self, ctx: SimpleNamespace) -> None:
        assert 'href="/"' in ctx.response.text, (
            "the way back to today's entry must stay one tap away (A16)"
        )

    def assert_invite_offered(self, ctx: SimpleNamespace) -> None:
        assert 'id="empty-invite"' in ctx.response.text, (
            "an empty record must still offer the first-log invite (A16)"
        )

    def assert_none(self, ctx: SimpleNamespace) -> None:
        assert not HISTORY_LIST_BLOCK.search(ctx.response.text), (
            "an empty record renders no list -- only the first-log invite (A16)"
        )

    def assert_ready_within(self, ctx: SimpleNamespace, budget_ms: int) -> None:
        assert ctx.response.status_code == 200
        assert ctx.elapsed_ms <= budget_ms, (
            f"the History page took {ctx.elapsed_ms:.0f} ms with the complete record, "
            f"budget {budget_ms} ms (G-2 extended)"
        )


class StudyService(_Service):
    """Intent telemetry (ADR-009): deliberate study = History-page opens +
    explicit lens/scale taps (the beacon, closed vocabulary); ambient = home
    graph deliveries. KPI-3 purity is asserted on the /stats read surface."""

    def _stats(self) -> dict[str, Any]:
        return self.comp.observer().get("/stats").json()

    def deliberate_count(self) -> int:
        count = self._stats().get(STUDY_COUNT_KEY)
        assert count is not None, (
            f"/stats must serve {STUDY_COUNT_KEY} -- KPI-3's new home (ADR-009)"
        )
        return count

    def trail_counts(self) -> dict[str, Any]:
        body = self._stats()
        keys = (STUDY_COUNT_KEY, AMBIENT_COUNT_KEY, "trend_view_opened_count", "entry_logged_count")
        return {key: body.get(key) for key in keys}

    # -- journey moves --------------------------------------------------------

    def log_only_morning(self, ctx: SimpleNamespace, raw_weight: str) -> None:
        """The ambient path end-to-end: open, ambient fetch, save, post-save
        refetch -- exactly what a log-only morning drives, and nothing else."""
        actor, today = self.comp.actor(), self.comp.resolve_day("today").isoformat()
        ctx.response = actor.get("/")
        actor.get("/trend", params={"scale": "3M", "today": today})
        self.comp.logging.record("today", raw_weight)
        actor.get("/trend", params={"scale": "3M", "today": today})

    def tap(self, surface: str, control: str, value: str) -> Any:
        resp = self.comp.actor().post(
            BEACON_PATH, json={"surface": surface, "control": control, "value": value}
        )
        assert resp.status_code < 300, (
            f"an explicit {control} tap must be accepted as deliberate study "
            f"(the beacon, ADR-009), got {resp.status_code}"
        )
        return resp

    def choose_scale_then_raw(self, ctx: SimpleNamespace, window: str) -> None:
        ctx.study_before = self._stats().get(STUDY_COUNT_KEY) or 0
        self.tap("home", "scale", window)
        self.tap("home", "lens", "raw")

    def send_garbled(self, ctx: SimpleNamespace) -> None:
        ctx.trail_before = self.trail_counts()
        ctx.beacon_response = self.comp.actor().post(
            BEACON_PATH, json={"surface": "kitchen", "control": "mood", "value": "loud"}
        )

    def stranger_taps(self, ctx: SimpleNamespace) -> None:
        from fastapi.testclient import TestClient

        ctx.trail_before = self.trail_counts()
        stranger = TestClient(self.comp._build(), raise_server_exceptions=True)
        ctx.beacon_response = stranger.post(
            BEACON_PATH, json={"surface": "home", "control": "scale", "value": "1Y"}
        )

    # -- outcome assertions ---------------------------------------------------

    def assert_deliberate(self, expected: int) -> None:
        count = self.deliberate_count()
        assert count == expected, (
            f"the deliberate trend-study count must read {expected} (A19), /stats reads {count}"
        )

    def assert_ambient_delivery(self) -> None:
        count = self._stats().get(AMBIENT_COUNT_KEY)
        assert count is not None, (
            f"/stats must serve {AMBIENT_COUNT_KEY} -- KPI-7's instrument (ADR-009)"
        )
        assert count >= 1, "the morning graph delivery must be on the record (KPI-7)"

    def assert_taps_counted(self, ctx: SimpleNamespace, taps: int) -> None:
        self.assert_deliberate(getattr(ctx, "study_before", 0) + taps)

    def assert_refused_unintelligible(self, ctx: SimpleNamespace) -> None:
        assert ctx.beacon_response.status_code == 400, (
            f"an unknown study vocabulary must be refused with 400 -- never served, "
            f"never a 500 (closed vocabulary, ADR-009), got "
            f"{ctx.beacon_response.status_code}"
        )

    def assert_stranger_turned_away(self, ctx: SimpleNamespace) -> None:
        assert ctx.beacon_response.status_code in (303, 401), (
            f"the beacon sits behind the same door as every route (AccessGate), "
            f"got {ctx.beacon_response.status_code}"
        )

    def assert_no_study_mark(self, ctx: SimpleNamespace) -> None:
        self.deliberate_count()  # the counter must exist for "no mark" to mean anything
        assert self.trail_counts() == ctx.trail_before, (
            "a refused or stranger's signal must leave the trail untouched"
        )


# ---------------------------------------------------------------- dated entry

#: Executable markup contract (entry-date-picker, DISTILL 2026-07-24): the date
#: row is a native <input type="date" id="entry-date"> INSIDE the entry form and
#: ABOVE the weight field. `min` (first entry day - 1 year, D-25/OQ-11) is the
#: only bound the server can supply; `value` and `max` come from the phone's own
#: day (A5 -- the server has no device day), so they are client-structural and
#: verified at dogfood (client-paint precedent, D-15). The server's skew-bounded
#: no-future rule stays authoritative and IS asserted here.
DATE_ROW = re.compile(r'<input[^>]*id="entry-date"[^>]*>')
DATE_ROW_EARLIEST = re.compile(r'min="(\d{4}-\d{2}-\d{2})"')
#: ONE hint node (D-24) carrying three mutually exclusive states: the yesterday
#: anchor, `Editing {day} — was {v} kg`, `No entry for {day} yet`. "Never two
#: hints at once" is STRUCTURAL -- there is one node -- not a convention.
ENTRY_HINT_NODE = re.compile(r'<[a-z]+[^>]*id="entry-hint"[^>]*>')
RETIRED_ANCHOR_NODE = re.compile(r'id="yesterday-reference"')

#: /stats key for in-app repairs (KPI-8): backdated saves over the same rolling
#: week frame as every counter beside it.
REPAIR_COUNT_KEY = "backdated_saves_this_week"

#: Trail-only universe (Mandate 8) for the KPI-1 purity promise (A23/ADR-011).
#: The record's own delta is the co-located "holds exactly one entry" step's
#: promise, declared over UNIVERSE there; these scenarios promise what a save
#: does to the TRAIL, fail-closed.
PURITY_UNIVERSE = {
    "telemetry.entry_logged_count",
    "telemetry.speed_sample_count",
    "telemetry.repair_count",
}


class DatedEntryService(_Service):
    """The date row, the whole-record map, and write-time save classification
    (US-013 + US-014, ADR-010 + ADR-011).

    DELIVER-facing HTTP contract (executable spec):
        GET  /        -> the entry form carries `#entry-date` (native date input,
                         no autofocus) above `#weight`, with `min` = first entry
                         day - 1 year (omitted on an empty record); ONE `#entry-hint`
                         node replaces `#yesterday-reference`; the inline script's
                         map widens to the WHOLE record as {iso_day: kg}
                         (`const recordWeights = {...}`) -- one map for the anchor
                         AND the prefill, so the two can never disagree.
        POST /entries -> accepts an additive, optional `today` claim (the phone's
                         own day). After validation, `backdated = date != claimed
                         day` (skew-clamped; absent/garbled falls back to the
                         server's UTC day and never 400s). A backdated save records
                         entry_ms as NULL -- 0 KPI-1 samples via the shipped
                         null-skip -- and carries "backdated": true on its
                         entry.saved payload. Response shape unchanged.
        GET  /stats   -> gains `backdated_saves_this_week` (KPI-8), same rolling
                         week as its neighbours.

    Oracles: the record read-back (`/entries?scale=ALL`) for the map, the shipped
    pure `trend_series` for the post-repair recompute, and the server's own row
    grammar for the hint's day label -- never a second wording invented here."""

    # -- what the tracker serves ------------------------------------------------

    def _date_row(self, ctx: SimpleNamespace) -> str:
        found = DATE_ROW.search(ctx.response.text)
        assert found, (
            "the entry screen must offer a date row (a native #entry-date input) "
            "so a past day can be repaired where the habit lives"
        )
        return found.group(0)

    def assert_row_above_field(self, ctx: SimpleNamespace) -> None:
        html, row = ctx.response.text, self._date_row(ctx)
        assert 'type="date"' in row, (
            f"the date row must be the phone's OWN picker -- a native date input (D6), got {row}"
        )
        assert html.index("<form") < html.index(row) < html.index('id="weight"'), (
            "the date row belongs inside the entry form, above the weight field (D6)"
        )

    def assert_no_focus_theft(self, ctx: SimpleNamespace) -> None:
        assert "autofocus" not in self._date_row(ctx), (
            "the date row must never take the morning focus -- the keypad comes up "
            "on the weight field, as it always did (D6/D-25)"
        )
        self.comp.home_graph.assert_no_focus_theft(ctx)

    def assert_reaches_back_to(self, ctx: SimpleNamespace, day: date) -> None:
        row = self._date_row(ctx)
        earliest = DATE_ROW_EARLIEST.search(row)
        assert earliest and earliest.group(1) == day.isoformat(), (
            f"a mistyped year would stretch every recompute for good: the date row's "
            f"earliest day must be {day} (the record's first day minus a year, OQ-11), "
            f"row: {row}"
        )

    # -- the map that answers ANY stored day (ADR-010) --------------------------

    def _offered(self, ctx: SimpleNamespace) -> dict[str, float]:
        weights = embedded_weights(ctx.response.text)
        assert weights is not None, (
            "the entry screen must hand the phone the record's day-to-weight map -- "
            "ONE map answering both the yesterday anchor and the edit prefill (ADR-010)"
        )
        return weights

    def _stored(self) -> dict[str, float]:
        shown = self.comp.observer().get("/entries", params={"scale": TimeScale.ALL.value}).json()
        return {entry["date"]: entry["weight_kg"] for entry in shown["entries"]}

    def assert_offers(self, ctx: SimpleNamespace, day: date, kg: float) -> None:
        offered = self._offered(ctx).get(day.isoformat())
        assert offered == kg, (
            f"picking {day} must offer its stored {kg:.1f} kg back for correction -- "
            f"any stored day, however old (A24) -- but the screen offers {offered}"
        )

    def assert_offers_whole_record(self, ctx: SimpleNamespace) -> None:
        offered, stored = self._offered(ctx), self._stored()
        assert offered == stored, (
            f"every stored day must answer with its own value (ADR-010): {len(stored)} "
            f"days stored, {len(offered)} offered; first disagreements "
            f"{sorted(set(stored.items()) ^ set(offered.items()))[:5]}"
        )

    def assert_offers_nothing_for(self, ctx: SimpleNamespace, day: date) -> None:
        assert day.isoformat() not in self._offered(ctx), (
            f"a day without an entry must come back as a gap, never as a value -- "
            f"a blind overwrite is exactly what the prefill exists to prevent ({day})"
        )

    def assert_nothing_to_correct(self, ctx: SimpleNamespace) -> None:
        assert self._offered(ctx) == {}, (
            "an empty record offers nothing to correct, and the save path is "
            "untouched either way (degrade-to-absent)"
        )

    # -- one hint line, one grammar (D-24) --------------------------------------

    def assert_single_hint_line(self, ctx: SimpleNamespace) -> None:
        html = ctx.response.text
        nodes = ENTRY_HINT_NODE.findall(html)
        assert len(nodes) == 1, (
            f"ONE hint line serves the anchor, the editing hint and the no-entry hint: "
            f"'never two at once' is structural, but the screen carries {len(nodes)}"
        )
        assert not RETIRED_ANCHOR_NODE.search(html), (
            "the anchor's old node is absorbed INTO the one hint line, never kept beside it"
        )

    def assert_hint_speaks_record_grammar(self, ctx: SimpleNamespace) -> None:
        """The hint names its day in the ONE grammar the record already speaks:
        the label the phone renders must equal the day half of the server's own
        row for that day -- no second calendar wording (D-24, Mandate-12)."""
        stored = self._stored()
        assert stored, "the grammar check needs at least one stored day"
        newest = date.fromisoformat(max(stored))
        block = RECENT_LIST_BLOCK.search(ctx.response.text)
        assert block, "the grammar check reads the record's own rendered row"
        newest_row = LIST_ROW.search(block.group(0))
        assert newest_row and newest_row.group(1).strip().split(" — ")[0] == day_label(newest), (
            f"the hint must name its day in the record's own grammar ({day_label(newest)!r}), "
            f"but the record renders {newest_row and newest_row.group(1)!r}"
        )

    # -- write-time classification (ADR-011): the trail --------------------------

    def capture_trail(self) -> dict[str, Any]:
        """Snapshot of what a save may move on the trail. Deliberately TOLERANT of a
        missing KPI-8 counter (None) so a scenario fails at its OWN first missing
        thing rather than at the capture -- the repair-count assertions below
        demand the counter explicitly."""
        stats = self.comp.observer().get("/stats").json()
        return {
            "telemetry.entry_logged_count": stats["entry_logged_count"],
            "telemetry.speed_sample_count": stats["speed"]["sample_count"],
            "telemetry.repair_count": stats.get(REPAIR_COUNT_KEY),
            # extra slot, deliberately outside PURITY_UNIVERSE: a morning legitimately
            # moves the median, a repair must not (the R-2 corruption guard).
            "telemetry.speed_median_ms": stats["speed"]["median_ms"],
        }

    def remember(self, ctx: SimpleNamespace) -> None:
        """Both promises captured before the save: the record's and the trail's."""
        ctx.before = self.comp.capture_universe()
        ctx.trail_before = self.capture_trail()

    def assert_mornings_unchanged(self, ctx: SimpleNamespace) -> None:
        """KPI-1 purity (A23): however long the repair took, the week's morning
        record neither gains a sample nor shifts its median -- and correcting a
        timed morning does not erase what that morning already cost (the trail is
        the KPI-1 source of truth, R-2)."""
        after, before = self.capture_trail(), ctx.trail_before
        for slot in ("telemetry.speed_sample_count", "telemetry.speed_median_ms"):
            assert after[slot] == before[slot], (
                f"a repair must leave the morning-speed record exactly as it was "
                f"({slot}: {before[slot]} -> {after[slot]}) -- one slow backfill would "
                f"otherwise poison the week the five-second target guards"
            )

    def _require_repair_counter(self, snapshot: dict[str, Any]) -> None:
        assert snapshot["telemetry.repair_count"] is not None, (
            f"the stats page must count in-app repairs ({REPAIR_COUNT_KEY!r}, KPI-8): "
            "a gap or typo repaired in the app is the whole point of the date row"
        )

    def assert_repair_counted(self, ctx: SimpleNamespace) -> None:
        self._require_repair_counter(ctx.trail_before)
        assert_state_delta(
            before=ctx.trail_before,
            after=self.capture_trail(),
            universe=PURITY_UNIVERSE,
            expected={
                "telemetry.entry_logged_count": set_to(
                    ctx.trail_before["telemetry.entry_logged_count"] + 1
                ),
                "telemetry.repair_count": set_to(ctx.trail_before["telemetry.repair_count"] + 1),
                "telemetry.speed_sample_count": unchanged(),
            },
        )

    def assert_morning_counted(self, ctx: SimpleNamespace) -> None:
        self._require_repair_counter(ctx.trail_before)
        assert_state_delta(
            before=ctx.trail_before,
            after=self.capture_trail(),
            universe=PURITY_UNIVERSE,
            expected={
                "telemetry.entry_logged_count": set_to(
                    ctx.trail_before["telemetry.entry_logged_count"] + 1
                ),
                "telemetry.speed_sample_count": set_to(
                    ctx.trail_before["telemetry.speed_sample_count"] + 1
                ),
                "telemetry.repair_count": unchanged(),
            },
        )

    def assert_no_repair_counted(self, ctx: SimpleNamespace) -> None:
        after = self.capture_trail()
        self._require_repair_counter(after)
        assert after["telemetry.repair_count"] == ctx.trail_before["telemetry.repair_count"], (
            "a same-day morning is not a repair: the KPI-8 counter must not move"
        )

    def assert_trail_untouched(self, ctx: SimpleNamespace) -> None:
        self._require_repair_counter(ctx.trail_before)
        assert_state_delta(
            before=ctx.trail_before,
            after=self.capture_trail(),
            universe=PURITY_UNIVERSE,
            expected={},  # fail-closed: a refused save marks neither speed nor repairs
        )

    # -- the refreshed picture (A22) + the recompute -----------------------------

    def assert_handed_back(self, ctx: SimpleNamespace, row_text: str) -> None:
        body = ctx.response.json()
        recent = body.get("recent")
        assert recent is not None, (
            "the save must hand back the refreshed picture (`recent`, D-19) -- a repair "
            "refreshes in place exactly like a morning log"
        )
        rows = [entry_row_text(date.fromisoformat(e["date"]), e["weight_kg"]) for e in recent]
        assert rows.count(row_text) == 1, (
            f"the repaired day must stand exactly ONCE in the refreshed picture "
            f"(one entry per day), expected {row_text!r} among {rows}"
        )
        assert "glance" in body, "the repair's response carries the recomputed glance beside it"

    def assert_trend_reflects(self, day: date) -> None:
        """The trend recomputes over the repaired record: the served line equals the
        shipped pure series over the CURRENT entry set, and covers the repaired day."""
        stored = self._stored()
        entries = [
            Entry(day=date.fromisoformat(iso), weight_kg=kg) for iso, kg in sorted(stored.items())
        ]
        expected = [
            (point.day.isoformat(), round(point.trend_kg, 9)) for point in trend_series(entries)
        ]
        served = self.comp.observer().get("/trend", params={"scale": TimeScale.ALL.value}).json()
        shown = [(point["date"], round(point["trend_kg"], 9)) for point in served["points"]]
        assert shown == expected, (
            "after a repair the trend must be recomputed over the whole repaired record "
            f"({len(expected)} days expected, {len(shown)} served)"
        )
        assert day.isoformat() in {shown_day for shown_day, _ in shown}, (
            f"the repaired day {day} must be part of the trend the record now tells"
        )
