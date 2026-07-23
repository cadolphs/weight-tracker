# Slice 01: glanceable-trend

**Goal**: The entry screen answers "where am I and which way am I moving" in one glance — `Trend: 82.3 kg · ↓0.25 kg/week` — and refreshes that answer in place the moment today's weight is saved, without costing the five-second entry anything.

**Stories**: US-007 (user-visible value). Slice composition gate satisfied (1/1 stories user-visible).

## IN

- Trend value + weekly rate line on the entry screen (`/`), visible without scrolling with the keypad open
- In-place refresh of the line after a successful save (inline; no reload) — including first appearance after the very first entry
- Precision/glyph rules: 0.1 kg trend (A9); 0.05 kg/week rate, ↓/↑/→ neutral glyphs (A10)
- Sparse honesty: rate only when record spans ≥7 days; value from first entry; nothing at 0 entries (A11)
- Graceful degradation: trend lookup failure → absent line, entry/save unaffected (A12)
- Glance telemetry event, counted separately from `trend.view.opened` (A13, KPI-3 integrity)

## OUT

- Rate derivation method and read-surface shape (DESIGN decides: Kalman state vs. endpoint differencing; new port op vs. shell derivation)
- Rate on the graph page; goal lines; predictions; direction color-coding
- Any change to save semantics, validation, or the graph views

## Learning Hypothesis

Disproves "ambient trend display makes the morning verdict effortless without taxing entry" if — over a week of real mornings — KPI-1 entry speed degrades (median >5 s or interactive >2 s), or the glance proves noise (Clemens still opens the graph every morning purely to get the same answer, or finds the line clutter on the five-second screen). Substitution on KPI-3 (fewer deliberate graph opens) is expected, not disproof.

## Acceptance Criteria

- US-007 scenarios 1–7 green (glance, post-save refresh, neutral gain display, young-record no-rate, empty record, entry-primacy @property, KPI-counter separation)
- Home glance value equals the graph trend line for the same entry set (shared-artifact checkpoint, journey step 1 ↔ step 3)
- Dogfood: next real morning entry shows the glance and its post-save refresh on the phone

## Dependencies

`weight-trend-tracker` slices 01–05 (all delivered 2026-07-23): `TrendProjection` (ADR-004 Kalman+RTS), inline save flow, telemetry trail, production pipeline. No external dependencies. DESIGN: rate derivation + KPI-3 separation mechanism.

## Effort / Reference Class

~0.5–1 day. Reference class: prior slices took ~0.5–1 day each; this one is smaller than most (one read surface, one template line, one telemetry event; no new algorithm — trend already computed per read).

## Slice Taste Tests

| Test | Verdict |
|---|---|
| 1. End-to-end vertical (store → trend projection → rendered glance + post-save refresh) | PASS |
| 2. User-visible value, demoable same day | PASS |
| 3. ≤1 day effort | PASS |
| 4. Production data + same-day dogfood moment | PASS (next real morning entry) |
| 5. Named, falsifiable learning hypothesis | PASS |
