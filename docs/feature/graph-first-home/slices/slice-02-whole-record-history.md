# Slice 02: whole-record-history

**Goal**: "History" keeps its promise — one deliberate tap opens the full-control graph with the complete numeric record beneath it, so any exact day and value in the record is auditable.

**Stories**: US-012 (user-visible value). Slice composition gate satisfied (1/1 stories user-visible).

## IN

- Complete entries list (all entries, newest first, date + kg at 0.1 precision) below the graph on the History destination (D8)
- Existing `/graph` behaviors preserved: lens toggle preserves scale, deep links `?view=`/`?scale=` unchanged, empty-invite at 0 entries, back-link to `/` (A16)
- History-page open counts as one deliberate trend-study session (A19 — KPI-3's new home)
- ≤2 s interactive with a ≥300-entry list (G-2 extended); gaps absent from list and plot alike
- Calm-theme compliance for the list in both schemes

## OUT

- Front-page changes (slice 01); pagination/search/filtering; editing from the list (D9); per-entry annotations; export
- Any change to the trend algorithm or windows

## Learning Hypothesis

Disproves "a single combined page serves the deliberate audit" if the complete list makes the page feel slow or unwieldy on the phone (interactive >2 s, or Clemens finds himself wanting search/pagination within the first week of real audits) — which would send us back toward a paged or separate record view.

## Acceptance Criteria

- US-012 scenarios 1–6 green (whole record, list-equals-plot, deliberate count, deep links, empty invite, ≤2 s @property)
- Shared-artifact checkpoint: listed values identical to plotted raw entries and to the front page's data for the same entry set
- /stats check: History open increments the deliberate trend-study count by exactly 1; ambient front-page mornings unaffected
- Dogfood: one real History-page audit on the phone the day it ships

## Dependencies

Slice 01 shipped first (entries-list presentation idiom to reuse; KPI-3 redefinition already live so the deliberate counter's meaning flips once, not twice). `weight-trend-tracker` slice 02 (`/graph`), `calm-visual-theme` slice 02 (graph theming) — delivered. DESIGN: A16 confirmation (extend `/graph` vs new route — deep links must keep working either way).

## Effort / Reference Class

~0.5–1 day. Reference class: prior slices ~0.5–1 day; this one is mostly one template + one read reuse (the raw-lens fetch already carries the entries).

## Slice Taste Tests

| Test | Verdict |
|---|---|
| 1. End-to-end vertical (store → history read → rendered combined page + deliberate telemetry) | PASS |
| 2. User-visible value, demoable same day | PASS |
| 3. ≤1 day effort | PASS |
| 4. Production data + same-day dogfood moment | PASS (real audit of the real record) |
| 5. Named, falsifiable learning hypothesis | PASS |
| Not a scale-duplicate of slice 01 (different surface, different moment: deliberate vs ambient) | PASS |
