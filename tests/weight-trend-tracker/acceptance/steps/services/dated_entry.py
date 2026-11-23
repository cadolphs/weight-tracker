"""The date row, the whole-record map, and write-time save classification
(US-013 + US-014, ADR-010 + ADR-011)."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from typing import Any

from domain_types import day_label
from oracles import series_by_day
from pages import EntryScreen
from state_delta import assert_state_delta, set_to, unchanged

from services._base import REPAIR_COUNT_KEY, Service
from weight_tracker.core.trend import trend_series
from weight_tracker.core.types import Entry

#: Trail-only universe (Mandate 8) for the KPI-1 purity promise (A23/ADR-011).
#: The record's own delta is the co-located "holds exactly one entry" step's
#: promise, declared over UNIVERSE there; these scenarios promise what a save
#: does to the TRAIL, fail-closed.
PURITY_UNIVERSE = {
    "telemetry.entry_logged_count",
    "telemetry.speed_sample_count",
    "telemetry.repair_count",
}


class DatedEntryService(Service):
    """DELIVER-facing HTTP contract (executable spec):
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

    def _date_row(self, ctx: SimpleNamespace) -> EntryScreen:
        screen = self.entry_screen(ctx)
        assert screen.date_row is not None, (
            "the entry screen must offer a date row (a native #entry-date input) "
            "so a past day can be repaired where the habit lives"
        )
        return screen

    def assert_row_above_field(self, ctx: SimpleNamespace) -> None:
        screen = self._date_row(ctx)
        assert screen.date_row_native, (
            f"the date row must be the phone's OWN picker -- a native date input (D6), "
            f"got {screen.date_row}"
        )
        assert screen.form_at is not None and screen.weight_field_at is not None, (
            "the entry screen must carry the entry form and its weight field"
        )
        assert screen.form_at < screen.date_row_at < screen.weight_field_at, (
            "the date row belongs inside the entry form, above the weight field (D6)"
        )

    def assert_no_focus_theft(self, ctx: SimpleNamespace) -> None:
        assert "autofocus" not in self._date_row(ctx).date_row, (
            "the date row must never take the morning focus -- the keypad comes up "
            "on the weight field, as it always did (D6/D-25)"
        )
        self.comp.home_graph.assert_no_focus_theft(ctx)

    def assert_reaches_back_to(self, ctx: SimpleNamespace, day: date) -> None:
        screen = self._date_row(ctx)
        assert screen.date_row_earliest == day.isoformat(), (
            f"a mistyped year would stretch every recompute for good: the date row's "
            f"earliest day must be {day} (the record's first day minus a year, OQ-11), "
            f"row: {screen.date_row}"
        )

    # -- the map that answers ANY stored day (ADR-010) --------------------------

    def _offered(self, ctx: SimpleNamespace) -> dict[str, float]:
        weights = self.entry_screen(ctx).record_weights
        assert weights is not None, (
            "the entry screen must hand the phone the record's day-to-weight map -- "
            "ONE map answering both the yesterday anchor and the edit prefill (ADR-010)"
        )
        return weights

    def assert_offers(self, ctx: SimpleNamespace, day: date, kg: float) -> None:
        offered = self._offered(ctx).get(day.isoformat())
        assert offered == kg, (
            f"picking {day} must offer its stored {kg:.1f} kg back for correction -- "
            f"any stored day, however old (A24) -- but the screen offers {offered}"
        )

    def assert_offers_whole_record(self, ctx: SimpleNamespace) -> None:
        offered, stored = self._offered(ctx), self.comp.stored_weights()
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
        screen = self.entry_screen(ctx)
        assert screen.hint_node_count == 1, (
            f"ONE hint line serves the anchor, the editing hint and the no-entry hint: "
            f"'never two at once' is structural, but the screen carries "
            f"{screen.hint_node_count}"
        )
        assert not screen.retired_anchor_present, (
            "the anchor's old node is absorbed INTO the one hint line, never kept beside it"
        )

    def assert_hint_speaks_record_grammar(self, ctx: SimpleNamespace) -> None:
        """The hint names its day in the ONE grammar the record already speaks:
        the label the phone renders must equal the day half of the server's own
        row for that day -- no second calendar wording (D-24, Mandate-12)."""
        stored = self.comp.stored_weights()
        assert stored, "the grammar check needs at least one stored day"
        newest = date.fromisoformat(max(stored))
        table = self.entry_screen(ctx).recent
        assert table, "the grammar check reads the record's own rendered row"
        rendered = table.rows
        assert rendered and rendered[0].day == day_label(newest), (
            f"the hint must name its day in the record's own grammar ({day_label(newest)!r}), "
            f"but the record renders {rendered[0].day if rendered else None!r}"
        )

    # -- write-time classification (ADR-011): the trail --------------------------

    def capture_trail(self) -> dict[str, Any]:
        """Snapshot of what a save may move on the trail. Deliberately TOLERANT of a
        missing KPI-8 counter (None) so a scenario fails at its OWN first missing
        thing rather than at the capture -- the repair-count assertions below
        demand the counter explicitly."""
        stats = self.comp.served_stats()
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
        rows = [
            f"{day_label(date.fromisoformat(e['date']))} — {e['weight_kg']:.1f} kg" for e in recent
        ]
        assert rows.count(row_text) == 1, (
            f"the repaired day must stand exactly ONCE in the refreshed picture "
            f"(one entry per day), expected {row_text!r} among {rows}"
        )
        assert "glance" in body, "the repair's response carries the recomputed glance beside it"

    def assert_trend_reflects(self, day: date) -> None:
        """The trend recomputes over the repaired record: the served line equals the
        shipped pure series over the CURRENT entry set, and covers the repaired day."""
        entries = sorted(self.comp.stored_entries(), key=lambda entry: entry.day)
        entries = [Entry(day=entry.day, weight_kg=entry.weight_kg) for entry in entries]
        expected = {day: round(kg, 9) for day, kg in series_by_day(trend_series(entries)).items()}
        shown = {day: round(kg, 9) for day, kg in series_by_day(self.comp.served_series()).items()}
        assert shown == expected, (
            "after a repair the trend must be recomputed over the whole repaired record "
            f"({len(expected)} days expected, {len(shown)} served)"
        )
        assert day in shown, (
            f"the repaired day {day} must be part of the trend the record now tells"
        )
