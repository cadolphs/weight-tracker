"""Layer-1 pure-core properties for the glance (US-007, ADR-006) -- PBT full (Mandate 9).

Driving port = the pure functions `glance`, `quantize_rate`, `rate_glyph` (their
signatures ARE the port). Oracle = the shipped `trend_series` (OUT-5-verified by the
prior feature): ADR-006 derives the glance FROM that series, so the properties pin:

  * determinism + input-order invariance (a fixed entry set -> an identical glance)
  * single source: glance value == the trend line's END value (where the graph ends)
  * the rate IS the line's own trailing-7-day net change: smoothed[-1] - smoothed[-8]
    (sign-and-magnitude consistency with the displayed line holds by construction)
  * sparse honesty: rate is None below a 7-day ENTRY span (latest - earliest entry
    date), present at exactly 7 and beyond (span >= 7  <=>  grid >= 8 points)
  * empty record -> no glance; a single entry already has a trend value (rate None)
  * quantization: `round(rate / 0.05) * 0.05` verbatim (built-in round, float
    semantics pinned as-is), and the glyph follows the ROUNDED sign (-> at 0.00,
    including negative zero)
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from weight_tracker.core.glance import glance, quantize_rate, rate_glyph
from weight_tracker.core.trend import trend_series
from weight_tracker.core.types import Entry

pytestmark = [pytest.mark.property, pytest.mark.us_007]

START = date(2026, 3, 1)

weights = st.integers(min_value=400, max_value=1500).map(lambda i: i / 10)  # 40.0..150.0 kg


def entries_on(offsets: list[int], kgs: list[float]) -> list[Entry]:
    return [
        Entry(day=START + timedelta(days=o), weight_kg=w) for o, w in zip(offsets, kgs, strict=True)
    ]


@st.composite
def spanned_entry_sets(draw, min_span: int = 0, max_span: int = 30) -> list[Entry]:
    """Entry sets with a CONTROLLED entry-based span: first and last offsets pinned."""
    span = draw(st.integers(min_span, max_span))
    inner = draw(st.sets(st.integers(0, span), max_size=span + 1))
    offsets = sorted({0, span} | inner)
    kgs = draw(st.lists(weights, min_size=len(offsets), max_size=len(offsets)))
    return entries_on(offsets, kgs)


@given(entries=spanned_entry_sets())
@settings(max_examples=100, deadline=None)
def test_a_fixed_entry_set_always_renders_an_identical_glance(entries):
    assert glance(entries) == glance(entries)


@given(entries=spanned_entry_sets(min_span=1), seed=st.randoms())
@settings(max_examples=100, deadline=None)
def test_entry_order_never_changes_the_glance(entries, seed):
    shuffled = list(entries)
    seed.shuffle(shuffled)
    assert glance(shuffled) == glance(entries)


@given(entries=spanned_entry_sets())
@settings(max_examples=100, deadline=None)
def test_the_glance_value_is_where_the_trend_line_ends(entries):
    summary = glance(entries)
    assert summary is not None
    assert summary.trend_kg == trend_series(entries)[-1].trend_kg


@given(entries=spanned_entry_sets(min_span=7))
@settings(max_examples=100, deadline=None)
def test_the_rate_is_the_lines_own_trailing_week_change(entries):
    series = trend_series(entries)
    summary = glance(entries)
    assert summary is not None
    # ADR-006 verbatim: the smoothed series' own net change over the trailing 7 grid
    # days -- sign-consistent with the visible endpoint movement by construction.
    assert summary.rate_kg_per_week == series[-1].trend_kg - series[-8].trend_kg


@given(entries=spanned_entry_sets(max_span=14))
@settings(max_examples=100, deadline=None)
@example(entries=entries_on([0, 6], [82.5, 82.5]))  # span 6: one day short, rate held
@example(entries=entries_on([0, 7], [82.5, 82.5]))  # span 7: exactly earned, rate shown
def test_the_rate_holds_its_tongue_below_a_seven_day_entry_span(entries):
    span_days = (entries[-1].day - entries[0].day).days
    summary = glance(entries)
    assert summary is not None
    assert (summary.rate_kg_per_week is not None) == (span_days >= 7)


def test_an_empty_record_offers_no_glance():
    assert glance([]) is None


@given(kg=weights)
@settings(max_examples=100, deadline=None)
def test_the_first_entry_already_has_a_trend_value_but_no_rate(kg):
    summary = glance(entries_on([0], [kg]))
    assert summary is not None
    assert summary.trend_kg == kg
    assert summary.rate_kg_per_week is None


@given(rate=st.floats(min_value=-3.0, max_value=3.0, allow_nan=False))
@settings(max_examples=200, deadline=None)
@example(rate=0.025)  # float 0.025/0.05 == 0.5 exactly: built-in round ties to even -> 0.0
@example(rate=0.075)  # float 0.075/0.05 == 1.4999...: rounds DOWN to 0.05 (pinned as-is)
@example(rate=-0.01)  # quantizes to -0.0: the glyph must still read ->
def test_quantization_snaps_to_the_pinned_0_05_grid(rate):
    # The oracle IS the ADR-006 pinned expression, float semantics included.
    assert quantize_rate(rate) == round(rate / 0.05) * 0.05


@given(rate=st.floats(min_value=-3.0, max_value=3.0, allow_nan=False))
@settings(max_examples=200, deadline=None)
@example(rate=0.0)
@example(rate=-0.02)  # rounds to -0.0 == 0.0: steady glyph, not a phantom decline
@example(rate=0.03)  # rounds to 0.05: rising
@example(rate=-0.26)  # rounds to -0.25: falling
def test_the_glyph_follows_the_rounded_sign(rate):
    quantized = quantize_rate(rate)
    expected = "↓" if quantized < 0 else ("↑" if quantized > 0 else "→")
    assert rate_glyph(quantized) == expected
