"""The tracker's first services (milestones 1-5): the clock, the door, logging and
seeding, the record read, the trend read, the History page, the morning screen,
the speed report, health, and the system itself."""

from __future__ import annotations

import os
import stat
import statistics
from collections.abc import Sequence
from datetime import date, timedelta
from types import SimpleNamespace
from typing import Any

from domain_types import (
    GARBLED_DAY_CLAIM,
    TEST_PASSPHRASE,
    DayClaim,
    RejectionReason,
    TimeScale,
    ViewMode,
)
from driver import UNIVERSE
from pages import read_door
from state_delta import assert_state_delta, set_to, unchanged

from services._base import BROWSER_HTML, STUDY_COUNT_KEY, Service, timed
from weight_tracker.composition import StartupRefused

#: Day-to-day wobble of a stalled record (US-015 seeds): +-0.1 kg around the level.
PLATEAU_WOBBLE_KG = (0.0, 0.1, -0.1, 0.1, -0.1, 0.0, 0.1, -0.1)


class ClockService(Service):
    def set_today(self, day: date) -> None:
        self.comp.fake_clock.set_today(day)

    def set_device_day(self, day: date) -> None:
        self.comp.device_day = day

    def days_pass(self, days: int) -> None:
        self.comp.fake_clock.advance_days(days)


class AccessService(Service):
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
        door = read_door(ctx.response)
        assert door.is_html, (
            "a locked browser visit must be met by the passphrase door page, "
            f"not {ctx.response.headers.get('content-type')!r}: {door.html[:120]!r}"
        )
        assert door.offers_passphrase_form, (
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
        assert read_door(ctx.response).shows_wrong_passphrase, (
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


class LoggingService(Service):
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

    def seed_plateau(self, kg: float, start: date, end: date) -> None:
        """A stalled stretch: the level held with the day-to-day wobble a 0.1 kg
        scale actually shows (deterministic +-0.1 kg pattern, never a flat line,
        so the trend has SOMETHING to smooth -- US-015's 'stalled month')."""
        for offset in range((end - start).days + 1):
            wobble = PLATEAU_WOBBLE_KG[offset % len(PLATEAU_WOBBLE_KG)]
            self.seed(start + timedelta(days=offset), round(kg + wobble, 1))

    def seed_mornings(self, values: Sequence[float], end: date) -> None:
        """A run of consecutive mornings ending on `end`, oldest value first."""
        for offset, kg in enumerate(reversed(values)):
            self.seed(end - timedelta(days=offset), kg)

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
        day = self.comp.resolve_day(day_spec)
        top = self.comp.stored_entries()[0]
        assert (top.day, top.weight_kg) == (day, kg), (
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


class HistoryService(Service):
    def open(self, scale: TimeScale) -> Any:
        return self.comp.actor().get("/entries", params={"scale": scale.value})

    def open_timed(self, scale: TimeScale, ctx: SimpleNamespace) -> Any:
        return timed(ctx, lambda: self.open(scale))

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
        self.assert_opened_within(ctx, budget_ms, "history")


class TrendService(Service):
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


class GraphService(Service):
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
        page = self.history_page(ctx)
        assert page.view == view.value, f"expected the {view.value} view"
        assert page.scale == scale.value, f"expected the {scale.value} window preserved"

    def assert_default_is_trend(self, ctx: SimpleNamespace) -> None:
        assert self.history_page(ctx).view == "trend", "the trend must be the default lens"


class ScreenService(Service):
    def open_entry(self) -> Any:
        return self.comp.actor().get("/")

    def open_entry_timed(self, ctx: SimpleNamespace) -> Any:
        return timed(ctx, self.open_entry)

    def assert_ready_within(self, ctx: SimpleNamespace, budget_ms: int) -> None:
        self.assert_opened_within(ctx, budget_ms, "the entry screen")

    def assert_ready_for_typing(self, ctx: SimpleNamespace) -> None:
        screen = self.entry_screen(ctx)
        assert screen.autofocus_count, "the weight field must be focused on open"
        assert screen.decimal_keypad, "a decimal keypad must come up"

    def shown_yesterday_kg(self, ctx: SimpleNamespace) -> float | None:
        """The yesterday anchor as the phone SHOWS it. Post-fix pages embed a
        recent-days map and render client-side: emulate that exact lookup with
        the DEVICE-local yesterday (device_day preferred over the server clock
        via resolve_day -- at the skew moment the two diverge). Pre-fix pages
        carried a server-rendered paragraph: read it, so the regression fails
        on the wrong value shown, never on a missing marker."""
        screen = self.entry_screen(ctx)
        if screen.record_weights is not None:
            return screen.record_weights.get(self.comp.resolve_day("yesterday").isoformat())
        return screen.server_rendered_yesterday_kg

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


class StatsService(Service):
    def open_speed(self) -> Any:
        return self.comp.actor().get("/stats")

    def assert_speed_report(self, ctx: SimpleNamespace, timings: list[int]) -> None:
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
        body = self.comp.served_stats()
        assert body[STUDY_COUNT_KEY] == n, (
            f"expected {n} deliberate trend stud(y/ies) counted this week, "
            f"got {body[STUDY_COUNT_KEY]}"
        )


class HealthService(Service):
    def check_unauthenticated(self) -> Any:
        return self.comp.stranger().get("/healthz")

    def assert_healthy(self, ctx: SimpleNamespace) -> None:
        assert ctx.response.status_code == 200, "health must be visible without the passphrase"
        assert ctx.response.json()["status"] == "ok"


class SystemService(Service):
    def ensure_fresh(self) -> None:
        assert not self.comp.db_path.exists(), "expected an empty record to start from"

    def restart(self) -> None:
        """Recreate the app over the SAME record file (durability contract)."""
        self.comp.restart()

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
