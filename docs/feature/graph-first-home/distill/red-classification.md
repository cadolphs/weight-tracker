# RED Classification — graph-first-home (DISTILL fail-for-the-right-reason gate)

Run: `RED_GATE_ALL=1 pytest tests/weight-trend-tracker/acceptance/steps/test_milestone_8.py test_milestone_9.py` — 2026-07-24.
Result: **18 RED / 1 GREEN-preserved / 0 BROKEN**. Handoff to DELIVER unblocked.

Two wrong-RED defects were found by the first gate run and fixed before this classification
(step-ordering bug in the hiccup scenario; a JSON-shaped invite oracle reused against an HTML
page → `JSONDecodeError` BROKEN). Both scenarios now fail on missing functionality only.

## milestone-8-graph-first-front-page.feature

| Scenario | Classification | Failing assertion (first missing behavior) |
|---|---|---|
| The morning opens on the whole picture | MISSING_FUNCTIONALITY | no `#home-graph` mount on `/` |
| An ambient morning never counts as deliberate study | MISSING_FUNCTIONALITY | `/stats` lacks `trend_study_this_week` |
| Choosing a lens or scale is deliberate study | MISSING_FUNCTIONALITY | beacon `POST /telemetry/trend-study` → 404 |
| Saving repaints the morning picture in place | MISSING_FUNCTIONALITY | save response lacks `recent` (D-19) |
| A graph hiccup never blocks the log | MISSING_FUNCTIONALITY | `/stats` lacks `home_graph_shown_this_week` (KPI-7); save/entry clauses already hold (preserved behavior) |
| An empty record keeps the front page simple | **GREEN (preserved-behavior guard)** | asserts absence of graph area/list on an empty record — true today by construction, guards the empty-state rule once the graph ships. Deliberately not RED. |
| The graph never taxes the entry | MISSING_FUNCTIONALITY | no `#home-graph` mount (timing + typing clauses already hold) |
| The last week of numbers is one look away | MISSING_FUNCTIONALITY | no `#recent-entries` list |
| Today's save goes straight to the top | MISSING_FUNCTIONALITY | no `#recent-entries` list (fails in the Given that pins the pre-save list state — still an assertion on unbuilt behavior) |
| A young record shows what it has | MISSING_FUNCTIONALITY | no `#recent-entries` list |
| Looking is not touching | MISSING_FUNCTIONALITY | no `#recent-entries` list |
| A garbled study signal is turned away without a mark | MISSING_FUNCTIONALITY | beacon route absent → 404, expected 400 |
| A stranger's study signal leaves no mark | MISSING_FUNCTIONALITY | `/stats` lacks `trend_study_this_week` (the "no mark" oracle requires the counter to exist) |

## milestone-9-whole-record-history.feature

| Scenario | Classification | Failing assertion |
|---|---|---|
| History leads to the whole record | MISSING_FUNCTIONALITY | no `#history-entries` list on `/graph` |
| The list and the plot tell the same story | MISSING_FUNCTIONALITY | no `#history-entries` list |
| Deliberate study is counted where it happens | MISSING_FUNCTIONALITY | `/stats` lacks `trend_study_this_week` |
| Old bookmarks still work | MISSING_FUNCTIONALITY | no `#history-entries` list (deep-link lens/scale clauses already hold) |
| An empty record still invites | MISSING_FUNCTIONALITY | `/stats` lacks `trend_study_this_week` (invite + no-list clauses preserved) |
| The full record arrives without a wait | MISSING_FUNCTIONALITY | no `#history-entries` list (≤2 s clause measured and holding) |

## Suite integrity

- Full suite (non-gate mode): **134 passed, 19 skipped (@pending)** — the consciously amended
  G-5 clause ("every moving part on the morning screen is the tracker's own") is green
  before DELIVER and stays green after (sanctioned-set form, ADR-008 disclosure).
- Pinned inherited-AT amendment for DELIVER (ADR-009 step): milestone-6
  "The stats page still tells deliberate study from ambient glances" — redirect
  `GlanceService.study_trend` to History-page opens and read the deliberate counter
  (`trend_study_this_week`); scenario wording unchanged. Noted in the feature file.
