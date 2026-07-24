"""The KPI-8 read model: in-app repairs counted off the shared event trail.

WHY-NEW-FILE: tests/weight-trend-tracker/integration/test_repair_count_query.py
  CLOSEST-EXISTING: tests/weight-trend-tracker/integration/test_schema_version_guard.py
  EXTENSION-COST: that file's contract is the startup migration/probe boundary --
    it builds the whole app to assert refusal semantics, and has no trail-seeding
    surface a windowed read-model property could reuse.
  PARALLEL-RATIONALE: this file exercises a different driven surface (a read-model
    query function, not the store's startup lifecycle) and is the suite's only
    Hypothesis-driven file, so its `@settings` budget and generated-trail fixtures
    would otherwise leak into a single-example wiring guard.

Property-based (paradigm mandate): the predicate is an equivalence-class claim
over an arbitrary trail, not an example. Real SQLite through the production
`SqliteEntryStore` -- the events table lives in ONE place (DEVOPS Pre-Requisite 5),
so the query is proven against the same rows a save actually writes.

Contract (feature-delta.md D-23, ADR-011):
- A repair is an `entry.saved` event whose payload carries `backdated` true.
  D-23 keeps ONE event per save rather than forking the trail grammar, so the
  flag -- not a second event name -- is what KPI-8 reads.
- The window is the same rolling frame as every counter beside it: stamped on
  `since` or any later day.
- Reading is reading: the query moves nothing on the trail (universe fail-closed).
"""

from __future__ import annotations

import json
import sqlite3
import tempfile
from contextlib import closing
from datetime import date, timedelta
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from state_delta import assert_state_delta

from weight_tracker.shell.entry_store import SqliteEntryStore
from weight_tracker.shell.telemetry_store import backdated_saves_since
from weight_tracker.web.routes import ENTRY_SAVED_EVENT

WINDOW_START = date(2026, 7, 18)

#: Names that share the trail with saves -- a repair count must ignore all of them,
#: however their payloads are shaped (the flag alone never makes a repair).
OTHER_TRAIL_NAMES = ("trend.study.opened", "home.graph.shown", "trend.glance.shown")

#: One recorded event: (name, days from the window start, backdated flag, entry_ms).
#: `None` for the flag means the payload carries no `backdated` word at all -- the
#: shape every event written before this feature has.
recorded_event = st.tuples(
    st.sampled_from((ENTRY_SAVED_EVENT, *OTHER_TRAIL_NAMES)),
    st.integers(min_value=-5, max_value=5),
    st.sampled_from((True, False, None)),
    st.one_of(st.none(), st.integers(min_value=1, max_value=30_000)),
)

#: Read-only universe (contract shape: query). Every slot a save could move is
#: declared so `strict=True` proves the count is a pure read of the trail.
TRAIL_UNIVERSE = {"trail.rows", "trail.event_count", "record.entries"}


def _payload_of(backdated: bool | None, entry_ms: int | None) -> str:
    payload: dict[str, object] = {"entry_ms": entry_ms}
    if backdated is not None:
        payload["backdated"] = backdated
    return json.dumps(payload)


def _seed_trail(db_path: Path, trail: list[tuple[str, int, bool | None, int | None]]) -> None:
    """Write the generated trail through the production store -- one events table."""
    store = SqliteEntryStore(db_path)
    store.apply_migrations()
    for name, day_offset, backdated, entry_ms in trail:
        store.append_event(
            ts=f"{WINDOW_START + timedelta(days=day_offset)}T08:30:00+00:00",
            name=name,
            payload=_payload_of(backdated, entry_ms),
        )


def _trail_state(db_path: Path) -> dict[str, object]:
    """Everything a WRITE could move, snapshotted off the real table."""
    store = SqliteEntryStore(db_path)
    with closing(sqlite3.connect(db_path)) as connection:
        rows = connection.execute("SELECT ts, name, payload FROM events ORDER BY id").fetchall()
    return {
        "trail.rows": rows,
        "trail.event_count": store.count_events(ENTRY_SAVED_EVENT),
        "record.entries": [(entry.day, entry.weight_kg) for entry in store.all_entries()],
    }


def _repairs_in_window(trail: list[tuple[str, int, bool | None, int | None]]) -> int:
    """The oracle, stated in the contract's own words: saves flagged backdated,
    stamped on the window's first day or any later day."""
    return sum(
        1
        for name, day_offset, backdated, _ in trail
        if name == ENTRY_SAVED_EVENT and day_offset >= 0 and backdated is True
    )


@pytest.mark.property
@pytest.mark.real_io
@pytest.mark.kpi
@given(trail=st.lists(recorded_event, max_size=20))
@settings(max_examples=50, deadline=None)
def test_repair_count_is_exactly_the_backdated_saves_in_the_window(
    trail: list[tuple[str, int, bool | None, int | None]],
) -> None:
    with tempfile.TemporaryDirectory() as workspace:
        db_path = Path(workspace) / "weight.db"
        _seed_trail(db_path, trail)
        before = _trail_state(db_path)

        counted = backdated_saves_since(db_path, ENTRY_SAVED_EVENT, WINDOW_START)

        assert counted == _repairs_in_window(trail), (
            "KPI-8 counts exactly the saves the record itself calls repairs: an "
            "entry.saved carrying backdated true, on the window's first day or later "
            f"-- trail {trail}"
        )
        assert_state_delta(
            before=before,
            after=_trail_state(db_path),
            universe=TRAIL_UNIVERSE,
            expected={},  # reading the repair count is a read: the trail never moves
            strict=True,
        )
