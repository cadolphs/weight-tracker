"""Trend math -- local-level Kalman filter + RTS smoother, Huberized (ADR-004).

RED scaffold (created by DISTILL). Constants below ARE the determinism contract:
never re-estimated from data at runtime; changes only via a superseding ADR.
"""

from __future__ import annotations

from typing import Sequence

from weight_tracker.core.types import Entry, TrendPoint

__SCAFFOLD__ = True

# ADR-004 fixed parameters (determinism contract)
R_KG2 = 0.20                                   # observation noise variance (sigma_eps ~ 0.45 kg)
ALPHA = 0.10                                   # steady-state forward gain (Hacker's Diet alpha)
Q_KG2 = R_KG2 * ALPHA**2 / (1.0 - ALPHA)       # ~0.002222 kg^2 process noise variance
HUBER_DELTA_KG = 1.0                           # innovation clip


def trend_series(entries: Sequence[Entry]) -> list[TrendPoint]:
    """Smoothed trend on the daily calendar grid from first to last entry day, inclusive.

    Local-level state-space model: Kalman forward pass (Huber-clipped innovations,
    missing days = predict-only, no interpolation) + Rauch-Tung-Striebel backward
    pass; the SMOOTHED series is returned (retrospective revision is intentional).
    Pure function of the full entry set: same entries -> identical series, always.
    Input order must not matter (entries are keyed by day).
    """
    raise AssertionError("Not yet implemented -- RED scaffold")
