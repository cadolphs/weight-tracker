"""Pure-core properties for the day-keyed trend projection (US-016, ADR-013) --
PBT full, the paired property DELIVER owes its own new core function (ADR-025).

Driving port = the pure function `trend_by_day` (its signature IS the port;
pure functions are the exempt single-output category, so no state-delta
universe applies -- there is no adjacent state).

DISTILL-pinned contract, as properties:

  * ONE series (G-3/A36): every value is exactly the `trend_series` value for
    that day -- not a rounding of it, not a re-smoothing, not an average. If a
    second algorithm ever appears, or the day keys ever slip by one, this
    module is where it dies;
  * TOTAL over the record (A32): every ENTRY day has a value, because the grid
    spans first->last entry day. No row can want for a trend, so the production
    row builder needs no fallback branch and has none;
  * order-invariant and deterministic (ADR-004): the mapping is a pure function
    of the entry SET, so shuffling the read order changes nothing;
  * gap days are present in the mapping and absent from the lists -- the lists
    slice ENTRIES, not calendar days (A33), which is why the mapping may be
    larger than the record and never smaller.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from weight_tracker.core.trend import trend_by_day, trend_series
from weight_tracker.core.types import Entry

pytestmark = [pytest.mark.property, pytest.mark.us_016]

days = st.dates(min_value=date(2026, 1, 1), max_value=date(2026, 12, 31))
weights = st.integers(min_value=300, max_value=2500).map(lambda i: i / 10)  # 30.0..250.0 kg


@st.composite
def records(draw, min_size: int = 0, max_size: int = 25) -> list[Entry]:
    """A record: distinct days, one entry each, in arbitrary read order."""
    picked = draw(st.sets(days, min_size=min_size, max_size=max_size))
    kgs = draw(st.lists(weights, min_size=len(picked), max_size=len(picked)))
    return [Entry(day=d, weight_kg=kg) for d, kg in zip(sorted(picked), kgs, strict=True)]


@given(entries=records())
@settings(max_examples=100, deadline=None)
def test_it_is_exactly_the_series_keyed_by_day(entries):
    assert trend_by_day(entries) == {p.day: p.trend_kg for p in trend_series(entries)}, (
        "the column and the chart must plot ONE series (A36) -- this mapping is a view "
        "of trend_series, never a second computation"
    )


@given(entries=records(min_size=1))
@settings(max_examples=100, deadline=None)
def test_every_entry_day_has_a_value(entries):
    """Totality (A32): the grid spans first->last entry day, so a row can never
    want for its trend. This is what licenses the absence of a fallback branch."""
    missing = [e.day for e in entries if e.day not in trend_by_day(entries)]
    assert not missing, f"every entry day sits on the trend grid, but {missing} do not"


@given(entries=records(min_size=1))
@settings(max_examples=100, deadline=None)
def test_it_spans_the_record_and_fills_the_gaps(entries):
    """The mapping covers every calendar day from the first entry to the last --
    gap days included. They are present here and deliberately unrendered: the
    lists slice ENTRIES, not days (A33), so the mapping is never smaller than
    the record and is larger exactly by the gaps."""
    smoothed = trend_by_day(entries)
    first, last = min(e.day for e in entries), max(e.day for e in entries)
    expected = {first + timedelta(days=offset) for offset in range((last - first).days + 1)}
    assert set(smoothed) == expected
    assert len(smoothed) >= len(entries)


@given(entries=records())
@settings(max_examples=100, deadline=None)
def test_read_order_cannot_change_a_single_value(entries):
    assert trend_by_day(entries) == trend_by_day(list(reversed(entries))), (
        "the mapping is a pure function of the entry SET; all_entries() serving "
        "newest-first must not make it a different mapping (ADR-004)"
    )


@given(entries=records())
@settings(max_examples=50, deadline=None)
def test_the_same_record_answers_identically_every_time(entries):
    assert trend_by_day(entries) == trend_by_day(entries), "G-3: same entries, same numbers"


def test_an_empty_record_yields_an_empty_mapping():
    """Not None, not a raise: the row builder asks it for days it will never have,
    and the empty record simply has no rows to build."""
    assert trend_by_day([]) == {}


def test_a_single_entry_is_its_own_trend():
    """The diffuse-prior start (ADR-004): the first observation IS the state, so a
    first morning reads the same number in both columns rather than a blank."""
    assert trend_by_day([Entry(day=date(2026, 7, 24), weight_kg=77.2)]) == {date(2026, 7, 24): 77.2}
