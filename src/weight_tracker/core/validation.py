"""Pure validation and upsert-resolution functions -- RED scaffold (created by DISTILL).

Rules (System Constraints, US-001/US-003):
- weight parseable, 30.0 <= kg <= 250.0, exactly 0.1 kg precision, never silently coerced
- date parseable, date <= server_utc_date + MAX_DEVICE_SKEW_DAYS (device-local day, A5)
- one entry per calendar day: applying an entry for an existing day REPLACES it
"""

from __future__ import annotations

from datetime import date
from typing import Mapping

from weight_tracker.core.types import Rejected

__SCAFFOLD__ = True


def validate_weight(raw: str) -> float | Rejected:
    """Parse and validate a raw weight input.

    Returns the weight in kg, or Rejected with reason in
    {MISSING_VALUE, NOT_A_WEIGHT, OUT_OF_RANGE, BAD_PRECISION}.
    """
    raise AssertionError("Not yet implemented -- RED scaffold")


def validate_entry_date(raw: str, server_utc_today: date) -> date | Rejected:
    """Parse and validate an entry date against the no-future rule with device-skew bound.

    Accepts dates up to server_utc_today + MAX_DEVICE_SKEW_DAYS (a phone one timezone
    ahead may already be in its new day). Returns Rejected with reason in
    {BAD_DATE, FUTURE_DATE} otherwise.
    """
    raise AssertionError("Not yet implemented -- RED scaffold")


def apply_entry(record: Mapping[date, float], day: date, weight_kg: float) -> dict[date, float]:
    """Pure upsert resolution: returns the new record with `day` holding exactly `weight_kg`.

    One-entry-per-day invariant: never duplicates, always replaces. All other days unchanged.
    """
    raise AssertionError("Not yet implemented -- RED scaffold")
