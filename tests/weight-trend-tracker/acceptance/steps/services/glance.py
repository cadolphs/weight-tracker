"""Glance summary on the entry screen (US-007, ADR-006, D-13/D-14)."""

from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from typing import Any

from domain_types import RateDisposition, TimeScale, TrendDirection
from driver import UNIVERSE
from oracles import glance_text, rate_text
from state_delta import assert_state_delta, set_to, unchanged

from services._base import GLANCE_COUNT_KEY, Service

#: Glance-aware universe (US-007). The three shared slots stay untouched for the
#: pre-existing scenarios (their universes are their own declared promises); the
#: glance scenarios additionally track the glance-delivery counter.
GLANCE_UNIVERSE = UNIVERSE | {"telemetry.trend_glance_shown_count"}


class GlanceService(Service):
    """DELIVER-facing HTTP contract (executable spec):
        GET  /        -> when a glance exists, the HTML holds exactly the neutral element
                         (no direction-dependent class/style; rate part absent below
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

    Oracle: the shipped glance rule over the record as read back (`oracles.glance_text`:
    value = series END at 0.1 kg; rate = trailing-week change iff the entry span >= 7
    days, quantized onto the 0.05 grid, glyph from the ROUNDED sign). The glance must
    equal the graph line's own end and trailing-week change for the same entries
    (single-source AC); after a save BOTH revise together (RTS co-revision) -- these
    oracles judge the CURRENT pair's coherence, never prior renderings.
    """

    # -- oracle -------------------------------------------------------------------

    def expected_text(self) -> str | None:
        return glance_text(self.comp.stored_entries())

    def _shown_line(self, ctx: SimpleNamespace) -> str:
        """The CURRENT glance line: the rendered element on an entry-screen response,
        or -- after a save -- the line the saved response carried for the in-place
        refresh (already oracle-checked and remembered as ctx.glance_text)."""
        shown = self.entry_screen(ctx).glance_line
        if shown is not None:
            return shown
        delivered = getattr(ctx, "glance_text", None)
        assert delivered is not None, "expected the glance line on the entry screen, none shown"
        return delivered

    # -- universe (Mandate 8; glance-aware superset of the shared capture) ---------

    def capture(self) -> dict[str, Any]:
        stats = self.comp.served_stats()
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
        assert self.entry_screen(ctx).glance_line is None, "an empty record must show no trend line"
        ctx.glance_before = self.capture()

    def break_computation(self, monkeypatch: Any) -> None:
        """The glance is one derivation inside the picture (ADR-014): a failing
        trend takes the glance line with it. `monkeypatch` is kept for the step
        signature; nothing is patched."""
        self.comp.break_picture()

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
        assert self.entry_screen(ctx).glance_line is None, (
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
        assert self.entry_screen(ctx).neutral_glance_element, (
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

    def assert_matches_graph_line_end(self, ctx: SimpleNamespace) -> None:
        """Single-source AC (journey step 1<->3): glanced value == the graph line's END."""
        line_end_kg = self.comp.served_series()[-1].trend_kg
        self.assert_value_fragment(ctx, f"{line_end_kg:.1f} kg")

    def assert_rate_is_trailing_week_change(self, ctx: SimpleNamespace) -> None:
        """RTS co-revision oracle: the CURRENT pair coheres -- displayed rate == the
        displayed line's own trailing-7-day net change (never prior renderings)."""
        series = self.comp.served_series()
        self.assert_rate_fragment(ctx, rate_text(series[-1].trend_kg - series[-8].trend_kg))

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
