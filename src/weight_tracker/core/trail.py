"""The Trail -- the append-only KPI event record, read as one weekly report (ADR-015).

GLOSSARY: Trail, Event, KPI report. This module is the trail's vocabulary and
its only derivation:

* `EventName` -- the closed set of names the trail speaks. Routes decide WHEN
  to emit (ADR-009); the names themselves live here and nowhere else.
* `parse_study_signal` -- the beacon's closed-vocabulary gate (ADR-009): free
  text cannot pass it, so free text can never reach the trail.
* `kpi_report(events, today)` -- the `/stats` report as a PURE function of the
  events and the day it is read on: every counter, the rolling-week framing
  and the KPI-1 speed summary derive here, so the shell has nothing to assemble.

Pure Domain Core module: no I/O, no clock, imports nothing from the shell
(import-linter contract). The shell (`shell/trail.py`) stamps and stores.
"""

from __future__ import annotations

import statistics
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any

from weight_tracker.core.types import TimeScale, ViewMode, window_start


class EventName(Enum):
    """The trail's dotted grammar, closed. A name's `.value` is its on-trail spelling."""

    ENTRY_SAVED = "entry.saved"
    #: Emission RETIRED by ADR-009 (2026-07-24): GET /trend is a pure read. The
    #: name remains so the report can keep reading the frozen-historical rows.
    TREND_VIEW_OPENED = "trend.view.opened"
    TREND_GLANCE_SHOWN = "trend.glance.shown"
    #: Intent telemetry (ADR-009): intent is recorded on intent-expressing
    #: surfaces, never inferred on data reads. Ambient = the front page
    #: delivering the graph; deliberate = a History-page open or an explicit
    #: lens/scale tap (beacon).
    HOME_GRAPH_SHOWN = "home.graph.shown"
    TREND_STUDY_OPENED = "trend.study.opened"
    TREND_STUDY_INTERACTION = "trend.study.interaction"


@dataclass(frozen=True)
class Event:
    """One row of the trail, read back: when, what, and the payload it carried.

    `name` is a plain string on purpose -- the trail is append-only and may hold
    names from retired emissions or hand-seeded rows; the report ignores what it
    does not know rather than refusing to read."""

    ts: datetime
    name: str
    payload: Mapping[str, object]


#: The study beacon's closed vocabulary (ADR-009): the ONLY words a signal may
#: speak. Surface/control name the two graph surfaces and their two explicit
#: controls; value tokens derive from the core's own lens and scale sets
#: (Mandate-12: reuse, no new enums). Anything else never reaches the trail.
STUDY_SURFACES = frozenset({"home", "history"})
STUDY_CONTROLS = frozenset({"lens", "scale"})
STUDY_VALUES = frozenset(lens.value for lens in ViewMode) | frozenset(
    scale.value for scale in TimeScale
)
STUDY_VOCABULARY: dict[str, frozenset[str]] = {
    "surface": STUDY_SURFACES,
    "control": STUDY_CONTROLS,
    "value": STUDY_VALUES,
}


def parse_study_signal(body: object) -> dict[str, str] | None:
    """Total parse of a beacon body against the closed vocabulary (ADR-009).

    Pure judgment, `parse_time_scale` precedent: the validated
    {surface, control, value} tokens when every field speaks the vocabulary;
    None for ANYTHING else -- wrong shape, unknown words, non-string values.
    Free text cannot survive this gate, so it can never reach the append-only
    trail (unbounded preservation). The core judges; the shell phrases 400."""
    if not isinstance(body, dict) or set(body) != set(STUDY_VOCABULARY):
        return None
    if any(
        not isinstance(body[field], str) or body[field] not in spoken
        for field, spoken in STUDY_VOCABULARY.items()
    ):
        return None
    return {field: body[field] for field in STUDY_VOCABULARY}


def kpi_week_start(today: date) -> date:
    """Rolling KPI week: exactly the 1W scale window -- the core's single pinned
    "last N days inclusive of today" rule applied to the trail (no second copy
    of the calendar arithmetic)."""
    week_start = window_start(TimeScale.ONE_WEEK, today)
    return week_start if week_start is not None else today  # None is ALL-only, 1W is bounded


def speed_summary(samples: Sequence[int]) -> dict[str, Any]:
    """KPI-1 speed report over client-measured entry durations: median, p90, count.

    Pure summary of whatever window the caller selected; an empty window reports
    honest nulls rather than a pretended speed."""
    if not samples:
        return {"median_ms": None, "p90_ms": None, "sample_count": 0}
    ordered = sorted(samples)
    return {
        "median_ms": statistics.median(ordered),
        "p90_ms": _p90(ordered),
        "sample_count": len(ordered),
    }


def _p90(ordered_samples: Sequence[int]) -> float:
    """Worst-case-but-one duration: the 90th percentile (last decile boundary,
    inclusive method so it never extrapolates past the observed worst case)."""
    if len(ordered_samples) == 1:
        return float(ordered_samples[0])
    return float(statistics.quantiles(ordered_samples, n=10, method="inclusive")[-1])


def kpi_report(events: Sequence[Event], today: date) -> dict[str, Any]:
    """The `/stats` report: the whole trail in, one dict out (the HTTP contract).

    Two counters are all-time; everything else reads the rolling KPI week ending
    on `today`. A pure function of the SET of events -- order never matters --
    and of the day it is read on, so the shell's only job is to read and stamp.
    """
    week_start = kpi_week_start(today)
    this_week = [event for event in events if event.ts.date() >= week_start]
    saves_this_week = [event for event in this_week if event.name == EventName.ENTRY_SAVED.value]
    return {
        "entry_logged_count": _count(events, EventName.ENTRY_SAVED),
        # FROZEN-HISTORICAL (ADR-009 instrument switch, labeled per Forge
        # condition 2): the trend.view.opened emission retired 2026-07-24;
        # this counter reads the preserved pre-switch rows and can only age.
        # The live KPI-3 counter is trend_study_this_week below.
        "trend_view_opened_count": _count(events, EventName.TREND_VIEW_OPENED),
        # Ambient glance deliveries over the SAME rolling week as the deliberate
        # trend views beside it (KPI-3/KPI-5 separation read from the real trail);
        # historical seeding/backdated saves age out of the window by construction.
        "trend_glance_shown_count": _count(this_week, EventName.TREND_GLANCE_SHOWN),
        "trend_views_this_week": _count(this_week, EventName.TREND_VIEW_OPENED),
        # KPI-3 live (ADR-009, Q2): raw rolling-week count of deliberate study --
        # History-page opens + explicit lens/scale taps; any session collapse is
        # a read-time refinement.
        "trend_study_this_week": (
            _count(this_week, EventName.TREND_STUDY_OPENED)
            + _count(this_week, EventName.TREND_STUDY_INTERACTION)
        ),
        # KPI-7 (ADR-009): ambient morning-graph deliveries, same rolling week.
        "home_graph_shown_this_week": _count(this_week, EventName.HOME_GRAPH_SHOWN),
        # KPI-8 (ADR-011): gaps and typos repaired in the app. Read off the
        # `backdated` flag the save itself stamps -- ONE event per save (D-23) --
        # so a repair shows up here exactly where it is withheld from the
        # morning-speed record below. A save written before the flag existed
        # carries no `backdated` word and is no repair.
        "backdated_saves_this_week": sum(
            1 for event in saves_this_week if event.payload.get("backdated") is True
        ),
        # KPI-1: a repair carries no timing at all (null entry_ms, ADR-011), so
        # it is not a sample -- purity is structural at the write, not a rule here.
        "speed": speed_summary(
            [
                int(duration)  # type: ignore[call-overload]
                for event in saves_this_week
                if (duration := event.payload.get("entry_ms")) is not None
            ]
        ),
    }


def _count(events: Sequence[Event], name: EventName) -> int:
    return sum(1 for event in events if event.name == name.value)
