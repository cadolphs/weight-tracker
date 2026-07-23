"""Typed test-side domain vocabulary (Mandate-12 SSOT + zero duplication).

Domain nouns are defined ONCE in `weight_tracker.core.types` (production SSOT)
and re-exported here; this module adds only test-side typed vocabulary
(phrase-to-reason mapping, scale labels, date parsing for Gherkin surface).
Step methods and composition services consume these types -- never raw strings
where an enum exists.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from enum import Enum

from weight_tracker.core.types import (  # noqa: F401  (re-exports are the point)
    MAX_DEVICE_SKEW_DAYS,
    MAX_WEIGHT_KG,
    MIN_WEIGHT_KG,
    PRECISION_KG,
    Entry,
    Rejected,
    RejectionReason,
    Saved,
    TimeScale,
    TrendPoint,
    ViewMode,
)

TEST_PASSPHRASE = "correct-horse-battery-staple"

#: Business-language rejection phrases (Gherkin surface) -> closed reason set (C6b/C6c).
REASON_PHRASES: dict[str, RejectionReason] = {
    "the value must be between 30.0 and 250.0 kg": RejectionReason.OUT_OF_RANGE,
    "the value is finer than the 0.1 kg scale": RejectionReason.BAD_PRECISION,
    "that is not a weight": RejectionReason.NOT_A_WEIGHT,
    "a weight is required": RejectionReason.MISSING_VALUE,
    "future dates cannot be logged": RejectionReason.FUTURE_DATE,
    "the date is not recognisable": RejectionReason.BAD_DATE,
}

#: Gherkin scale labels -> TimeScale enum.
SCALE_LABELS: dict[str, TimeScale] = {
    "1W": TimeScale.ONE_WEEK,
    "1M": TimeScale.ONE_MONTH,
    "3M": TimeScale.THREE_MONTHS,
    "6M": TimeScale.SIX_MONTHS,
    "1Y": TimeScale.ONE_YEAR,
    "All": TimeScale.ALL,
    "ALL": TimeScale.ALL,
}

#: Window length in days per scale (pinned at DISTILL; window = [today - (N-1), today]).
SCALE_WINDOW_DAYS: dict[TimeScale, int] = {
    TimeScale.ONE_WEEK: 7,
    TimeScale.ONE_MONTH: 30,
    TimeScale.THREE_MONTHS: 91,
    TimeScale.SIX_MONTHS: 182,
    TimeScale.ONE_YEAR: 365,
}

VIEW_WORDS: dict[str, ViewMode] = {
    "Trend": ViewMode.TREND,
    "trend": ViewMode.TREND,
    "Raw": ViewMode.RAW,
    "raw": ViewMode.RAW,
}


class TrendDirection(Enum):
    """Recent movement of the record, as the Gherkin surface speaks it (US-007)."""

    FALLING = "falling"
    RISING = "rising"
    STEADY = "steady"


class RateDisposition(Enum):
    """Whether the weekly rate is shown or honestly held back (ADR-006 span rule)."""

    SHOWN = "shown"
    HELD_BACK = "held back"


_WEEKDAYS = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)


def parse_day(text: str) -> date:
    """Parse a Gherkin day like 'Tuesday 21 July 2026', '21 July 2026' or ISO."""
    cleaned = text.strip()
    for weekday in _WEEKDAYS:
        cleaned = cleaned.removeprefix(weekday).strip()
    for fmt in ("%d %B %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"unparseable Gherkin day: {text!r}")


def parse_scale(label: str) -> TimeScale:
    return SCALE_LABELS[label]


def parse_view(word: str) -> ViewMode:
    return VIEW_WORDS[word]


def parse_direction(word: str) -> TrendDirection:
    return TrendDirection(word)


def parse_rate_disposition(phrase: str) -> RateDisposition:
    return RateDisposition(phrase)


def parse_reason(phrase: str) -> RejectionReason:
    return REASON_PHRASES[phrase]


def window_start(scale: TimeScale, today: date) -> date | None:
    """First day of the window for a scale, or None for ALL (unbounded)."""
    if scale is TimeScale.ALL:
        return None
    return today - timedelta(days=SCALE_WINDOW_DAYS[scale] - 1)
