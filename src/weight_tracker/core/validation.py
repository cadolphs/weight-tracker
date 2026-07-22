"""Pure validation and upsert-resolution functions.

Rules (System Constraints, US-001/US-003):
- weight parseable, 30.0 <= kg <= 250.0, exactly 0.1 kg precision, never silently coerced
- date parseable, date <= server_utc_date + MAX_DEVICE_SKEW_DAYS (device-local day, A5)
- one entry per calendar day: applying an entry for an existing day REPLACES it

All functions are total over hostile input: every failure maps to `Rejected`
with a reason from the closed `RejectionReason` set (C6a, C6c) -- no exceptions
escape the pure core. `server_utc_today` is a parameter: the core never reads a clock.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from weight_tracker.core.types import (
    MAX_DEVICE_SKEW_DAYS,
    MAX_WEIGHT_KG,
    MIN_WEIGHT_KG,
    Rejected,
    RejectionReason,
)


def validate_weight(raw: str) -> float | Rejected:
    """Parse and validate a raw weight input.

    Returns the weight in kg, or Rejected with reason in
    {MISSING_VALUE, NOT_A_WEIGHT, OUT_OF_RANGE, BAD_PRECISION}.
    """
    if raw.strip() == "":
        return Rejected(RejectionReason.MISSING_VALUE)
    parsed = _parse_weight_decimal(raw)
    if parsed is None or not parsed.is_finite():
        return Rejected(RejectionReason.NOT_A_WEIGHT)
    if not MIN_WEIGHT_KG <= parsed <= MAX_WEIGHT_KG:
        return Rejected(RejectionReason.OUT_OF_RANGE)
    if not _has_tenth_precision(parsed):
        return Rejected(RejectionReason.BAD_PRECISION)
    return float(parsed)


def validate_entry_date(raw: str, server_utc_today: date) -> date | Rejected:
    """Parse and validate an entry date against the no-future rule with device-skew bound.

    Accepts dates up to server_utc_today + MAX_DEVICE_SKEW_DAYS (a phone one timezone
    ahead may already be in its new day). Returns Rejected with reason in
    {BAD_DATE, FUTURE_DATE} otherwise.
    """
    parsed = _parse_iso_date(raw)
    if parsed is None:
        return Rejected(RejectionReason.BAD_DATE)
    latest_allowed = server_utc_today + timedelta(days=MAX_DEVICE_SKEW_DAYS)
    if parsed > latest_allowed:
        return Rejected(RejectionReason.FUTURE_DATE)
    return parsed


def apply_entry(record: Mapping[date, float], day: date, weight_kg: float) -> dict[date, float]:
    """Pure upsert resolution: returns the new record with `day` holding exactly `weight_kg`.

    One-entry-per-day invariant: never duplicates, always replaces. All other days unchanged.
    """
    return {**record, day: weight_kg}


def _parse_weight_decimal(raw: str) -> Decimal | None:
    """Parse hostile text into an exact Decimal, or None if it is not a number at all."""
    try:
        return Decimal(raw.strip())
    except InvalidOperation:
        return None


def _has_tenth_precision(weight_kg: Decimal) -> bool:
    """True when the value carries no information finer than 0.1 kg (A2: reject, never round)."""
    exponent = weight_kg.normalize().as_tuple().exponent
    return isinstance(exponent, int) and exponent >= -1


def _parse_iso_date(raw: str) -> date | None:
    """Parse hostile text into a calendar date, or None when unparseable."""
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None
