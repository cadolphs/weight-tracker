"""Domain types (ubiquitous language, DISCUSS/DESIGN SSOT).

Single source of truth for domain nouns (Mandate-12): acceptance-test
`domain_types.py` re-exports from here rather than redefining.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class TimeScale(Enum):
    """Selectable graph windows (A3, OQ-5 resolution)."""

    ONE_WEEK = "1W"
    ONE_MONTH = "1M"
    THREE_MONTHS = "3M"
    SIX_MONTHS = "6M"
    ONE_YEAR = "1Y"
    ALL = "ALL"


class ViewMode(Enum):
    """Graph lens (US-005). Default on open is TREND (A4)."""

    TREND = "trend"
    RAW = "raw"


class RejectionReason(Enum):
    """Closed set of save-rejection reasons. No other rejection reason may exist (C6c)."""

    OUT_OF_RANGE = "out_of_range"  # outside 30.0-250.0 kg (A1)
    BAD_PRECISION = "bad_precision"  # finer than 0.1 kg (A2)
    NOT_A_WEIGHT = "not_a_weight"  # unparseable weight input
    MISSING_VALUE = "missing_value"  # empty submit
    FUTURE_DATE = "future_date"  # beyond device-skew bound (server UTC date + 1)
    BAD_DATE = "bad_date"  # unparseable date


# Validation constants (System Constraints A1/A2)
MIN_WEIGHT_KG = 30.0
MAX_WEIGHT_KG = 250.0
PRECISION_KG = 0.1
# Timezone-skew bound (DESIGN open question 1, pinned at DISTILL):
# client device-local date accepted iff date <= server_utc_date + MAX_DEVICE_SKEW_DAYS
MAX_DEVICE_SKEW_DAYS = 1


@dataclass(frozen=True)
class Entry:
    """One logged weight: the `weight_entry` shared artifact. At most one per calendar day."""

    day: date
    weight_kg: float
    entry_ms: int | None = None  # KPI-1 client-measured icon-tap -> save-confirm duration


@dataclass(frozen=True)
class TrendPoint:
    """One point of the smoothed trend series, on the daily calendar grid (ADR-004)."""

    day: date
    trend_kg: float


@dataclass(frozen=True)
class Saved:
    day: date
    weight_kg: float

    @property
    def confirmation(self) -> str:
        """Human confirmation shown after a save, e.g. 'Saved: 82.4 kg — Tue 21 Jul'."""
        return f"Saved: {self.weight_kg:.1f} kg — {self.day:%a} {self.day.day} {self.day:%b}"


@dataclass(frozen=True)
class Rejected:
    reason: RejectionReason
