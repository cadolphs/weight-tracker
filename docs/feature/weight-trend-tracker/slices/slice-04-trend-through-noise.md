# Slice 04: trend-through-noise

**Goal**: Show a smoothed trend line that absorbs daily noise, survives gaps, and tracks real change — with a one-tap Trend↔Raw toggle. This is the differentiating value and the riskiest assumption of the product.

**Stories**: US-004 (trend, user-visible value) + US-005 (toggle, user-visible value). Slice composition gate satisfied.

## IN

- Trend line over the selected time scale; default view = Trend (A4)
- Behavioral guarantees: +1.5 kg one-day spike moves trend ≤0.3 kg; ≤7-day gaps cause no discontinuity; sustained 0.5 kg/week change visible within 7 days; deterministic
- Corrections/backfills recompute the trend over the affected range
- Trend↔Raw toggle preserving `selected_time_scale`

## OUT

- Algorithm choice/tuning documentation (DESIGN owns the selection against the ACs)
- Goal lines, predictions, rate-of-change annotations
- Persisting toggle choice across sessions (defaults to Trend each open)

## Learning Hypothesis

Disproves "a smoothed trend can be trusted on real, gappy data" if — on the freshly accumulated production history (plus any real backfills) — the trend visibly jumps at gaps, chases single-day spikes, or hides a known real change; failure here invalidates the product's core reason to exist over a spreadsheet. The trend is available and judgeable from the first entry; confidence grows as the record does.

## Acceptance Criteria

- US-004 scenarios 1–5 green (sushi spike, vacation gap, real decline, correction recompute, determinism @property)
- US-005 scenarios 1–3 green (toggle preserves window, lossless round trip, Trend default)
- Dogfood: Clemens judges his real trend on freshly accumulated production entries the day this ships

## Dependencies

Slice 02 (graph substrate). Slice 03 is NOT a dependency — ordering is free and this slice may ship before backfill; the trend validates on fresh data. DESIGN: smoothing algorithm satisfying the behavioral ACs (ADR-004: Kalman+RTS, fixed parameters).

## Effort / Reference Class

~1 day. Reference class: time-series derivation + chart overlay + view toggle — moderate; risk concentrated in meeting the quantified smoothness/gap thresholds (bounded by DESIGN pre-selecting the algorithm).

## Slice Taste Tests

| Test | Verdict |
|---|---|
| 1. End-to-end vertical (store → trend projection → rendered overlay + toggle) | PASS |
| 2. User-visible value, demoable same day | PASS |
| 3. ≤1 day effort | PASS (algorithm pre-decided in DESIGN) |
| 4. Production data + same-day dogfood moment | PASS (real seeded history) |
| 5. Named, falsifiable learning hypothesis | PASS (riskiest assumption) |

## Changed Assumptions

- **Original (DISCUSS)**: Learning hypothesis relied on "the ≥30 days of seeded production history from Slice 03"; Dependencies listed "Slice 03 (seeded real history — makes the hypothesis testable now, not in a month)"; dogfood AC referenced "seeded history + fresh entries".
- **Now (DISTILL amendment, 2026-07-22)**: OQ-2 resolution voids the seeding rationale. Slice ordering is free — the trend may precede backfill and validates on freshly accumulated production data (it is available from the first entry per US-004 AC). Trend determinism oracle framed as "fixed entry set → identical trend line"; retrospective revision when entries change is BY DESIGN (smoothed display, ADR-004). Gap oracle asserts smoothed continuity of the CURRENT line across gaps (bounded step, no kink), not immutability of previously rendered values.
- **Rationale**: OQ-2 resolution + ADR-004 consequences, `feature-delta.md` § Resolutions + § Changed Assumptions (DESIGN), 2026-07-22.
