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
import stat
import time
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from argon2 import PasswordHasher
from domain_types import (
    TEST_PASSPHRASE,
    RejectionReason,
    TimeScale,
    ViewMode,
    parse_day,
)
from fake_clock import FakeClock
from state_delta import assert_state_delta, set_to, unchanged

from weight_tracker.composition import StartupRefused, build_app

UNIVERSE = {
    "record.entries",
    "telemetry.entry_logged_count",
    "telemetry.trend_view_opened_count",
}

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


class AccessService(_Service):
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
