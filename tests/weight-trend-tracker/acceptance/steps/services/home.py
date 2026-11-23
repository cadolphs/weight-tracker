"""Graph-first home (US-010/011/012, ADR-008/009) and the trend column on both
entries lists (US-016, ADR-013): the front-page graph, the recent list, the
complete record on the History page, the trend rows, and intent telemetry."""

from __future__ import annotations

from datetime import date, timedelta
from types import SimpleNamespace
from typing import Any

from domain_types import TimeScale, ViewMode, day_label, parse_scale
from oracles import expected_rows, series_by_day
from pages import COLUMN_HEADINGS, EntriesTable, Row

from services._base import AMBIENT_COUNT_KEY, STUDY_COUNT_KEY, Service, timed

BEACON_PATH = "/telemetry/trend-study"
ALL_SCALE_WINDOWS = ("1W", "1M", "3M", "6M", "1Y", "ALL")


class HomeGraphService(Service):
    """Front-page ambient graph (US-010, ADR-008): served mount + full controls +
    defaults, driven by the same shared engine and the same telemetry-free data
    reads as the History page. Client paint itself is structural (one extracted
    module, D-15) and verified at DELIVER dogfood -- the glance/theme precedent."""

    def _today_iso(self) -> str:
        return self.comp.today().isoformat()

    def _ambient_points(self) -> list[dict[str, Any]]:
        resp = self.comp.observer().get(
            "/trend", params={"scale": TimeScale.THREE_MONTHS.value, "today": self._today_iso()}
        )
        assert resp.status_code == 200, f"the morning series read failed: {resp.status_code}"
        return resp.json()["points"]

    # -- served shape ---------------------------------------------------------

    def assert_curve_above_form(self, ctx: SimpleNamespace) -> None:
        screen = self.entry_screen(ctx)
        assert screen.home_graph_mount_at is not None, (
            "the front page must offer the trend graph (a #home-graph mount)"
        )
        assert screen.form_at is not None and screen.home_graph_mount_at < screen.form_at, (
            "the graph must sit ABOVE the entry form (D6/D7)"
        )

    def assert_full_controls(self, ctx: SimpleNamespace) -> None:
        screen = self.entry_screen(ctx)
        for lens in ("trend", "raw"):
            assert lens in screen.lens_controls, (
                f'the graph must offer the full lens toggle, missing data-lens="{lens}"'
            )
        missing = [w for w in ALL_SCALE_WINDOWS if w not in screen.window_controls]
        assert not missing, f"the scale picker must offer every window (D7), missing {missing}"

    def assert_opens_at_defaults(self, ctx: SimpleNamespace, scale: TimeScale) -> None:
        screen = self.entry_screen(ctx)
        assert screen.home_graph_mount, (
            "the front page must offer the trend graph (a #home-graph mount)"
        )
        assert (screen.mount_view, screen.mount_scale) == ("trend", scale.value), (
            f"the front-page graph must open at the ambient defaults (A17/D-20): "
            f'data-view="trend" data-scale="{scale.value}" on the mount, '
            f"got {screen.home_graph_mount}"
        )

    def assert_shared_engine(self, ctx: SimpleNamespace) -> None:
        history = SimpleNamespace(response=self.comp.graph.open())
        surfaces = {
            "front page": self.entry_screen(ctx).links_graph_module,
            "History page": self.history_page(history).links_graph_module,
        }
        missing = [name for name, linked in surfaces.items() if not linked]
        assert not missing, (
            f"both surfaces must drive the ONE shared graph module (ADR-008), missing on: {missing}"
        )
        served = self.comp.actor().get("/static/graph.js")
        assert served.status_code == 200, (
            f"the shared graph module must be delivered by the tracker itself, "
            f"got {served.status_code}"
        )

    def assert_absent(self, ctx: SimpleNamespace) -> None:
        assert self.entry_screen(ctx).home_graph_mount is None, (
            "an empty record must keep the front page simple -- no graph area (A18 kin)"
        )

    def assert_no_focus_theft(self, ctx: SimpleNamespace) -> None:
        screen = self.entry_screen(ctx)
        assert screen.autofocus_count == 1, (
            "exactly one autofocus belongs on the morning screen: the weight field (Q4)"
        )
        assert screen.weight_field and "autofocus" in screen.weight_field, (
            "the weight field must keep the morning focus (D6: keypad-cover accepted, "
            "focus theft is not)"
        )
        assert not screen.has_tabindex, "no element may reorder the morning focus (Q4)"

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
        (absent area client-side) while entry, save, and confirmation are untouched.
        The series lives in the picture (ADR-014); nothing is patched."""
        self.comp.break_picture()

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


class RecentListService(Service):
    """Last-7 entries list (US-011, A18/D9): server-rendered, display-only,
    entries not days, gaps simply absent; refreshed on the save response (D-19)."""

    def table(self, ctx: SimpleNamespace) -> EntriesTable:
        table = self.entry_screen(ctx).recent
        assert table is not None, (
            "the front page must carry the recent-entries list (#recent-entries)"
        )
        return table

    def rows(self, ctx: SimpleNamespace) -> list[Row]:
        return list(self.table(ctx).rows)

    def _stored_rows(self, limit: int = 7) -> list[Row]:
        smoothed = series_by_day(self.comp.served_series())
        return expected_rows(self.comp.stored_entries()[:limit], smoothed)

    def assert_last_seven(self, ctx: SimpleNamespace) -> None:
        rows = self.rows(ctx)
        expected = self._stored_rows()
        assert rows == expected, (
            f"the recent list must show the last 7 ENTRIES newest first (A18), "
            f"expected {expected}, shown {rows}"
        )

    def assert_begins_with(self, ctx: SimpleNamespace, text: str) -> None:
        """`text` names the row by its DAY and RAW weight ("Fri 24 Jul — 82.2 kg"),
        the wording the feature files have always used; the trend column is pinned
        by its own scenarios (US-016), not smuggled into every other one."""
        rows = self.rows(ctx)
        shown = f"{rows[0].day} — {rows[0].raw} kg" if rows else "nothing"
        assert rows and shown == text, (
            f"the recent list must begin with {text!r}, it begins with {shown!r}"
        )

    def screen_begins_with(self, ctx: SimpleNamespace, text: str) -> None:
        probe = SimpleNamespace(response=self.comp.screen.open_entry())
        self.assert_begins_with(probe, text)

    def assert_day_absent(self, ctx: SimpleNamespace, day: date) -> None:
        rows = self.rows(ctx)
        marker = day_label(day)
        offenders = [row for row in rows if row.day == marker or "0.0" in (row.raw, row.trend)]
        assert not offenders, (
            f"a missed day must be simply absent -- no zero, no placeholder (A18), "
            f"but the list carries {offenders}"
        )

    def assert_exactly(self, ctx: SimpleNamespace, count: int) -> None:
        rows = self.rows(ctx)
        expected = self._stored_rows(limit=count)
        assert rows == expected and len(rows) == count, (
            f"a young record must show exactly its {count} entries, shown {rows}"
        )

    def assert_none(self, ctx: SimpleNamespace) -> None:
        assert self.entry_screen(ctx).recent is None, (
            "an empty record must show no recent list at all (A18)"
        )

    def assert_display_only(self, ctx: SimpleNamespace) -> None:
        touched = self.table(ctx).touch_affordance
        assert touched is None, (
            f"looking is not touching (D9): the recent list must offer no affordances, "
            f"found <{touched}>"
        )

    def assert_values_match_store(self, ctx: SimpleNamespace) -> None:
        rows = self.rows(ctx)
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


class HistoryRecordService(Service):
    """Complete record on the History page (US-012, D-17): server-rendered from
    the same all-entries read the raw plot draws, ALWAYS the whole record
    regardless of the chart's window; /graph behaviors preserved (A16)."""

    def open_timed(self, ctx: SimpleNamespace) -> Any:
        return timed(ctx, lambda: self.comp.actor().get("/graph"))

    def table(self, ctx: SimpleNamespace) -> EntriesTable:
        table = self.history_page(ctx).record
        assert table is not None, (
            "the History page must carry the complete record (#history-entries)"
        )
        return table

    def rows(self, ctx: SimpleNamespace) -> list[Row]:
        return list(self.table(ctx).rows)

    def _all_stored_rows(self) -> list[Row]:
        smoothed = series_by_day(self.comp.served_series())
        return expected_rows(self.comp.stored_entries(), smoothed)

    def assert_complete_newest_first(self, ctx: SimpleNamespace) -> None:
        rows = self.rows(ctx)
        expected = self._all_stored_rows()
        assert rows == expected, (
            f"the complete record must list every stored entry newest first "
            f"({len(expected)} entries), the page lists {len(rows)}"
        )
        page = self.history_page(ctx)
        assert page.chart_at is not None and page.record_at is not None, (
            "the History page must carry both the chart and the complete record"
        )
        assert page.chart_at < page.record_at, "the complete record belongs BENEATH the graph (D8)"

    def assert_days_absent(self, ctx: SimpleNamespace, start: date, end: date) -> None:
        rows = self.rows(ctx)
        gap_days = [start + timedelta(days=offset) for offset in range((end - start).days + 1)]
        offenders = [row for row in rows for day in gap_days if row.day == day_label(day)]
        assert not offenders, (
            f"days without an entry must be absent from the list exactly as they are "
            f"gaps in the plot, but the list carries {offenders}"
        )

    def assert_matches_raw_plot(self, ctx: SimpleNamespace) -> None:
        rows = self.rows(ctx)
        plotted = self._all_stored_rows()  # the raw plot draws from the same /entries read
        assert rows == plotted, (
            f"the list and the plot must tell the same story (single source, D-18): "
            f"list {len(rows)} rows vs stored {len(plotted)} entries"
        )

    def assert_back_link(self, ctx: SimpleNamespace) -> None:
        assert self.history_page(ctx).back_link, (
            "the way back to today's entry must stay one tap away (A16)"
        )

    def assert_invite_offered(self, ctx: SimpleNamespace) -> None:
        assert self.history_page(ctx).invite, (
            "an empty record must still offer the first-log invite (A16)"
        )

    def assert_none(self, ctx: SimpleNamespace) -> None:
        assert self.history_page(ctx).record is None, (
            "an empty record renders no list -- only the first-log invite (A16)"
        )

    def assert_ready_within(self, ctx: SimpleNamespace, budget_ms: int) -> None:
        assert ctx.response.status_code == 200
        assert ctx.elapsed_ms <= budget_ms, (
            f"the History page took {ctx.elapsed_ms:.0f} ms with the complete record, "
            f"budget {budget_ms} ms (G-2 extended)"
        )


class TrendRowsService(Service):
    """The trend column on both entries lists (US-016, ADR-013).

    DELIVER-facing contract (executable spec):
        GET  /        -> the recent list is a <table id="recent-entries"> with a
                         <th scope="col"> header row (Date / Raw (kg) / Trend (kg))
                         and one <tr> of three <td> per ENTRY, newest first, both
                         weights at 0.1 kg.
        GET  /graph   -> the same table on id="history-entries", the WHOLE record,
                         never windowed by the chart's selected scale (D-17).
        POST /entries -> each `recent` pair gains `"trend_kg": <float> | null`
                         (key always present) for the in-place repaint (D-37).
        GET  /entries -> BYTE-IDENTICAL to pre-feature: the raw lens's read carries
                         no trend (D-37); the trend lens keeps its own /trend.

    Oracle: `GET /trend` at "ALL" -- the chart's own smoothed series, over the HTTP
    boundary. Reading the expectation from the series the chart plots is what makes
    A36 ("one value per day across the glance, both lists and the chart") a real
    claim: a second algorithm, a second rounding, or a windowed re-smoothing on
    either surface fails here rather than in a comment.
    """

    # -- oracle -------------------------------------------------------------------

    def series_by_day(self) -> dict[date, float]:
        """The smoothed series as {day: kg}, read from the chart's own endpoint."""
        return series_by_day(self.comp.served_series())

    def _expected_trend(self, day: date) -> str:
        smoothed = self.series_by_day()
        assert day in smoothed, (
            f"every entry day sits on the trend grid by construction (A32), but {day} "
            f"is missing from a series spanning {min(smoothed, default=None)}"
            f"..{max(smoothed, default=None)}"
        )
        return f"{smoothed[day]:.2f}"

    def _recent_rows(self, ctx: SimpleNamespace) -> list[Row]:
        return self.comp.recent_list.rows(ctx)

    def _complete_rows(self, ctx: SimpleNamespace) -> list[Row]:
        return self.comp.history_record.rows(ctx)

    def _rows_by_day(self, rows: list[Row]) -> dict[str, Row]:
        return {row.day: row for row in rows}

    def _stored_days(self, limit: int | None = None) -> list[date]:
        days = [entry.day for entry in self.comp.stored_entries()]
        return days if limit is None else days[:limit]

    # -- fault injection ----------------------------------------------------------

    def break_projection(self, monkeypatch: Any) -> None:
        """The day-keyed trend is one derivation inside the picture (ADR-014);
        a failing picture empties every trend cell. Nothing is patched."""
        self.comp.break_picture()

    # -- assertions ---------------------------------------------------------------

    def _assert_rows_complete(self, rows: list[Row], surface: str) -> None:
        assert rows, f"the {surface} must carry at least one row for a non-empty record"
        thin = [row for row in rows if not (row.day and row.raw and row.trend)]
        assert not thin, (
            f"every {surface} row carries a date, a raw weight AND a trend weight "
            f"(US-016), but these are incomplete: {thin}"
        )

    def assert_recent_rows_complete(self, ctx: SimpleNamespace) -> None:
        self._assert_rows_complete(self._recent_rows(ctx), "recent list")

    def assert_complete_rows_complete(self, ctx: SimpleNamespace) -> None:
        self._assert_rows_complete(self._complete_rows(ctx), "complete record")

    def _assert_matches_series(self, rows: list[Row], days: list[date], surface: str) -> None:
        smoothed = self.series_by_day()
        wrong = [
            (row.day, row.trend, f"{smoothed[day]:.2f}")
            for row, day in zip(rows, days, strict=True)
            if day in smoothed and row.trend != f"{smoothed[day]:.2f}"
        ]
        assert not wrong, (
            f"every {surface} trend value must be the smoothed series value for its own day "
            f"-- one series, one rounding (A36) -- but (day, shown, series) differ: {wrong}"
        )
        off_grid = [day for day in days if day not in smoothed]
        assert not off_grid, f"every entry day sits on the trend grid (A32), missing {off_grid}"

    def assert_recent_matches_series(self, ctx: SimpleNamespace) -> None:
        rows = self._recent_rows(ctx)
        self._assert_matches_series(rows, self._stored_days(limit=len(rows)), "recent list")

    def assert_complete_matches_series(self, ctx: SimpleNamespace) -> None:
        self._assert_matches_series(
            self._complete_rows(ctx), self._stored_days(), "complete record"
        )

    def assert_newest_row_matches_glance(self, ctx: SimpleNamespace) -> None:
        """ONE value, two precisions (A35/A36): the glance speaks the series end at
        0.1 kg and the newest row speaks the same day at 0.01 kg. Both are checked
        against the SERIES rather than against each other, so a re-rounding of an
        already-rounded number -- the way two precisions usually start to drift --
        cannot pass by looking self-consistent."""
        rows = self._recent_rows(ctx)
        glance = self.entry_screen(ctx).glance_line
        assert rows and glance is not None, (
            "the scenario needs both a recent list and a glance line"
        )
        newest = max(self._stored_days())
        smoothed = self.series_by_day()[newest]
        assert rows[0].day == day_label(newest), "the newest entry belongs on top of the list"
        assert rows[0].trend == f"{smoothed:.2f}", (
            f"the newest row must speak its day's series value at 0.01 kg "
            f"({smoothed:.2f}), it speaks {rows[0].trend!r}"
        )
        assert f"Trend: {smoothed:.1f} kg" in glance, (
            f"the glance must speak that SAME value at 0.1 kg (Trend: {smoothed:.1f} kg), "
            f"it speaks {glance!r}"
        )

    def assert_surfaces_agree(self, ctx: SimpleNamespace) -> None:
        newest = max(self._stored_days())
        front = self._rows_by_day(self._recent_rows(ctx))
        history = self._rows_by_day(
            self._complete_rows(SimpleNamespace(response=self.comp.graph.open()))
        )
        label = day_label(newest)
        assert label in front and label in history, (
            f"{label} must appear on both surfaces: front page {label in front}, "
            f"History page {label in history}"
        )
        assert front[label].trend == history[label].trend == self._expected_trend(newest), (
            f"one day, one trend value: front page {front[label].trend!r}, History page "
            f"{history[label].trend!r}, series {self._expected_trend(newest)!r}"
        )

    def assert_unwindowed(self, ctx: SimpleNamespace) -> None:
        """The complete record is the WHOLE record at every scale (D-17/A34): the
        chart windows, the list does not. The lens x scale world is closed and small,
        so it is enumerated rather than sampled."""
        baseline = self._complete_rows(ctx)
        for lens in (ViewMode.TREND, ViewMode.RAW):
            for window in ALL_SCALE_WINDOWS:
                shown = SimpleNamespace(response=self.comp.graph.open(lens, parse_scale(window)))
                assert self._complete_rows(shown) == baseline, (
                    f"the complete record must read identically at {lens.value}/{window} "
                    f"-- the chart windows, the record does not (D-17)"
                )

    def assert_no_half_rows(self, ctx: SimpleNamespace) -> None:
        rows = self._complete_rows(ctx)
        half = [row for row in rows if bool(row.raw) != bool(row.trend)]
        assert not half, (
            f"a rendered row carries both weights or the record has no row for that day "
            f"at all -- never half of one (A33), but found {half}"
        )

    def _handback(self, ctx: SimpleNamespace) -> list[dict[str, Any]]:
        recent = ctx.response.json().get("recent")
        assert recent, "the save must hand back the refreshed recent list (`recent`, D-19)"
        return recent

    def assert_handback_complete(self, ctx: SimpleNamespace) -> None:
        missing = [pair for pair in self._handback(ctx) if pair.get("trend_kg") is None]
        assert not missing, (
            f"the repaint needs a trend for every handed-back entry (D-37, key always "
            f"present and non-null on a healthy read), but these carry none: {missing}"
        )

    def assert_handback_matches_series(self, ctx: SimpleNamespace) -> None:
        smoothed = self.series_by_day()
        wrong = [
            (pair["date"], pair["trend_kg"], smoothed.get(date.fromisoformat(pair["date"])))
            for pair in self._handback(ctx)
            if round(pair["trend_kg"], 9) != round(smoothed[date.fromisoformat(pair["date"])], 9)
        ]
        assert not wrong, (
            f"the handed-back trend values are the RECOMPUTED series over the record "
            f"including the just-saved day (D11 retrospective revision), but "
            f"(day, handed back, series) differ: {wrong}"
        )

    def assert_raw_survives(self, ctx: SimpleNamespace) -> None:
        rows = self._recent_rows(ctx)
        assert rows, "a failing trend must not cost the raw record its list (A37)"
        thin = [row for row in rows if not (row.day and row.raw)]
        assert not thin, f"every row keeps its date and raw weight under degrade, missing: {thin}"

    def assert_trend_blank(self, ctx: SimpleNamespace) -> None:
        rows = self._recent_rows(ctx)
        spoken = [row for row in rows if row.trend != ""]
        assert not spoken, (
            f"a failing trend renders EMPTY cells -- never a zero, a stale value, or a "
            f"copy of the raw weight (D12/A37) -- but these speak: {spoken}"
        )

    def assert_one_grammar(self, ctx: SimpleNamespace) -> None:
        recent = self._recent_rows(ctx)
        complete = self._complete_rows(SimpleNamespace(response=self.comp.graph.open()))
        assert recent == complete[: len(recent)], (
            f"one row definition serves both surfaces (D7/D-35): the recent list must be "
            f"the newest rows of the complete record, got {recent} vs {complete[: len(recent)]}"
        )

    def _assert_headers(self, table: EntriesTable | None, surface: str) -> None:
        assert table is not None, f"the {surface} must be rendered as a table"
        assert table.headings == COLUMN_HEADINGS, (
            f'the {surface} names its columns as real <th scope="col"> headers so a screen '
            f"reader announces each cell (D-38), expected {COLUMN_HEADINGS}, got {table.headings}"
        )

    def assert_recent_headers(self, ctx: SimpleNamespace) -> None:
        self._assert_headers(self.entry_screen(ctx).recent, "recent list")

    def assert_complete_headers(self, ctx: SimpleNamespace) -> None:
        self._assert_headers(self.history_page(ctx).record, "complete record")


class StudyService(Service):
    """Intent telemetry (ADR-009): deliberate study = History-page opens +
    explicit lens/scale taps (the beacon, closed vocabulary); ambient = home
    graph deliveries. KPI-3 purity is asserted on the /stats read surface."""

    def deliberate_count(self) -> int:
        count = self.comp.served_stats().get(STUDY_COUNT_KEY)
        assert count is not None, (
            f"/stats must serve {STUDY_COUNT_KEY} -- KPI-3's new home (ADR-009)"
        )
        return count

    def trail_counts(self) -> dict[str, Any]:
        body = self.comp.served_stats()
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
        ctx.study_before = self.comp.served_stats().get(STUDY_COUNT_KEY) or 0
        self.tap("home", "scale", window)
        self.tap("home", "lens", "raw")

    def send_garbled(self, ctx: SimpleNamespace) -> None:
        ctx.trail_before = self.trail_counts()
        ctx.beacon_response = self.comp.actor().post(
            BEACON_PATH, json={"surface": "kitchen", "control": "mood", "value": "loud"}
        )

    def stranger_taps(self, ctx: SimpleNamespace) -> None:
        ctx.trail_before = self.trail_counts()
        ctx.beacon_response = self.comp.stranger().post(
            BEACON_PATH, json={"surface": "home", "control": "scale", "value": "1Y"}
        )

    # -- outcome assertions ---------------------------------------------------

    def assert_deliberate(self, expected: int) -> None:
        count = self.deliberate_count()
        assert count == expected, (
            f"the deliberate trend-study count must read {expected} (A19), /stats reads {count}"
        )

    def assert_ambient_delivery(self) -> None:
        count = self.comp.served_stats().get(AMBIENT_COUNT_KEY)
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
