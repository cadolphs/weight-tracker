"""Layer-1 pure-core properties for the trend (US-004, ADR-004) -- PBT full (Mandate 9).

Driving port = the pure function `trend_series` (its signature IS the port).
Oracles encode ADR-004's quantified guarantees with the fixed parameters
R_KG2 = 0.20, Q_KG2 = R*alpha^2/(1-alpha) with alpha = 0.10, Huber delta = 1.0 kg:

  * determinism: a FIXED entry set always renders an identical line
    (retrospective revision when the entry set CHANGES is by design)
  * input-order invariance (entries are keyed by day)
  * daily-grid coverage: first entry day .. last entry day inclusive, gaps included
  * smoothness: a single-day +1.5 kg outlier moves the trend <= 0.3 kg everywhere
  * Huber clipping: an outlier of ANY magnitude moves the trend <= 0.3 kg
  * gap continuity: the CURRENT line steps <= 0.3 kg/day across gaps up to 7 days
    (bounded step, no kink -- never immutability of previously rendered values)
  * responsiveness: a sustained 0.5 kg/week decline is visible within 7 days,
    and after 3 weeks the endpoint sits >1 kg below the pre-onset PLATEAU
    (anchored on the fixed input level, never on a retrospectively revised
    rendered value -- ADR-004 Consequences)
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from weight_tracker.core.trend import trend_series
from weight_tracker.core.types import Entry

pytestmark = [pytest.mark.property, pytest.mark.us_004]

START = date(2026, 3, 1)
SPIKE_LIMIT_KG = 0.3
STEP_LIMIT_KG = 0.3

weights = st.integers(min_value=400, max_value=1500).map(lambda i: i / 10)  # 40.0..150.0 kg


def entries_on(offsets: list[int], kgs: list[float]) -> list[Entry]:
    return [Entry(day=START + timedelta(days=o), weight_kg=w) for o, w in zip(offsets, kgs)]


@st.composite
def entry_sets(draw, min_size: int = 1, max_size: int = 60) -> list[Entry]:
    offsets = sorted(draw(st.sets(st.integers(0, 120), min_size=min_size, max_size=max_size)))
    kgs = draw(st.lists(weights, min_size=len(offsets), max_size=len(offsets)))
    return entries_on(offsets, kgs)


def steady(kg: float, days: int, first_offset: int = 0) -> list[Entry]:
    return entries_on(list(range(first_offset, first_offset + days)), [kg] * days)


@given(entries=entry_sets())
@settings(max_examples=100, deadline=None)
def test_a_fixed_entry_set_always_renders_an_identical_line(entries):
    assert trend_series(entries) == trend_series(entries)


@given(entries=entry_sets(min_size=2), seed=st.randoms())
@settings(max_examples=100, deadline=None)
def test_entry_order_never_changes_the_line(entries, seed):
    shuffled = list(entries)
    seed.shuffle(shuffled)
    assert trend_series(shuffled) == trend_series(entries)


@given(entries=entry_sets())
@settings(max_examples=100, deadline=None)
def test_trend_covers_every_day_from_first_to_last_entry(entries):
    points = trend_series(entries)
    first, last = entries[0].day, entries[-1].day
    assert [p.day for p in points] == [
        first + timedelta(days=o) for o in range((last - first).days + 1)
    ]


@given(kg=st.integers(500, 1200).map(lambda i: i / 10), days=st.integers(14, 45))
@settings(max_examples=100, deadline=None)
@example(kg=82.3, days=15)  # the sushi-dinner canonical case (US-004 domain example)
def test_a_single_day_spike_of_1_5kg_moves_the_trend_at_most_0_3kg(kg, days):
    base = steady(kg, days)
    spiked = base[:-1] + [Entry(day=base[-1].day, weight_kg=round(kg + 1.5, 1))]
    calm = {p.day: p.trend_kg for p in trend_series(base)}
    noisy = {p.day: p.trend_kg for p in trend_series(spiked)}
    assert max(abs(noisy[d] - calm[d]) for d in calm) <= SPIKE_LIMIT_KG


@given(
    kg=st.integers(500, 1200).map(lambda i: i / 10),
    days=st.integers(14, 45),
    outlier=st.integers(2, 50),
)
@settings(max_examples=100, deadline=None)
def test_huber_clipping_bounds_an_outlier_of_any_magnitude(kg, days, outlier):
    base = steady(kg, days)
    wild_kg = min(round(kg + outlier, 1), 250.0)
    spiked = base[:-1] + [Entry(day=base[-1].day, weight_kg=wild_kg)]
    calm = {p.day: p.trend_kg for p in trend_series(base)}
    wild = {p.day: p.trend_kg for p in trend_series(spiked)}
    assert max(abs(wild[d] - calm[d]) for d in calm) <= SPIKE_LIMIT_KG


@given(
    kg=st.integers(500, 1200).map(lambda i: i / 10),
    gap_days=st.integers(1, 7),
    side_days=st.integers(7, 21),
)
@settings(max_examples=100, deadline=None)
def test_the_current_line_crosses_a_gap_with_bounded_daily_steps(kg, gap_days, side_days):
    before_gap = steady(kg, side_days)
    after_gap = steady(kg, side_days, first_offset=side_days + gap_days)
    points = trend_series(before_gap + after_gap)
    steps = [abs(b.trend_kg - a.trend_kg) for a, b in zip(points, points[1:])]
    assert max(steps) <= STEP_LIMIT_KG
    assert all(abs(p.trend_kg - kg) <= SPIKE_LIMIT_KG for p in points)


@given(kg=st.integers(600, 1100).map(lambda i: i / 10))
@settings(max_examples=50, deadline=None)
def test_a_sustained_half_kilo_per_week_decline_is_visible_within_7_days(kg):
    plateau_kg = kg  # the pre-onset level: a FIXED input, never a revised rendered value
    stable = steady(plateau_kg, 14)
    onset = 14
    decline = [
        Entry(
            day=START + timedelta(days=onset + o),
            weight_kg=round(plateau_kg - 0.5 * (o // 7 + 1), 1),
        )
        for o in range(21)
    ]
    onset_day = START + timedelta(days=onset)

    # Within 7 days (the AC as the user lives it): with only the first decline
    # week LOGGED, the current line already points down and its endpoint sits
    # visibly below the plateau (RTS endpoint = filtered endpoint ~ plateau-0.26).
    # Rejects over-lagging smoothers: an EMA with alpha=0.01 leaves the endpoint
    # within ~0.03 kg of the plateau and fails the -0.1 clause.
    week_one = {p.day: p.trend_kg for p in trend_series(stable + decline[:7])}
    assert week_one[max(week_one)] < week_one[onset_day]
    assert week_one[max(week_one)] < plateau_kg - 0.1

    # Three weeks logged: the CURRENT line falls through the onset window
    # (shape of the current line -- the only thing ADR-004 lets an oracle pin).
    series = {p.day: p.trend_kg for p in trend_series(stable + decline)}
    assert series[onset_day + timedelta(days=7)] < series[onset_day] - 0.05

    # ...and the endpoint is >1 kg below the PLATEAU. Anchoring on the fixed
    # input, NOT on series[onset_day]: RTS revises the onset-day value down
    # ~0.45 kg while the endpoint lags ~0.40 kg, capping any onset-anchored
    # delta at ~0.65 kg for EVERY correct ADR-004 implementation (oracle-
    # verified 2026-07-22). Raw level is plateau-1.5 by day 21; the smoothed
    # endpoint reaches ~plateau-1.10 (margin ~0.10, shift-invariant: 0.5 kg
    # steps never trip the Huber clip, so the filter is linear here).
    # Rejects a flat/cumulative-mean line, which would sit at ~plateau-0.6.
    assert series[max(series)] < plateau_kg - 1.0
