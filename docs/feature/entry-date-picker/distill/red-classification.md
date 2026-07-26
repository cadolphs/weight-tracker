# RED Classification — entry-date-picker (DISTILL fail-for-the-right-reason gate)

Run: `RED_GATE_ALL=1 pytest tests/weight-trend-tracker/acceptance/steps/test_milestone_10.py` — 2026-07-24.
Result: **9 RED / 5 GREEN-preserved / 0 BROKEN** (14 scenario executions; 13 titles, one a
2-example outline). Handoff to DELIVER unblocked.

Every RED fails on an `AssertionError` naming a missing behavior — no import error, no fixture
fault, no setup failure. Two authoring defects were found by the first gate run and fixed before
this classification:

1. **Scenario-frame contradiction** — "A slow repair never slows the morning record" backfilled
   19 July while `he has logged timed entries every morning for the last week` had already seeded
   it (the timed week ends on today, 24 July). The gap day moved to 10 July. Wrong-RED, caught.
2. **Capture-shadowing** — the trail snapshot originally demanded the KPI-8 counter at capture
   time, so 8 of 13 scenarios failed at their `When` step instead of at their own headline
   assertion (a masked, uninformative RED). The snapshot is now tolerant (`None` when the counter
   is absent) and the repair-count assertions demand it explicitly, so each scenario now fails at
   the first thing IT is about.

The GREEN-preserved count is high by design and is the honest signature of this feature: DISCUSS
D2 pinned it as a **presentation delta on a shipped backend** (`POST /entries` has accepted any
valid past date, upserted one-per-day, and refreshed glance/recent/curve since
`weight-trend-tracker` / `graph-first-home`). Those scenarios are the regression guards proving
the shipped save path serves the new journey unchanged; every genuinely new commitment — the date
row, the whole-record map, the single hint node, write-time classification, KPI-1 purity, KPI-8 —
has its own RED anchor.

## milestone-10-dated-entry.feature

| Scenario | Classification | First missing behavior |
|---|---|---|
| A forgotten day is backfilled from the entry screen | **GREEN (preserved-behavior guard)** | the save path already backfills, confirms, hands back `recent`+`glance`, and recomputes the trend; guards that a backdated save keeps doing so once the date row ships |
| The morning flow never pays for the picker | MISSING_FUNCTIONALITY | no `#entry-date` row on `/` (readiness + focus clauses already hold) |
| The picker cannot wander off before the record began | MISSING_FUNCTIONALITY | no `#entry-date` row → no server-supplied `min` (first entry − 1 year, OQ-11) |
| The future stays closed however the phone frames its day | MISSING_FUNCTIONALITY | `/stats` lacks `backdated_saves_this_week` (the "trail untouched" oracle needs the counter to exist); the rejection + nothing-stored clauses already hold |
| A slow repair never slows the morning record | MISSING_FUNCTIONALITY | **the live bug the feature exists to prevent**: `telemetry.speed_sample_count: 7 → 8` — a 22-second backfill is currently counted as a morning |
| A morning still counts as a morning | MISSING_FUNCTIONALITY | `/stats` lacks `backdated_saves_this_week` (the converse guard: withholding timings from *every* save must fail too) |
| A phone that will not say which day it is on is still served (2 examples) | **GREEN ×2 (preserved-behavior guard)** | an unknown `today` key is ignored today; guards that the additive claim never becomes a 400 — a telemetry concern must never cost an entry |
| Any day of the record answers the picker | MISSING_FUNCTIONALITY | the embedded map answers `None` for 3 Mar 2026 (shipped map is the latest four entries) |
| A gap is offered as a gap, never as a value | **GREEN (preserved-behavior guard)** | a day without an entry is already absent from the map; guards the no-blind-overwrite rule once the map widens |
| A mistyped past day is corrected in place | **GREEN (preserved-behavior guard)** | the one-per-day upsert already corrects in place and refreshes; guards it for the picker journey |
| Correcting a timed morning leaves the week's mornings intact | MISSING_FUNCTIONALITY | `/stats` lacks `backdated_saves_this_week`; this is also the R-2 guard (the correction NULLs `entries.entry_ms`, so the trail must remain KPI-1's source of truth) |
| One hint line serves the anchor and the repair alike | MISSING_FUNCTIONALITY | no `#entry-hint` node (the screen carries 0; today's `#yesterday-reference` is removed from the DOM by the client) |
| An empty record still opens straight into typing | MISSING_FUNCTIONALITY | no `#entry-date` row on an empty record |

## Suite integrity

- Full suite (non-gate mode): **165 passed, 14 skipped (@pending)** — unchanged pass count
  before and after the harness renegotiations below.
- **Renegotiation A (map const, R-1a)** — `RECORD_WEIGHTS_MAP` (`const recordWeights`) is read
  first, with the shipped `RECENT_WEIGHTS_MAP` (`const recentWeights`) kept as a fallback and the
  server-rendered paragraph beneath it. Green before AND after the rename; a page carrying neither
  still fails on the missing VALUE, never on a missing marker.
- **Renegotiation B (timed-morning seeding — found at DISTILL, not listed in DESIGN R-1)** —
  `seed_timed_week` now walks the clock and each save claims its own day, because a morning IS a
  same-day save. Under ADR-011's write-time classification, seeding a whole week in one instant
  would be indistinguishable from seven repairs and would strip six of seven timings out of the
  KPI-1 report. It fails LOUDLY (milestone-5 asserts `sample_count == 7`), never silently — and
  is fixed here, before DELIVER, rather than being discovered as a mystery red.
- **Renegotiation C (entry readiness, R-1c) — resolved differently from DESIGN's suggestion.**
  DESIGN proposed extending the shared `assert_ready_for_typing`; that would red a dozen shipped
  scenarios for the whole of DELIVER. The readiness guarantee is instead extended by a NEW
  `@pending` scenario ("The morning flow never pays for the picker") that composes the shipped
  readiness assertion with the date-row and focus clauses. Shipped scenarios stay green; the new
  guarantee is still pinned. Recorded, never silent.
