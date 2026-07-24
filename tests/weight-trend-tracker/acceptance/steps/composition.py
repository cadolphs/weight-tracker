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
    POST /entries {date, weight, entry_ms?}  -> {"outcome":"saved","confirmation":...,
                                                 "date","weight_kg"}
                                              | {"outcome":"rejected",
                                                 "reason":<RejectionReason value>,
                                                 "echo":<raw input>}   (401 when locked)
    GET  /trend?scale=...                    -> {"points":[{"date","trend_kg"}...]} (+event)
    GET  /graph?view=trend|raw&scale=...     -> HTML with data-view=... data-scale=...
    GET  /                                   -> entry screen HTML (autofocus, inputmode="decimal",
                                                "yesterday: X kg" when it exists)
    GET  /stats                              -> {"entry_logged_count","trend_view_opened_count",
                                                 "trend_views_this_week",
                                                 "speed":{"median_ms","p90_ms","sample_count"}}
    GET  /healthz                            -> 200 {"status":"ok",...} without auth
    GET  /manifest.webmanifest               -> 200 PWA manifest
"""

from __future__ import annotations

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
    MIN_CONTRAST_RATIO,
    TEST_PASSPHRASE,
    ColorScheme,
    ContrastClass,
    RateDisposition,
    RejectionReason,
    Screen,
    TimeScale,
    TrendDirection,
    ViewMode,
    contrast_ratio,
    dark_override_names,
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

    # -- seeding (always through the driving port, never the store) ---------------

    def seed(self, day: date, kg: float, entry_ms: int | None = None) -> None:
        payload: dict[str, Any] = {"date": day.isoformat(), "weight": f"{kg:.1f}"}
        if entry_ms is not None:
            payload["entry_ms"] = entry_ms
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
        timings = [4200, 3900, 5100, 4400, 4800, 6900, 4100]
        for offset, ms in enumerate(timings):
            self.seed(end - timedelta(days=6 - offset), 82.4, entry_ms=ms)
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

    def assert_yesterday(self, ctx: SimpleNamespace, kg: float) -> None:
        assert f"yesterday: {kg:.1f} kg" in ctx.response.text, (
            f"expected the reference 'yesterday: {kg:.1f} kg' beside the input"
        )

    def assert_no_yesterday(self, ctx: SimpleNamespace) -> None:
        assert "yesterday:" not in ctx.response.text, (
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
        body = self.comp.observer().get("/stats").json()
        assert body["trend_views_this_week"] == n, (
            f"expected {n} trend view(s) counted this week, got {body['trend_views_this_week']}"
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
        GET  /trend   -> UNTOUCHED: still emits `trend.view.opened` per open (KPI-3
                         separation is structural -- the glance never touches it).

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
        for _ in range(times):
            self.comp.actor().get("/trend", params={"scale": TimeScale.ONE_MONTH.value})

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

    def assert_no_new_entry_moving_parts(self, ctx: SimpleNamespace) -> None:
        entry_html = ctx.dressed_pages[Screen.ENTRY]
        scripts = entry_html.count("<script")
        assert scripts == 1 and "<script src" not in entry_html, (
            "the morning screen must gain no new moving parts (G-5: zero new "
            f"entry-screen scripts beyond the existing inline one), found {scripts}"
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
