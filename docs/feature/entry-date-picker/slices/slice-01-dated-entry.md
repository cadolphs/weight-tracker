# Slice 01 — Dated entry: backfill and correct on the entry screen

**Feature**: entry-date-picker · **Stories**: US-013, US-014 · **Priority**: Must

## Goal

The entry screen gains a native date field defaulting to today, so any past day can be backfilled or corrected in place without taxing the five-second morning log.

## IN scope

- Native `<input type="date">` above the weight field, prefilled device-local today, `max` = device-local today (A20), themed per calm-visual rules (AA both schemes).
- Save submits the selected date (replaces the hardcoded `deviceLocalDay()` payload); confirmation names the saved date.
- Post-save reset: date → device today, weight field cleared (D8).
- Edit prefill: past day with entry → stored value + `Editing {day} — was {v} kg`; without entry → empty field + `No entry for {day} yet`; single hint line shared with the yesterday anchor (D7, A21). Correct for any stored day (A24); degrade-to-absent on lookup failure.
- In-place refresh after backdated saves via the existing save-response mechanism (A22).
- KPI-1 sample purity: backdated saves contribute 0 entry-speed samples; backdated marker readable on /stats for KPI-8 (A23).
- Conscious renegotiation of entry-screen ATs asserting the hardcoded device-day submission (DISTILL).

## OUT scope

Entry deletion; tap-row-to-edit; bulk backfill; historical import; future-dated entries; changes to `/graph`, `/stats` presentation beyond the purity split, trend algorithm, auth; picker libraries.

## Learning hypothesis

**Disproves, if it fails**: that an always-visible date control can ride the entry screen without cost — i.e. if the first dogfood mornings show added taps, focus theft, slower interaction (>2 s), or KPI-1 median drift, the "native input, always visible" bet (D6) is wrong and a collapsed control (the rejected alternative) must be reconsidered.
**Confirms, if it succeeds**: the last journey moment (`js-3-maintain`) is served by one form-row delta — no admin surface, no edit mode, no separate flow.

## Acceptance criteria (summary — full G/W/T in feature-delta.md)

1. Default morning flow: zero date-row interactions, autofocus + keypad unchanged, interactive ≤2 s.
2. Backfill: pick past empty day → save → confirmation names the day; graph/glance/list include it; trend recomputes.
3. Edit: pick stored day → field prefills stored value with editing hint; save replaces (exactly one entry per day in list + graph).
4. Future date impossible from the picker (`max`) and rejected by the server (existing rule) when forged.
5. Post-save: date back on today, field cleared.
6. @property: backdated saves add 0 KPI-1 speed samples.

## Dependencies

All delivered ✅: date-accepting save + validation (weight-trend-tracker), recent-days map + device-day reads (fix-device-day-reads), save-response refresh (home-trend-display, graph-first-home), theme (calm-visual-theme). No pre-slice SPIKE — uncertainty is UX-taste, not mechanism, and dogfood answers it same-day.

## Effort & reference class

~0.5–1 day. Reference: US-006 (yesterday anchor, one form-row + map read) and US-011 (recent list + in-place repaint) each landed in ≤0.5 day; this slice is the two patterns combined on the same template.

## Dogfood moment

Same day as deploy: correct or backfill one real day on the phone (there is usually a candidate), then verify the next morning log feels identical. Production data by definition.
