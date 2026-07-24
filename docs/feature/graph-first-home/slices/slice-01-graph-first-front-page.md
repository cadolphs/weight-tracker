# Slice 01: graph-first-front-page

**Goal**: The front page opens on the whole picture — trend curve with full lens + scale controls above the entry form, glance line kept, last-7 entries below — without costing the five-second entry anything, and without polluting the deliberate trend-study counter.

**Stories**: US-010, US-011 (both user-visible value). Slice composition gate satisfied (2/2 stories user-visible).

## IN

- Graph on `/` above the entry form: Trend/Raw lens toggle + 1W/1M/3M/6M/1Y/All scale picker, defaults Trend at 3M (A17); same series and lens/scale behavior as `/graph`
- Entry primacy held: autofocus + decimal keypad + interactive ≤2 s unchanged; keypad-covers-graph accepted (D6); graph/list load never delays input readiness; degrade-to-absent (A15)
- **KPI-3 purity mechanism**: ambient renders (open at defaults, post-save refresh) add 0 to the deliberate counter; explicit lens/scale taps count as deliberate (A19); ambient presence recorded as its own event (KPI-7)
- In-place refresh after save: graph + glance line + recent list (A15)
- Last-7-entries list below the form: reverse-chronological, date + kg, display-only, gaps absent, <7 → shorter, 0 → none (A18, D9)
- Glance line kept as today (A14)
- Calm-theme compliance for new elements (both schemes AA, ≥44 px targets, zero new external origins)

## OUT

- Combined History page / complete entries list (slice 02)
- Any change to `/graph` (History still points there, unchanged, until slice 02)
- Editing from the list (D9); scale/lens persistence across surfaces (A17); glance-line removal (OQ-7)
- Telemetry event naming and graph-delivery mechanism (DESIGN)

## Learning Hypothesis

Disproves "the graph belongs above the entry form" (locked D6/D7) if — over a week of real mornings — KPI-1 degrades (median >5 s or interactive >2 s), or the keypad-covered graph proves so annoying that Clemens stops glancing at it (KPI-7 presence irrelevant because he scrolls past), or the screen feels cluttered enough to tax the habit (KPI-2 dip). Substitution on KPI-3 (fewer deliberate opens) is expected, not disproof.

## Acceptance Criteria

- US-010 scenarios 1–7 green (graph-above-form, ambient-never-counts, deliberate-interaction, in-place refresh, degrade, empty record, entry-primacy @property)
- US-011 scenarios 1–4 green (last-7 list, save-to-top refresh, young/empty record, display-only)
- Front-page graph renders the same trend/raw data as `/graph` for the same entry set (shared-artifact checkpoint, journey step 1 ↔ steps 2–3)
- /stats check: a log-only morning adds 0 to the deliberate trend-study count; ambient event present
- calm-visual-theme ATs pass with the **consciously amended** G-5 script clause (no silent breakage)
- Dogfood: next real morning entry logged on the graph-first front page on the phone

## Dependencies

`weight-trend-tracker` slices 01–05, `home-trend-display` slice 01, `calm-visual-theme` slices 01–02 (all delivered 2026-07-23): uPlot + token theming, TrendProjection, inline save flow, device-day read framing, telemetry trail, pipeline. DESIGN: ambient/deliberate telemetry mechanism + graph delivery within ≤2 s. DISTILL: G-5 clause renegotiation.

## Effort / Reference Class

~1 day (US-010 ~0.5–1 d + US-011 ~0.25–0.5 d, heavily shared substrate: the graph JS, series reads, and list data all exist). Reference class: prior slices ~0.5–1 day each; this is the largest since slice-04 but ships zero new algorithms or ports.

## Slice Taste Tests

| Test | Verdict |
|---|---|
| 1. End-to-end vertical (store → projections → rendered front page + in-place refresh + telemetry separation) | PASS |
| 2. User-visible value, demoable same day | PASS |
| 3. ≤1 day effort | PASS (tight; all substrate shipped) |
| 4. Production data + same-day dogfood moment | PASS (next real morning entry) |
| 5. Named, falsifiable learning hypothesis | PASS |
| No new abstraction before use; list idiom ships here, slice 02 consumes it | PASS |
