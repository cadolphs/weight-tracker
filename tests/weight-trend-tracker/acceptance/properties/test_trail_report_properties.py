"""Pure-core properties for the trail's KPI report (ADR-015) -- PBT full.

Driving port = the pure function `kpi_report(events, today)` (its signature IS
the port): the trail's events in, the `/stats` report out. These properties pin,
independently of HTTP, what `/stats` has always served:

  * the report carries exactly the shipped `/stats` keys -- the HTTP contract is
    the dict's shape, byte-identical before and after the trail moved;
  * the two all-time counters count every event of their name, however old;
  * every `*_this_week` counter and the speed report read the rolling KPI week:
    stamped on the week's first day (today - 6, the 1W scale's own window) or
    any later day -- the shipped rule has no upper edge, because the clock
    stamps every row and the report never second-guesses the trail;
  * deliberate study = History opens + beacon interactions, ambient apart (ADR-009);
  * a repair is an `entry.saved` whose payload says `backdated` (ADR-011) and it
    never contributes a speed sample, because a repair carries no timing at all;
  * the speed report is honest: nulls over an untimed week, otherwise the median,
    the inclusive p90 (never past the worst case) and the sample count;
  * the report is a pure function of the set of events: order never matters.

Vocabulary gate (`parse_study_signal`) properties sit here too: the beacon's
closed vocabulary is judged in the core, phrased as 400 by the shell.
"""

from __future__ import annotations

import dataclasses
import statistics
from datetime import UTC, date, datetime, time, timedelta

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from weight_tracker.core.trail import (
    Event,
    EventName,
    kpi_report,
    kpi_week_start,
    parse_study_signal,
    speed_summary,
)
from weight_tracker.core.types import TimeScale, ViewMode

pytestmark = [pytest.mark.property, pytest.mark.kpi]

#: The `/stats` contract, spelled out as the oracle (never derived from the code).
STATS_KEYS = frozenset(
    {
        "entry_logged_count",
        "trend_view_opened_count",
        "trend_glance_shown_count",
        "trend_views_this_week",
        "trend_study_this_week",
        "home_graph_shown_this_week",
        "backdated_saves_this_week",
        "speed",
    }
)
SPEED_KEYS = frozenset({"median_ms", "p90_ms", "sample_count"})

#: On-trail names, verbatim (the oracle must not read them off the enum).
ENTRY_SAVED = "entry.saved"
TREND_VIEW_OPENED = "trend.view.opened"
TREND_GLANCE_SHOWN = "trend.glance.shown"
HOME_GRAPH_SHOWN = "home.graph.shown"
TREND_STUDY_OPENED = "trend.study.opened"
TREND_STUDY_INTERACTION = "trend.study.interaction"
#: Names the trail may hold from a retired emission or a hand-seeded row: the
#: report must ignore them everywhere, whatever their payload says and whichever
#: side of `entry.saved` they sort on.
RETIRED_NAME = "trend.something.retired"
IMPORTED_NAME = "backfill.imported"

TODAY = date(2026, 7, 24)

days_around_today = st.integers(min_value=-20, max_value=3).map(
    lambda offset: TODAY + timedelta(days=offset)
)
times_of_day = st.times()


@st.composite
def trail_events(draw) -> Event:
    """One event as the trail could hold it: any name, any day near today, a
    payload shaped the way that name's emitter shapes it (or, for a save, the
    pre-ADR-011 shape with no `backdated` word at all)."""
    name = draw(
        st.sampled_from(
            (
                ENTRY_SAVED,
                TREND_VIEW_OPENED,
                TREND_GLANCE_SHOWN,
                HOME_GRAPH_SHOWN,
                TREND_STUDY_OPENED,
                TREND_STUDY_INTERACTION,
                RETIRED_NAME,
                IMPORTED_NAME,
            )
        )
    )
    stamped = datetime.combine(draw(days_around_today), draw(times_of_day), tzinfo=UTC)
    payload: dict[str, object] = {}
    if name in (ENTRY_SAVED, IMPORTED_NAME):  # an import may carry a save's words
        payload = {"entry_ms": draw(st.one_of(st.none(), st.integers(1, 30_000)))}
        flag = draw(st.sampled_from((True, False, None)))
        if flag is not None:
            payload["backdated"] = flag
    elif name == TREND_STUDY_INTERACTION:
        payload = {"surface": "home", "control": "lens", "value": "raw"}
    return Event(ts=stamped, name=name, payload=payload)


trails = st.lists(trail_events(), max_size=40)


def in_week(event: Event) -> bool:
    """The oracle's week: stamped on today - 6 or any later day (no upper edge)."""
    return event.ts.date() >= TODAY - timedelta(days=6)


def count(events: list[Event], name: str, *, week_only: bool) -> int:
    return sum(1 for e in events if e.name == name and (in_week(e) or not week_only))


# ------------------------------------------------------------------ the contract


@given(events=trails)
@settings(max_examples=100, deadline=None)
def test_the_report_serves_exactly_the_stats_contract(events):
    report = kpi_report(events, today=TODAY)
    assert set(report) == STATS_KEYS, f"/stats keys drifted: {sorted(report)}"
    assert set(report["speed"]) == SPEED_KEYS, f"speed keys drifted: {sorted(report['speed'])}"


@given(events=trails)
@settings(max_examples=100, deadline=None)
def test_the_all_time_counters_count_every_event_of_their_name(events):
    report = kpi_report(events, today=TODAY)
    assert report["entry_logged_count"] == count(events, ENTRY_SAVED, week_only=False)
    assert report["trend_view_opened_count"] == count(events, TREND_VIEW_OPENED, week_only=False)


@given(events=trails)
@settings(max_examples=100, deadline=None)
def test_the_week_counters_read_from_six_days_ago_onwards(events):
    report = kpi_report(events, today=TODAY)
    assert report["trend_glance_shown_count"] == count(events, TREND_GLANCE_SHOWN, week_only=True)
    assert report["trend_views_this_week"] == count(events, TREND_VIEW_OPENED, week_only=True)
    assert report["home_graph_shown_this_week"] == count(events, HOME_GRAPH_SHOWN, week_only=True)


@given(events=trails)
@settings(max_examples=100, deadline=None)
def test_deliberate_study_is_history_opens_plus_beacon_taps_this_week(events):
    report = kpi_report(events, today=TODAY)
    expected = count(events, TREND_STUDY_OPENED, week_only=True) + count(
        events, TREND_STUDY_INTERACTION, week_only=True
    )
    assert report["trend_study_this_week"] == expected, (
        "KPI-3 is the raw rolling-week count of History opens + explicit taps (ADR-009)"
    )


@given(events=trails)
@settings(max_examples=100, deadline=None)
def test_repairs_are_the_saves_flagged_backdated_this_week(events):
    report = kpi_report(events, today=TODAY)
    expected = sum(
        1
        for e in events
        if e.name == ENTRY_SAVED and in_week(e) and e.payload.get("backdated") is True
    )
    assert report["backdated_saves_this_week"] == expected, (
        "KPI-8 counts exactly the entry.saved events carrying backdated true inside the week"
    )


@given(events=trails)
@settings(max_examples=100, deadline=None)
def test_the_speed_report_is_the_timed_saves_this_week(events):
    report = kpi_report(events, today=TODAY)
    samples = [
        int(e.payload["entry_ms"])  # type: ignore[call-overload]
        for e in events
        if e.name == ENTRY_SAVED and in_week(e) and e.payload.get("entry_ms") is not None
    ]
    speed = report["speed"]
    assert speed["sample_count"] == len(samples)
    if not samples:
        assert speed == {"median_ms": None, "p90_ms": None, "sample_count": 0}, (
            "an untimed week makes no speed claims (honest nulls)"
        )
        return
    assert speed["median_ms"] == statistics.median(samples)
    assert max(samples) >= speed["p90_ms"] >= speed["median_ms"], (
        f"p90 must sit between the median and the worst case, got {speed}"
    )


@given(events=trails, seed=st.randoms(use_true_random=False))
@settings(max_examples=100, deadline=None)
def test_the_report_is_a_function_of_the_set_of_events_not_their_order(events, seed):
    shuffled = list(events)
    seed.shuffle(shuffled)
    assert kpi_report(shuffled, today=TODAY) == kpi_report(events, today=TODAY)


@given(today=st.dates(min_value=date(2026, 1, 1), max_value=date(2030, 12, 31)))
@settings(max_examples=50, deadline=None)
def test_the_kpi_week_is_the_one_week_scale_window(today):
    assert kpi_week_start(today) == today - timedelta(days=6)


def test_an_empty_trail_reports_zeros_and_honest_nulls():
    assert kpi_report([], today=TODAY) == {
        "entry_logged_count": 0,
        "trend_view_opened_count": 0,
        "trend_glance_shown_count": 0,
        "trend_views_this_week": 0,
        "trend_study_this_week": 0,
        "home_graph_shown_this_week": 0,
        "backdated_saves_this_week": 0,
        "speed": {"median_ms": None, "p90_ms": None, "sample_count": 0},
    }


def test_a_foreign_row_wearing_a_saves_payload_is_no_save():
    """A hand-seeded row under another name carries entry_ms and a backdated
    flag; the report reads the NAME, so it is neither a sample nor a repair."""
    foreign = Event(
        ts=datetime.combine(TODAY, time(8, 0), tzinfo=UTC),
        name=IMPORTED_NAME,
        payload={"entry_ms": 4200, "backdated": True},
    )
    report = kpi_report([foreign], today=TODAY)
    assert report["entry_logged_count"] == 0
    assert report["backdated_saves_this_week"] == 0
    assert report["speed"] == {"median_ms": None, "p90_ms": None, "sample_count": 0}


def test_an_event_read_back_cannot_be_rewritten():
    """Frozen (ADR-005): the report derives from rows as the trail holds them."""
    event = Event(ts=datetime.combine(TODAY, time(8, 0), tzinfo=UTC), name=ENTRY_SAVED, payload={})
    with pytest.raises(dataclasses.FrozenInstanceError):
        event.name = HOME_GRAPH_SHOWN  # type: ignore[misc]


def test_the_week_opens_at_midnight_six_days_ago_and_has_no_upper_edge():
    """Day -6 at 00:00 is in; day -7 at 23:59:59 is out; tonight is in; and a
    stamp a day AHEAD of today is in too -- the shipped rule counts everything
    from the week's first day onwards (a clock-stamped trail holds no future)."""
    first_day = datetime.combine(TODAY - timedelta(days=6), time(0, 0), tzinfo=UTC)
    day_before = datetime.combine(TODAY - timedelta(days=7), time(23, 59, 59), tzinfo=UTC)
    tonight = datetime.combine(TODAY, time(23, 59, 59), tzinfo=UTC)
    tomorrow = datetime.combine(TODAY + timedelta(days=1), time(0, 0), tzinfo=UTC)
    stamps = (first_day, day_before, tonight, tomorrow)
    events = [Event(ts=stamp, name=HOME_GRAPH_SHOWN, payload={}) for stamp in stamps]
    assert kpi_report(events, today=TODAY)["home_graph_shown_this_week"] == 3


# --------------------------------------------------------------- speed summary


@given(samples=st.lists(st.integers(1, 60_000), min_size=1, max_size=30))
@settings(max_examples=100, deadline=None)
def test_the_speed_summary_never_extrapolates_past_the_worst_case(samples):
    speed = speed_summary(samples)
    assert speed["sample_count"] == len(samples)
    assert speed["median_ms"] == statistics.median(samples)
    assert max(samples) >= speed["p90_ms"] >= speed["median_ms"]


@given(sample=st.integers(1, 60_000))
@settings(max_examples=20, deadline=None)
def test_a_single_sample_is_its_own_median_and_p90(sample):
    assert speed_summary([sample]) == {
        "median_ms": sample,
        "p90_ms": float(sample),
        "sample_count": 1,
    }


def test_the_p90_is_the_inclusive_last_decile_boundary():
    ordered = list(range(1, 11))  # 1..10
    assert (
        speed_summary(ordered)["p90_ms"]
        == statistics.quantiles(ordered, n=10, method="inclusive")[-1]
    )


# ------------------------------------------------------------ the event names


def test_the_trail_speaks_exactly_the_shipped_event_names():
    assert {name.value for name in EventName} == {
        ENTRY_SAVED,
        TREND_VIEW_OPENED,
        TREND_GLANCE_SHOWN,
        HOME_GRAPH_SHOWN,
        TREND_STUDY_OPENED,
        TREND_STUDY_INTERACTION,
    }


# ------------------------------------------------------- the vocabulary gate

STUDY_SURFACES = ("home", "history")
STUDY_CONTROLS = ("lens", "scale")
STUDY_VALUES = tuple(lens.value for lens in ViewMode) + tuple(scale.value for scale in TimeScale)


def speaks_the_vocabulary(body: object) -> bool:
    return (
        isinstance(body, dict)
        and set(body) == {"surface", "control", "value"}
        and body["surface"] in STUDY_SURFACES
        and body["control"] in STUDY_CONTROLS
        and body["value"] in STUDY_VALUES
    )


closed_vocabulary_signals = st.fixed_dictionaries(
    {
        "surface": st.sampled_from(STUDY_SURFACES),
        "control": st.sampled_from(STUDY_CONTROLS),
        "value": st.sampled_from(STUDY_VALUES),
    }
)

free_words = st.one_of(
    st.sampled_from(STUDY_SURFACES + STUDY_CONTROLS + STUDY_VALUES + ("kitchen", "", "HOME")),
    st.text(max_size=12),
    st.none(),
    st.booleans(),
    st.integers(-10, 10),
)

garbled_bodies = st.one_of(
    st.fixed_dictionaries({"surface": free_words, "control": free_words, "value": free_words}),
    st.dictionaries(st.text(max_size=10), free_words, max_size=4),
    free_words,
    st.lists(free_words, max_size=3),
).filter(lambda body: not speaks_the_vocabulary(body))


@given(signal=closed_vocabulary_signals)
@settings(max_examples=50, deadline=None)
def test_a_closed_vocabulary_signal_parses_to_exactly_its_three_validated_tokens(signal):
    assert parse_study_signal(signal) == signal


@given(body=garbled_bodies)
@settings(max_examples=75, deadline=None)
def test_anything_else_is_turned_away_by_the_vocabulary_gate(body):
    assert parse_study_signal(body) is None
