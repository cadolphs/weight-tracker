# RED Classification — y-axis-floor (DISTILL fail-for-the-right-reason gate)

Run: `RED_GATE_ALL=1 uv run pytest tests/weight-trend-tracker/acceptance/steps/test_milestone_11.py -q` — 2026-09-04.
Result: **12 RED / 1 GREEN-preserved / 0 BROKEN** (13 scenario executions; 13 titles, no
outlines). Handoff to DELIVER unblocked.

Every RED fails on an `AssertionError` naming the one missing behavior — the read carries
no `y_range` — raised at the FIRST axis clause of its scenario, after every shipped clause
before it (the gap read, the first-log invite) has already passed. No import error, no
fixture fault, no setup failure. One authoring defect was found before the first gate run
and fixed: the gap scenario had been drafted with a "struck from his record" step, but
entry deletion is out of scope and the product has no such path — the gap is now seeded
as six mornings around an absent day with the shipped record vocabulary.

Two mechanical guards were run beside the gate:

1. **Wrong-GREEN guard.** A scratch pytest plugin (never touching `src/`) injected the
   test-side oracle's band into every read; all 13 scenarios went green under it, so no
   clause is mis-specified against the pinned rule (a real 0.4 kg/wk loss covers 47 % of
   its band; a stalled month 0.2 %; the steady week yields exactly 76.0…78.0).
2. **Seed calibration.** Every pinned bound was recomputed from the production series
   (`trend_series_in` / `entries_in_window`, shipped code) through the oracle before the
   scenario was written — the numbers in the feature file are what the rule yields for
   what the harness actually seeds, not the DISCUSS prose transcribed.

The single GREEN-preserved scenario is the honest signature of this feature: DISCUSS D2 and
DESIGN D-32 pin it as a presentation delta on a **shipped** series — the values a lens plots
are byte-identical before and after (G-3), so the guard that pins that must already pass.
Every genuinely new commitment — the floor, the ordinary-range formula, the outward snap,
the null-on-empty answer, lens/scale invariance — has its own RED anchor.

## milestone-11-honest-axis.feature

| Scenario | Classification | First missing behavior |
|---|---|---|
| A stalled month reads flat | MISSING_FUNCTIONALITY | `/trend?scale=1M` carries no `y_range` (expected `[76.0, 78.5]`; trend 77.196…77.202) |
| A real month of loss still slopes | MISSING_FUNCTIONALITY | `/trend?scale=1M` carries no `y_range` (expected a 2.5 kg band the line crosses 47 % of) |
| A long window keeps its ordinary range, with clean edges | MISSING_FUNCTIONALITY | `/trend?scale=6M` carries no `y_range` (expected the padded range snapped: `[76.5, 82.5]`) |
| A raw week is noise inside a band | MISSING_FUNCTIONALITY | `/entries?scale=1W` carries no `y_range` (expected `[76.0, 78.5]`) |
| A missing day stays a gap beneath the honest axis | MISSING_FUNCTIONALITY | the gap clause (shipped) passes; `/entries?scale=1W` then carries no `y_range` |
| Toggling lens or scale never changes the rule | MISSING_FUNCTIONALITY | the first stop of the tour (`/trend?scale=1W`) carries no `y_range`; every page tap already keeps its selection |
| Axis bounds are clean numbers | MISSING_FUNCTIONALITY | `/entries?scale=1W` carries no `y_range` (expected `[76.0, 78.5]` from midpoint 77.25) |
| A lone entry still stands on an honest axis | MISSING_FUNCTIONALITY | `/entries?scale=1W` carries no `y_range` (expected `[76.0, 78.5]` around 77.2) |
| A perfectly steady week is a flat line, never a zero-height axis | MISSING_FUNCTIONALITY | `/trend?scale=1W` carries no `y_range` (expected exactly `[76.0, 78.0]`) |
| An empty window offers no axis | MISSING_FUNCTIONALITY | the empty-window clause (shipped) passes; the read carries no `y_range` at all — an empty window must answer `null` explicitly |
| An empty record invites, and offers no axis | MISSING_FUNCTIONALITY | the invite (shipped) passes; the read carries no `y_range` at all |
| Exactly two kilograms of movement is where the floor steps aside | MISSING_FUNCTIONALITY | `/entries?scale=1W` carries no `y_range` (expected `[75.5, 78.5]` — the ordinary branch, not the floor's `[76.0, 78.0]`) |
| The axis frames the line and never moves it | **GREEN (preserved-behavior guard)** | the served 1M trend already equals the shipped pure series and reloads identically; guards G-3 through the enrichment |

## Suite integrity

- Full suite (non-gate mode): **219 passed, 13 skipped (@pending)** — pass count unchanged
  from the orchestrator's baseline (219 passed) before this feature's test infrastructure
  was added.
- **No inherited-AT renegotiation.** No shipped scenario, step or property asserts the exact
  key set of the `/entries` or `/trend` body (verified by grep: every reader indexes by key),
  so the additive `y_range` key breaks nothing; the shipped series/window/gap/palette
  scenarios stay green unchanged.
- **Zero production scaffolds (Mandate 7 satisfied structurally).** The oracle
  `expected_range` lives on the test side (`steps/composition.py`), deliberately NOT
  importing `weight_tracker.core.axis` — that module is DELIVER's to build, and an import
  here would have turned every RED into a BROKEN.
