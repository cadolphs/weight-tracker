"""The trail's shell: one write entry point, one read, over the real events table.

WHY-NEW-FILE: tests/weight-trend-tracker/integration/test_trail_adapter.py
  CLOSEST-EXISTING: tests/weight-trend-tracker/integration/test_repair_count_query.py
  EXTENSION-COST: that file is a Hypothesis property over the KPI-8 read model
    with a generated-trail fixture; the shell's contract here is example-shaped
    (one stamp, one row, one parse) and would dilute its `@settings` budget.
  PARALLEL-RATIONALE: this file pins the SEAM (ADR-015) -- `Trail` over a
    `TrailPort` adapter and a clock -- not a KPI derivation. The derivations are
    properties in `properties/test_trail_report_properties.py`.

Contract (ADR-015):
- `Trail.mark(name, payload)` stamps the event ONCE from the clock, with the
  name's on-trail spelling and the payload as compact JSON -- the exact bytes the
  routes used to write by hand, so historical and new rows are indistinguishable.
- `SqliteEntryStore.all_events()` reads every row back, parsed, in append order.
- `Trail.report()` is `kpi_report` over that read, framed by the clock's UTC day.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fake_clock import FakeClock

from weight_tracker.core.trail import Event, EventName, kpi_report
from weight_tracker.shell.entry_store import SqliteEntryStore
from weight_tracker.shell.trail import Trail

pytestmark = [pytest.mark.real_io, pytest.mark.adapter_integration, pytest.mark.kpi]


@pytest.fixture
def store(tmp_path: Path) -> SqliteEntryStore:
    opened = SqliteEntryStore(tmp_path / "weight.db")
    opened.apply_migrations()
    return opened


def _rows(store: SqliteEntryStore) -> list[tuple[str, str, str]]:
    with closing(sqlite3.connect(store._db_path)) as connection:
        return connection.execute("SELECT ts, name, payload FROM events ORDER BY id").fetchall()


def test_a_mark_is_one_row_stamped_once_from_the_clock(store: SqliteEntryStore) -> None:
    clock = FakeClock(datetime(2026, 7, 24, 6, 45, 12, tzinfo=UTC))
    trail = Trail(store=store, clock=clock)

    trail.mark(EventName.ENTRY_SAVED, {"date": "2026-07-24", "entry_ms": 4200, "backdated": False})

    assert _rows(store) == [
        (
            "2026-07-24T06:45:12+00:00",
            "entry.saved",
            json.dumps({"date": "2026-07-24", "entry_ms": 4200, "backdated": False}),
        )
    ]


def test_a_mark_without_a_payload_writes_the_empty_object(store: SqliteEntryStore) -> None:
    trail = Trail(store=store, clock=FakeClock())

    trail.mark(EventName.HOME_GRAPH_SHOWN)

    assert [(name, payload) for _, name, payload in _rows(store)] == [("home.graph.shown", "{}")]


def test_every_row_reads_back_parsed_in_append_order(store: SqliteEntryStore) -> None:
    store.append_event(ts="2026-07-20T08:30:00+00:00", name="trend.view.opened", payload="{}")
    store.append_event(
        ts="2026-07-21T06:45:00+00:00",
        name="entry.saved",
        payload='{"date": "2026-07-21", "entry_ms": null, "backdated": true}',
    )

    assert store.all_events() == [
        Event(ts=datetime(2026, 7, 20, 8, 30, tzinfo=UTC), name="trend.view.opened", payload={}),
        Event(
            ts=datetime(2026, 7, 21, 6, 45, tzinfo=UTC),
            name="entry.saved",
            payload={"date": "2026-07-21", "entry_ms": None, "backdated": True},
        ),
    ]


def test_a_mark_reads_back_as_the_event_it_stamped(store: SqliteEntryStore) -> None:
    clock = FakeClock(datetime(2026, 7, 24, 6, 45, tzinfo=UTC))
    trail = Trail(store=store, clock=clock)

    trail.mark(
        EventName.TREND_STUDY_INTERACTION, {"surface": "home", "control": "lens", "value": "raw"}
    )

    assert store.all_events() == [
        Event(
            ts=clock.now_utc(),
            name="trend.study.interaction",
            payload={"surface": "home", "control": "lens", "value": "raw"},
        )
    ]


def test_the_report_is_the_pure_derivation_framed_by_the_clocks_day(
    store: SqliteEntryStore,
) -> None:
    clock = FakeClock(datetime(2026, 7, 24, 6, 45, tzinfo=UTC))
    trail = Trail(store=store, clock=clock)
    for days_ago in (0, 3, 6, 7, 30):
        stamped = clock.now_utc() - timedelta(days=days_ago)
        store.append_event(ts=stamped.isoformat(), name="home.graph.shown", payload="{}")
        store.append_event(ts=stamped.isoformat(), name="entry.saved", payload='{"entry_ms": 4000}')

    report = trail.report()

    assert report == kpi_report(store.all_events(), today=clock.today())
    assert report["home_graph_shown_this_week"] == 3  # today, -3, -6; -7 and -30 aged out
    assert report["entry_logged_count"] == 5  # all-time: nothing ages out
    assert report["speed"]["sample_count"] == 3


def test_the_report_reads_the_trail_and_moves_nothing(store: SqliteEntryStore) -> None:
    trail = Trail(store=store, clock=FakeClock())
    store.append_event(ts="2026-07-21T06:45:00+00:00", name="entry.saved", payload="{}")
    before = _rows(store)

    trail.report()

    assert _rows(store) == before
