"""Trend math -- local-level Kalman filter + RTS smoother, Huberized (ADR-004).

Constants below ARE the determinism contract: never re-estimated from data at
runtime; changes only via a superseding ADR.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta

from weight_tracker.core.types import Entry, TimeScale, TrendPoint, window_start

# ADR-004 fixed parameters (determinism contract)
R_KG2 = 0.20  # observation noise variance (sigma_eps ~ 0.45 kg)
ALPHA = 0.10  # steady-state forward gain (Hacker's Diet alpha)
Q_KG2 = R_KG2 * ALPHA**2 / (1.0 - ALPHA)  # ~0.002222 kg^2 process noise variance
HUBER_DELTA_KG = 1.0  # innovation clip


@dataclass(frozen=True)
class _ForwardPass:
    """Kalman forward-pass state per grid day, kept for the RTS backward pass."""

    filtered_means: tuple[float, ...]
    filtered_variances: tuple[float, ...]
    predicted_means: tuple[float, ...]
    predicted_variances: tuple[float, ...]


def trend_series(entries: Sequence[Entry]) -> list[TrendPoint]:
    """Smoothed trend on the daily calendar grid from first to last entry day, inclusive.

    Local-level state-space model: Kalman forward pass (Huber-clipped innovations,
    missing days = predict-only, no interpolation) + Rauch-Tung-Striebel backward
    pass; the SMOOTHED series is returned (retrospective revision is intentional).
    Pure function of the full entry set: same entries -> identical series, always.
    Input order must not matter (entries are keyed by day).
    """
    if not entries:
        return []
    weight_by_day = {entry.day: entry.weight_kg for entry in entries}
    grid = _daily_grid(min(weight_by_day), max(weight_by_day))
    later_observations = [weight_by_day.get(day) for day in grid[1:]]
    smoothed_means = _rts_backward(_kalman_forward(weight_by_day[grid[0]], later_observations))
    return [TrendPoint(day=day, trend_kg=kg) for day, kg in zip(grid, smoothed_means, strict=True)]


def trend_series_in(entries: Sequence[Entry], scale: TimeScale, today: date) -> list[TrendPoint]:
    """Smoothed trend for the selected scale: full-record smoothing, windowed OUTPUT.

    Derived, never stored (ADR-004): the trend is recomputed from the FULL entry
    set on every read, then the resulting points are windowed to the scale.
    Windowing the input entries instead would change smoothing near the window
    edge. ALL is unbounded; bounded scales keep [window_start, today].
    """
    first_shown_day = window_start(scale, today)
    full_series = trend_series(entries)
    if first_shown_day is None:
        return full_series
    return [point for point in full_series if first_shown_day <= point.day <= today]


def _daily_grid(first_day: date, last_day: date) -> list[date]:
    return [first_day + timedelta(days=offset) for offset in range((last_day - first_day).days + 1)]


def _huber_clip(innovation_kg: float) -> float:
    return max(-HUBER_DELTA_KG, min(HUBER_DELTA_KG, innovation_kg))


def _kalman_forward(
    first_weight_kg: float, later_observations: Sequence[float | None]
) -> _ForwardPass:
    """Forward filter over the daily grid; the first grid day always has an observation
    (grid starts at the first entry day), so it arrives as a plain float by construction.

    Diffuse-prior initialisation: the first observation is taken as the state,
    with the diffuse-limit filtered variance R (day-0 predicted slots are
    placeholders, never read by the backward pass).
    """
    filtered_means, filtered_variances = [first_weight_kg], [R_KG2]
    predicted_means, predicted_variances = [first_weight_kg], [R_KG2]
    for observed_kg in later_observations:
        prior_mean = filtered_means[-1]
        prior_variance = filtered_variances[-1] + Q_KG2
        predicted_means.append(prior_mean)
        predicted_variances.append(prior_variance)
        posterior_mean, posterior_variance = _observation_update(
            prior_mean, prior_variance, observed_kg
        )
        filtered_means.append(posterior_mean)
        filtered_variances.append(posterior_variance)
    return _ForwardPass(
        filtered_means=tuple(filtered_means),
        filtered_variances=tuple(filtered_variances),
        predicted_means=tuple(predicted_means),
        predicted_variances=tuple(predicted_variances),
    )


def _observation_update(
    prior_mean: float, prior_variance: float, observed_kg: float | None
) -> tuple[float, float]:
    """One Kalman update; a missing day is a predict-only step (no interpolation)."""
    if observed_kg is None:
        return prior_mean, prior_variance
    innovation = _huber_clip(observed_kg - prior_mean)
    gain = prior_variance / (prior_variance + R_KG2)
    return prior_mean + gain * innovation, (1.0 - gain) * prior_variance


def _rts_backward(forward: _ForwardPass) -> list[float]:
    """Rauch-Tung-Striebel backward pass yielding the smoothed means."""
    smoothed_means = [forward.filtered_means[-1]]
    for day_index in range(len(forward.filtered_means) - 2, -1, -1):
        smoother_gain = (
            forward.filtered_variances[day_index] / forward.predicted_variances[day_index + 1]
        )
        smoothed_means.append(
            forward.filtered_means[day_index]
            + smoother_gain * (smoothed_means[-1] - forward.predicted_means[day_index + 1])
        )
    smoothed_means.reverse()
    return smoothed_means
