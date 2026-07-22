# Slice 03: backfill-and-correct

**Goal**: Add entries for missed past days and correct mistyped values in place, keeping the record trustworthy.

**Stories**: US-003 (user-visible value). Slice composition gate satisfied.

## IN

- Select any past date (from history list or date picker); add or replace its value
- Same validation as today-entry (range, precision, one-per-day)
- Future dates rejected with clear message
- Raw graph reflects changes immediately

## OUT

- Entry deletion (A7 — edit covers corrections)
- Automated import from old app (OQ-2)
- Trend recomputation display (lands with Slice 04; store-side correctness ensured here)

## Learning Hypothesis

Disproves "maintaining an accurate record is painless" if backfilling a forgotten day or fixing a typo takes more than ~15 s.

## Acceptance Criteria

- US-003 scenarios 1–4 green (backfill Sunday, correct 15 Jul typo, future rejected, past-day validation)
- One-entry-per-day invariant holds for all dates
- Dogfood: Clemens backfills or corrects at least one real day the day this ships

## Dependencies

Slice 01 (`WeightLogging` write path), Slice 02 (graph shows the effect). Ordering relative to Slice 04 is free — the trend does not depend on backfilled history.

## Effort / Reference Class

~0.5–1 day. Reference class: extending an existing form/write path with a date dimension — low uncertainty.

## Slice Taste Tests

| Test | Verdict |
|---|---|
| 1. End-to-end vertical (date pick → rule → store → graph update) | PASS |
| 2. User-visible value, demoable same day | PASS |
| 3. ≤1 day effort | PASS |
| 4. Production data + same-day dogfood moment | PASS (real backfills + history seeding) |
| 5. Named, falsifiable learning hypothesis | PASS |

## Changed Assumptions

- **Original (DISCUSS)**: Goal/hypothesis/dogfood AC referenced "enabling manual seeding of history from the old app before the trend ships", "hand-seeding ~30 days of old-app history is too tedious … (which would revive OQ-2 import)", and "Dogfood: … hand-copies ≥30 days of old-app history the day this ships (production data seeding for Slice 04)".
- **Now (DISTILL amendment, 2026-07-22)**: OQ-2 resolution — no old-app import and no hand-seeding pressure. Seeding ACs removed; backfill/edit remains in scope as a stated requirement; slice ordering is free (Slice 04 may ship before Slice 03); the trend validates on freshly accumulated production data.
- **Rationale**: OQ-2 resolution, `feature-delta.md` § Resolutions + § Changed Assumptions (DESIGN), 2026-07-22.
