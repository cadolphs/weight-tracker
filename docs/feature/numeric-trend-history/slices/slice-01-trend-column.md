# Slice 01 — Trend column: the trend has a readable history

**Feature**: numeric-trend-history · **Stories**: US-016 · **Priority**: Must

## Goal

Both entries lists show each entry's smoothed trend weight beside its raw weight in aligned columns, so a plateau or a real month of loss can be read as numbers and subtracted, instead of estimated off a curve.

## IN scope

- One row definition, three renderers (D7, A38): `Date | Raw | Trend`, newest first, on `/` (last 7 entries) and `/graph` (the complete record), plus the client-side post-save repaint. No second wording, no second precision rule, no second trend lookup.
- The trend value is `trend_series(all_entries)` at the row's own day — full-record smoothing, derived never stored (ADR-004, D8/A32). The lookup is total: every entry day is on the grid.
- Semantic table with a header row (`<th scope="col">`), `kg` stated once per weight column, ids `#recent-entries` / `#history-entries` kept (D9). Numbers right-aligned on tabular figures; no horizontal scroll at 360 px; AA contrast both schemes (ADR-007 tokens only).
- Both weight columns at 0.1 kg (D10/A35). A day's trend value reads identically on the glance line, both lists and the chart (A36).
- Entry-based rows, gaps absent (A33); the History table is never windowed by the chart's scale (A34); lists stay display-only (A39).
- Degrade to absent (D12/A37): a failing trend projection empties the trend cells only — raw column intact, entry and save untouched.
- Post-save in-place repaint from the save response, including revised trend values for the rows above a backfill (D11).

## OUT scope

Delta/change columns; sorting, filtering, paging, search; per-row affordances (edit, delete, links); export; per-row weekly rate; trend algorithm, parameters or windowing; the chart, the y-axis rule (US-015), the glance line's wording, `/stats`; a Raw/Trend toggle over the lists (explicitly rejected, D6); import; auth.

## Learning hypothesis

**Disproves, if it fails**: that 0.1 kg is a useful precision for a *smoothed* series read day by day — if a week of rows prints the same digits seven times while the curve visibly slopes, the precision default (OQ-15) is wrong and must be retuned before the column is trusted. It also disproves that numbers beat the picture at all: if the dogfood mornings still end in a tap through to `/graph` to answer "how much has it moved", the column is decoration and the real gap is elsewhere.
**Confirms, if it succeeds**: the noise-vs-signal judgment (`js-2-judge`) can be settled by subtraction on the surface the user is already on, with one pure lookup and no new fetch, script or tap.

## Acceptance criteria (summary — full G/W/T in feature-delta.md)

1. Noisy week: raw column spans ≥0.7 kg while the trend column spans ≤0.3 kg; every trend value equals the smoothed series for that day.
2. Top row's trend cell equals the glance line above it, and the same day on `/graph` (A36).
3. History table lists the whole record at every scale; tapping 1W changes the chart only.
4. Days with no entry produce no row; no row is half-filled.
5. Backfilling a past day repaints the front-page list in place — new row present, rows above revised, no reload.
6. A failing trend projection leaves both lists rendering raw values with empty trend cells; entry and save unaffected.
7. @property: header row names Date/Raw/Trend with kg once per weight column; numerals right-aligned and tabular; no wrap, truncation or horizontal scroll at 360 px; AA contrast in both schemes.

## Dependencies

All delivered ✅: smoothed series (weight-trend-tracker, ADR-004), recent list (US-011), complete record list (US-012), save-response repaint (D-19), calm theme tokens (US-009). No pre-slice SPIKE — the uncertainty is the precision's taste, and dogfood answers it next morning.

## Effort & reference class

~0.5 day. Reference: US-012 (complete record list) landed well under a day; this adds one pure day→trend projection and one column to that same rendering. The larger share of the diff is the existing acceptance tests and two CSS rules that assert the old single-string row grammar — an intended AC delta, enumerated in feature-delta.md Pre-Requisites (b).

## Dogfood moment

Next morning after deploy: read the seven trend values on `/` over the real ~77 kg plateau and judge whether the week reads as movement or noise without opening the chart; then on `/graph` subtract two trend values a month apart. Production data by definition; self-report feeds KPI-10.
