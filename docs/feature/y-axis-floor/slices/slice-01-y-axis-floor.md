# Slice 01 — Y-axis floor: stalled progress looks stalled

**Feature**: y-axis-floor · **Stories**: US-015 · **Priority**: Must

## Goal

The shared chart engine guarantees a minimum visible y-span of 2.0 kg on both surfaces and both lenses, so a plateaued month reads as a calm, near-flat line instead of a rollercoaster of 200 g wobble — while steep or long windows look exactly as they do today.

## IN scope

- One range rule, one floor constant (2.0 kg, absolute, kg): plotted span ≥ 2.0 kg → pre-feature auto-range (A28); plotted span < 2.0 kg → [midpoint − 1.0, midpoint + 1.0], data centred, every point inside (D8, A27).
- Clean bounds (D9, A31): after either branch, both bounds snap OUTWARD to the 0.5 kg grid (`floor(lo/0.5)×0.5`, `ceil(hi/0.5)×0.5`) on every window, both lenses, both surfaces. Snapping only widens (floored band 2.0–3.0 kg, centre within 0.25 kg of the data midpoint); no bound ever carries more than one decimal.
- Plotted span = max − min of the values plotted for the current window and lens; gap nulls ignored (A26). Single-point and all-equal windows get a 2.0 kg axis, never zero-height.
- Parity by construction (D7, ADR-008): `/` (`#home-graph`) and `/graph` (`#graph-page`), Trend and Raw, every scale — lens/scale toggles preserve selection exactly as today and change data only, never the rule.
- Placement decided at DESIGN (A29): client-side range function in `graph.js`, or a pure core `floored_range` returned on `/entries` + `/trend` and consumed by the engine. Either way: series untouched (G-3), no new fetch/script/tap, no telemetry.
- Pad/snap order pinned at DESIGN: uPlot's default pad is bypassed when a range function is supplied; the auto-range branch decides explicitly whether to reproduce that pad before snapping; any pad is symmetric and only widens (D8/D9).

## OUT scope

Trend algorithm/parameters; configurable floor; shared y-range across lenses (OQ-13); x-axis; tooltips/hover; `/stats`/telemetry; import; deletion; auth.

## Learning hypothesis

**Disproves, if it fails**: that an *absolute* 2.0 kg floor is the right honesty constant across all scales — if the first dogfood mornings show a real 1M loss (~1 kg) looking flat, or 6M looking cramped, the constant (OQ-12) or the absolute-vs-relative choice (D6) is wrong and must be retuned before anything else is built on it — and that a 0.5 kg bound grid reads clean without feeling cramped (if the up-to-1.0 kg extra span blunts a 1M loss, or the edges still look arbitrary, the grid step (OQ-14) is wrong).
**Confirms, if it succeeds**: the noise-vs-signal judgment (`js-2-judge`) survives rendering with a one-line rule — no per-scale tuning, no second algorithm, no UI control.

## Acceptance criteria (summary — full G/W/T in feature-delta.md)

1. Stalled 1M trend (77.1–77.3 kg): axis 76.0–78.5, line ≤10 % of plot height, same on `/` and `/graph`.
2. Real 1M loss (78.4→77.4): axis 76.5–79.0, line descends through ~40 % of the height — clearly sloped.
3. Long 6M window (82.1→77.2, span 4.9): pre-feature auto-range snapped outward, 76.5–83.0; no floor widening.
4. Raw 1W (76.8–77.4): axis 76.0–78.5, all points inside, gaps stay gaps.
5. Toggling lens/scale never changes the rule; selection survives as today.
6. Clean bounds: smoothed values 77.15…77.32 (mid 77.235) → axis 76.0–78.5; every bound a multiple of 0.5 kg, never more than one decimal.
7. @property: for any window/lens/surface the y-span is ≥ 2.0 kg and contains every plotted value; both bounds are multiples of 0.5 kg; above the floor the range equals the pre-feature auto-range snapped outward; series values unchanged.

## Dependencies

All delivered ✅: shared engine + both mounts (graph-first-home, ADR-008), both lenses + scales (weight-trend-tracker), device-day windows (fix-device-day-reads), single palette (calm-visual-theme). No pre-slice SPIKE — the uncertainty is the constant's taste, and dogfood answers it next morning.

## Effort & reference class

~0.25–0.5 day. Reference: US-009 (single palette — one rule inside `graph.js`) landed in <0.5 day; a server-side placement adds one pure function plus one additive JSON field, still within the same reference class.

## Dogfood moment

Next morning after deploy: the ambient front-page glance over the real ~77 kg plateau (should read calm), then on History a 1M and a 1W tap in both lenses, and a 6M tap to confirm nothing changed. Production data by definition; self-report feeds KPI-9.
