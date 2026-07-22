# Slice 02: raw-history-graph

**Goal**: See the raw weight record as a phone-legible graph with selectable time scales (1W / 1M / 3M / 6M / 1Y / All), with missing days shown honestly as gaps.

**Stories**: US-002 (user-visible value). Slice composition gate satisfied.

## IN

- Graph view of raw entries, kg axis auto-ranged to visible data
- Time-scale selector: 1W / 1M / 3M / 6M / 1Y / All (A3)
- Gap-honest rendering: no zeros, no interpolated raw points
- Empty state inviting first log
- Mobile legibility; interactive ≤2 s on phone

## OUT

- Trend line and Trend↔Raw toggle (Slice 04)
- Past-day editing from the graph (Slice 03)
- Zoom/pan gestures, hover tooltips beyond basics

## Learning Hypothesis

Disproves "a raw-history graph is readable and useful on a phone screen" if, with Clemens's real entries, the plot is illegible at mobile viewport or takes >2 s to become interactive.

## Acceptance Criteria

- US-002 scenarios 1–4 green (3M window, All span, vacation gap, phone-usable @property)
- Exactly the stored entries plotted; `weight_entry` consistency with the list view (shared-artifact check)
- Dogfood: Clemens reviews his real production entries on the graph the day it ships

## Dependencies

Slice 01 (entries exist; `WeightHistory` read path).

## Effort / Reference Class

~1 day. Reference class: chart rendering integration over an existing read model — moderate, main unknown is mobile legibility tuning.

## Slice Taste Tests

| Test | Verdict |
|---|---|
| 1. End-to-end vertical (store → query → rendered graph) | PASS |
| 2. User-visible value, demoable same day | PASS |
| 3. ≤1 day effort | PASS |
| 4. Production data + same-day dogfood moment | PASS (reviews own real entries) |
| 5. Named, falsifiable learning hypothesis | PASS |
