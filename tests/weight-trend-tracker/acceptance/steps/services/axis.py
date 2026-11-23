"""US-015: the visible y-axis is an honest projection of what is plotted (ADR-012)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

from domain_types import AxisBand, TimeScale, ViewMode
from driver import UNIVERSE
from oracles import honest_band
from pages import HistoryPage, read_history_page
from state_delta import assert_state_delta, unchanged

from services._base import Service
from weight_tracker.core.axis import FLOOR_KG, GRID_KG
from weight_tracker.core.trend import trend_series, windowed_series
from weight_tracker.core.types import entries_in_window

#: Sentinel: the read carried no `y_range` key at all (pre-feature response).
NO_AXIS_KEY = object()


@dataclass(frozen=True)
class AxisReading:
    """One lens at one scale, as the chart engine reads it: the values it plots,
    whatever axis the read offered, and the page whose taps chose the view."""

    lens: ViewMode
    scale: TimeScale
    values: tuple[float, ...]
    offered: Any  # NO_AXIS_KEY | None | the wire pair
    response: Any
    page: HistoryPage | None

    @property
    def label(self) -> str:
        return f"the {self.lens.value} lens at {self.scale.value}"


class AxisService(Service):
    """Universe = the two series reads (`/entries`, `/trend`) as the shared engine
    fetches them for BOTH surfaces (parity by construction, ADR-008): the plotted
    values + the offered `y_range`. Reads are pure; every view/tour additionally
    guards the shared universe (record + frozen counters) as unchanged (Mandate 8).

    Oracle: the shipped `y_axis_range` (via `oracles.honest_band`) says what the
    honest axis IS; the floor, containment, grid, width, centre and line-share
    assertions say what the feature files promised, independently of it.
    """

    def _read(
        self, lens: ViewMode, scale: TimeScale, page: HistoryPage | None = None
    ) -> AxisReading:
        if lens is ViewMode.TREND:
            response = self.comp.actor().get("/trend", params={"scale": scale.value})
            assert response.status_code == 200, f"the trend did not answer: {response.status_code}"
            values = tuple(point["trend_kg"] for point in response.json()["points"])
        else:
            response = self.comp.actor().get("/entries", params={"scale": scale.value})
            assert response.status_code == 200, f"the record did not answer: {response.status_code}"
            values = tuple(entry["weight_kg"] for entry in response.json()["entries"])
        offered = response.json().get("y_range", NO_AXIS_KEY)
        return AxisReading(lens, scale, values, offered, response, page)

    def _open_page(self, lens: ViewMode, scale: TimeScale) -> HistoryPage:
        page = self.comp.actor().get("/graph", params={"view": lens.value, "scale": scale.value})
        assert page.status_code == 200, f"the graph page did not open: {page.status_code}"
        return read_history_page(page)

    def _guard_reads_are_pure(self, before: dict[str, Any]) -> None:
        assert_state_delta(
            before,
            self.comp.capture_universe(),
            universe=UNIVERSE,
            expected={name: unchanged() for name in UNIVERSE},
        )

    # -- When -------------------------------------------------------------------

    def view(self, lens: ViewMode, scale: TimeScale, ctx: SimpleNamespace) -> None:
        """A lens/scale tap on the History page, then the read the engine performs."""
        before = self.comp.capture_universe()
        reading = self._read(lens, scale, self._open_page(lens, scale))
        ctx.axis, ctx.response = reading, reading.response
        if lens is ViewMode.TREND:
            ctx.trend_scale = scale
            ctx.trend = [(p["date"], p["trend_kg"]) for p in reading.response.json()["points"]]
        self._guard_reads_are_pure(before)

    def tour(self, ctx: SimpleNamespace) -> None:
        """Every lens at every scale -- the closed 2 x 6 world, enumerated (falsifier-gate)."""
        before = self.comp.capture_universe()
        ctx.tour = tuple(
            self._read(lens, scale, self._open_page(lens, scale))
            for lens in ViewMode
            for scale in TimeScale
        )
        self._guard_reads_are_pure(before)

    # -- Then -------------------------------------------------------------------

    def _band(self, reading: AxisReading) -> AxisBand:
        assert reading.offered is not NO_AXIS_KEY, (
            f"no axis is offered for {reading.label}: the read carries no `y_range`"
        )
        assert reading.offered is not None, (
            f"{reading.label} plots {len(reading.values)} values but offers no axis (null)"
        )
        pair = reading.offered
        assert (
            isinstance(pair, list)
            and len(pair) == 2
            and all(isinstance(b, int | float) and math.isfinite(b) for b in pair)
            and pair[0] < pair[1]
        ), f"{reading.label} offers a garbled axis {pair!r}; expected [lo, hi] with lo < hi"
        return AxisBand(lo_kg=float(pair[0]), hi_kg=float(pair[1]))

    def _assert_honest(self, reading: AxisReading) -> None:
        band = self._band(reading)
        assert band.width_kg >= FLOOR_KG - 1e-9, (
            f"{reading.label}: axis {band.lo_kg}..{band.hi_kg} is only {band.width_kg} kg tall"
        )
        outside = [v for v in reading.values if not band.contains(v)]
        assert not outside, f"{reading.label}: plotted values fall outside the axis: {outside}"
        assert band.on_grid(GRID_KG), (
            f"{reading.label}: bounds {band.lo_kg}..{band.hi_kg} are not on the half-kilogram grid"
        )
        assert band == honest_band(reading.values), (
            f"{reading.label}: axis {band.lo_kg}..{band.hi_kg} is not the honest range "
            f"{honest_band(reading.values)} for values spanning "
            f"{min(reading.values)}..{max(reading.values)}"
        )

    def assert_band(self, ctx: SimpleNamespace, lo_kg: float, hi_kg: float) -> None:
        band = self._band(ctx.axis)
        assert band == AxisBand(lo_kg, hi_kg), (
            f"{ctx.axis.label}: axis runs {band.lo_kg}..{band.hi_kg}, expected {lo_kg}..{hi_kg}"
        )

    def assert_honest(self, ctx: SimpleNamespace) -> None:
        self._assert_honest(ctx.axis)

    def assert_floor_and_containment(self, ctx: SimpleNamespace) -> None:
        band = self._band(ctx.axis)
        assert band.width_kg >= FLOOR_KG - 1e-9, f"axis is only {band.width_kg} kg tall"
        outside = [v for v in ctx.axis.values if not band.contains(v)]
        assert not outside, f"plotted values fall outside the axis: {outside}"

    def _line_share(self, ctx: SimpleNamespace) -> float:
        band = self._band(ctx.axis)
        return (max(ctx.axis.values) - min(ctx.axis.values)) / band.width_kg

    def assert_line_share_at_most(self, ctx: SimpleNamespace, percent: int) -> None:
        share = self._line_share(ctx)
        assert share <= percent / 100 + 1e-9, (
            f"the plotted line fills {share:.0%} of the axis; a stalled window may fill "
            f"at most {percent}%"
        )

    def assert_line_share_at_least(self, ctx: SimpleNamespace, percent: int) -> None:
        share = self._line_share(ctx)
        assert share >= percent / 100 - 1e-9, (
            f"the plotted line fills only {share:.0%} of the axis; a real loss must cover "
            f"at least {percent}%"
        )

    def assert_width_between(self, ctx: SimpleNamespace, lo_w: float, hi_w: float) -> None:
        band = self._band(ctx.axis)
        assert lo_w - 1e-9 <= band.width_kg <= hi_w + 1e-9, (
            f"axis is {band.width_kg} kg tall; a floored band is {lo_w}..{hi_w} kg"
        )

    def assert_centre_within(self, ctx: SimpleNamespace, tolerance_kg: float) -> None:
        band = self._band(ctx.axis)
        mid = (min(ctx.axis.values) + max(ctx.axis.values)) / 2
        assert abs(band.centre_kg - mid) <= tolerance_kg + 1e-9, (
            f"axis centre {band.centre_kg} sits {abs(band.centre_kg - mid):.3f} kg from the "
            f"data midpoint {mid:.3f}; allowed {tolerance_kg}"
        )

    def assert_auto_branch(self, ctx: SimpleNamespace) -> None:
        """At or above the floor: the padded range snapped outward -- and nothing else.
        A padded range is at least 1.2 x span wide, so any band that is exactly the
        floor tall was widened by the floor branch, not padded (the independent half
        of this claim)."""
        values = ctx.axis.values
        span = max(values) - min(values)
        assert span >= FLOOR_KG, (
            f"this window moves only {span:.3f} kg; the ordinary range applies from "
            f"{FLOOR_KG} kg of movement (seed shape error, not a product defect)"
        )
        band = self._band(ctx.axis)
        assert band.width_kg > FLOOR_KG + 1e-9, (
            f"axis runs {band.lo_kg}..{band.hi_kg}, exactly the floor tall: a window moving "
            f"{span:.3f} kg takes the ordinary padded range, never the floor widening"
        )
        assert band == honest_band(values), (
            f"axis runs {band.lo_kg}..{band.hi_kg}; the ordinary range padded by a tenth "
            f"and snapped outward is {honest_band(values)} (no floor widening)"
        )

    def assert_clean_bounds(self, ctx: SimpleNamespace) -> None:
        band = self._band(ctx.axis)
        for bound in (band.lo_kg, band.hi_kg):
            assert float(bound * 2).is_integer(), f"bound {bound!r} is not a multiple of 0.5 kg"
            assert round(bound, 1) == bound, f"bound {bound!r} carries more than one decimal"

    def assert_exact_width_centred(
        self, ctx: SimpleNamespace, width_kg: float, centre_kg: float
    ) -> None:
        band = self._band(ctx.axis)
        assert abs(band.width_kg - width_kg) < 1e-9 and abs(band.centre_kg - centre_kg) < 1e-9, (
            f"axis runs {band.lo_kg}..{band.hi_kg}; expected exactly {width_kg} kg tall "
            f"centred on {centre_kg}"
        )

    def _assert_none(self, reading: AxisReading) -> None:
        assert reading.offered is not NO_AXIS_KEY, (
            f"{reading.label}: the read carries no `y_range` at all -- an empty window must "
            f"answer null, explicitly"
        )
        assert reading.offered is None, (
            f"{reading.label} plots nothing yet offers an axis {reading.offered!r}"
        )

    def assert_none_either_lens(self, scale: TimeScale) -> None:
        for lens in ViewMode:
            reading = self._read(lens, scale)
            assert not reading.values, f"{reading.label} unexpectedly plots {reading.values}"
            self._assert_none(reading)

    def assert_tour_honest(self, ctx: SimpleNamespace) -> None:
        for reading in ctx.tour:
            self._assert_honest(reading)
        spans = [max(r.values) - min(r.values) for r in ctx.tour if r.values]
        assert min(spans) < FLOOR_KG <= max(spans), (
            "the tour must cross the floor -- some windows stalled, some moving -- "
            f"or it proves only one branch (spans {min(spans):.2f}..{max(spans):.2f})"
        )

    def assert_tour_keeps_selection(self, ctx: SimpleNamespace) -> None:
        for reading in ctx.tour:
            assert reading.page is not None, f"{reading.label}: the tour opens the page first"
            assert reading.page.view == reading.lens.value, (
                f"{reading.label}: the lens did not survive the tap"
            )
            assert reading.page.scale == reading.scale.value, (
                f"{reading.label}: the scale did not survive the tap"
            )

    def assert_series_untouched(self, ctx: SimpleNamespace) -> None:
        """The plotted values are exactly the shipped pure series (G-3): the axis frames
        the line, it never moves it."""
        reading, today = ctx.axis, self.comp.today()
        stored = self.comp.stored_entries()
        if reading.lens is ViewMode.TREND:
            expected = [
                round(p.trend_kg, 9)
                for p in windowed_series(trend_series(stored), reading.scale, today)
            ]
        else:
            expected = [e.weight_kg for e in entries_in_window(stored, reading.scale, today)]
        assert [round(v, 9) for v in reading.values] == expected, (
            f"{reading.label}: the plotted values differ from the line the record has always "
            f"told ({len(expected)} expected, {len(reading.values)} served)"
        )
