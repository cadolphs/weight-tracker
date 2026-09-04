<!-- markdownlint-disable MD024 -->
# Feature Delta: y-axis-floor

## Wave: DISCUSS

### [REF] Persona ID

`clemens` — see `docs/product/personas/clemens.yaml`. Sole customer, sole user, sole developer. Phone-first, half-awake at 06:45, metric units, 0.1 kg scale. The record has moved since the persona was written (~82 kg in July → ~77 kg in September 2026); domain examples below use the production 77.x kg range. Unchanged otherwise.

### [REF] JTBD One-Liner

Job `track-true-weight-trend` (`docs/product/jobs.yaml`, status: validated). This feature repairs the **judging moment** (`js-2-judge`: *"see a smoothed trend line that absorbs water-weight noise — so I can decide whether to adjust anything based on real movement, not noise"*): the trend removes the noise, but the auto-zoomed y-axis puts it straight back — a month that moved 0.2 kg fills the full chart height and reads as dramatic swings. Secondary moment `js-4-glance` (the ambient front-page curve is the same engine, so it misleads the same way every morning).

**Bridge decision**: **no new job-story moment.** The job statement already names the outcome ("judge real progress without being misled by daily fluctuations"); this is a presentation defect against it. A dated note on `js-2-judge` and the feature-list entry in `jobs.yaml` record the delivery (js-3/js-4/js-5 precedent; no JTBD re-run).

### [REF] Locked Decisions

- **D1** Feature type: user-facing (presentation of the graph on both surfaces).
- **D2** Walking skeleton: NO — brownfield; the full vertical exists; this is a rendering-rule delta on the shared chart engine.
- **D3** UX research depth: lightweight — journey delta on steps 2–3 (failure modes), single persona.
- **D4** JTBD: bridge only to existing validated job `track-true-weight-trend`, primary moment `js-2-judge`, secondary `js-4-glance`; no re-analysis.
- **D5** Density: mode=lean (Tier-1 [REF] only), expansion_prompt=ask-intelligent (triggers evaluated — **none fired**, silent-lean).
- **D6** (proposed default, tunable — OQ-12) **Minimum visible y-span = 2.0 kg, absolute.** Rationale: 0.1 kg scale precision; daily raw noise ±0.5 kg; a stalled month of trend wobbles ≤0.2 kg → ≤10 % of chart height = reads flat; a real 0.25 kg/week loss over 1M = 1 kg = half the chart height = clearly sloped; over 3M = 3 kg > floor → natural auto-range. Absolute kg, not relative %, because honesty across scales matters more than adaptivity in a single-user, metric-only product.
- **D7** **One rule, both lenses, both surfaces**: the floor applies identically to Trend and Raw, on `#home-graph` (`/`) and `#graph-page` (`/graph`), at every time scale — it lives in the shared engine (ADR-008 parity by construction). Toggling lens or scale never changes the zoom rule.
- **D8** **Floor never clips, only widens**: when the plotted span (max − min) ≥ 2.0 kg the existing auto-range is kept (the feature shows on a long or steep window only as D9's clean edges); when the span < 2.0 kg the axis becomes [midpoint − 1.0, midpoint + 1.0] — every point inside, data centred. Degenerate windows (single point, all-equal values) fall under the same rule — never a zero-height axis. Whether a small extra symmetric pad rides on top is DESIGN's detail.
- **D9** (user) **Clean axis bounds**: after the range is determined (auto-range or floored), BOTH bounds snap OUTWARD to the nearest multiple of **0.5 kg** (`floor(lo / 0.5) × 0.5`, `ceil(hi / 0.5) × 0.5`). Uniform on every window, both lenses, both surfaces — not only below the floor — so every rendered y-axis has bounds and edge gridlines on a 0.5 kg grid and no bound ever reads like `77.42234`. Snapping only widens: the ≥ 2.0 kg guarantee and "every point inside" hold; the floored band becomes 2.0–3.0 kg wide (mid 77.235 → 76.235…78.235 → 76.0…78.5) and centring is approximate (band centre within 0.25 kg of the data midpoint).

### [REF] Scope Assessment

**PASS — 1 story, 1 bounded context (weight tracking / chart presentation), estimated ~0.25–0.5 day.** Oversized signals checked: stories 1/10; bounded contexts 1/3; walking skeleton N/A (exists); effort ≪ 2 weeks; user outcomes — one ("a stalled window reads as stalled"); lens/surface parity (D7) is an AC of that outcome, not a second story. No signal fired; no split needed. Reference class: US-009 (single palette in `graph.js`) landed in <0.5 day; this is one range rule in the same module — or one pure function in the core plus one field on two JSON responses, if DESIGN takes the server-side option.

### [REF] Journey Summary

SSOT: `docs/product/journeys/daily-weight-tracking.yaml` — **failure-mode delta on steps 2 and 3**; no step action, screen, or shared-artifact change; one new `integration_validation` rule (the floor constant must match across surfaces/lenses). Changelog entry dated 2026-09-04.

- **Step 3 (Judge the trend)** gains the failure mode this feature exists for: *auto-zoomed y-axis re-amplifies the noise the trend removed — a stalled month reads as dramatic swings*. The arc "possibly anxious after a raw spike → reassured" currently breaks at its last inch: the smoothed series is right, the axis lies about it. After: a stalled month is a near-flat stroke mid-chart; a real loss still slopes. A second failure mode covers D9: *axis bounds/labels at awkward floats (77.42234)* — bounds sit on a 0.5 kg grid on every window, so the edges of every chart read clean.
- **Step 2 (Review raw history)** gains the same rule for the raw lens: a week of ±0.3 kg dots is jitter inside a 2 kg band, not a sawtooth filling the screen.
- **Step 1** unchanged in flow and tap count; the ambient front-page curve (`js-4-glance`) inherits the fix through the shared engine — nothing added to the morning screen.
- Emotional delta: the reassurance the trend was built to deliver finally survives rendering; "stalled" feels like *calm*, not *chaos*.

### [REF] Story Map

Extends the existing map (same persona, same goal). No new activities; the Judge column gets the rendering-honesty story, which also governs the Review column's raw lens.

| Capture weight | Review history | Judge trend | Maintain record |
|---|---|---|---|
| US-001, US-006, US-007, US-008, US-010 ✅ | US-001, US-002, US-009, US-011, US-012 ✅ | US-004, US-005, US-009, US-010 ✅ | US-003, US-013, US-014 ✅ |
| *(front-page curve inherits the rule)* | *(raw lens, same rule — D7)* | **Stalled progress looks stalled (US-015)** | |

**Walking skeleton**: N/A — exists. **Slice** (elephant carpaccio, ≤0.5 day, dogfooded next morning):

- **Slice 01** — `slices/slice-01-y-axis-floor.md`: US-015 (one rule in the shared engine carrying both lenses and both surfaces; splitting by lens or surface would ship the constant twice and break D7).

### [REF] Priority Rationale

Single slice — priority question is only *whether now*. Yes: the record is currently plateaued around 77 kg, so the misread is happening on every morning glance and every History visit right now, in the exact emotional state (`js-2-judge`, "have I stalled?") the product exists to resolve. Value 4 (restores the trend's entire purpose — noise vs signal — at the point of rendering), Urgency 3 (active daily misread on production data; the bug is user-reported today), Effort 1 → score 12. MoSCoW: Must (explicit user request; D6–D8 locked as defaults, constant tunable).

### [REF] System Constraints

- Rendering rule only: the plotted **series values are untouched** (G-3 trend determinism is a property of the series; only the axis range changes). No change to the Kalman/RTS trend, windowing (ADR-004), or gap handling (nulls stay gaps).
- Axis bounds are clean (D9): after any range decision both bounds snap outward to the 0.5 kg grid; snapping only widens; no bound carries more than one decimal.
- Shared-engine parity (ADR-008): exactly **one definition** of the rule and **two constants** (floor 2.0 kg, bound grid 0.5 kg), never per-surface or per-lens. Whether it executes client-side (`graph.js`) or as a pure core projection returned on `/entries` and `/trend` is DESIGN's call — either way, one source of truth.
- Entry primacy (KPI-1, G-2): zero added fetches, zero added scripts, zero added taps; entry screen interactive ≤2 s with the rule live.
- Zero new external origins (G-5); axis/grid colors stay the theme's `--chart-*` tokens (US-009); with the wider range, gridlines and labels stay legible at AA in both schemes (G-4).
- Metric only: the floor is an absolute **kg** constant (`unit_label_kg` artifact); no unit conversion exists.
- KPI-3 purity: a render rule emits no telemetry; ambient renders and post-save repaints add 0 by construction (ADR-009).
- Read-only ports (`WeightHistory`, `TrendProjection`) must never gain write methods (CLAUDE.md / ADR-005); a server-side range, if chosen, is a pure projection of the existing windowed read.

### [REF] User Stories

All stories: `job_id: track-true-weight-trend`, moment `js-2-judge` (secondary `js-4-glance`). Persona: Clemens.

#### US-015: Stalled progress looks stalled

`job_id: track-true-weight-trend` · Slice 01 · Must · ~0.25–0.5 day

##### Problem

Clemens has hovered between 77.1 and 77.3 kg for a month. The trend line — correctly — is nearly flat. But the chart auto-zooms the y-axis to the data (bottom 77.1, top 77.3), so 200 g of residual wobble fills the full 320 px height and the plateau reads as a rollercoaster. The one moment the trend exists for ("is this real movement or noise?") is answered *wrongly by the axis* on both the ambient morning curve and the History page, in either lens, at 1W and 1M especially.

##### Elevator Pitch

- **Before**: Opens `/` on Fri 4 Sep 2026 at 06:45; the trend curve for the last month runs 77.1–77.3 kg, the y-axis reads `77.10 … 77.30`, and the flat month looks like a mountain range. Tapping **1M** on `/graph` makes it worse.
- **After**: Opens `/` (or `/graph`), taps **1M** → the y-axis runs `76.0 … 78.5` (a clean 2.5 kg band on the 0.5 kg grid), and the trend line sits as a near-flat stroke through the middle of the chart; tapping **Raw** shows the daily dots jittering inside the same band. On **6M**, where the record fell 82.1 → 77.2, the axis is the ordinary auto-range with clean edges, `76.5 … 83.0`.
- **Decision enabled**: "Have I actually stalled, or is this noise?" — decide whether to change anything from the real slope, which the axis now shows honestly instead of undoing.

##### Domain Examples

1. *Stalled month*: 1M window (5 Aug – 4 Sep 2026), Trend lens, smoothed values between 77.1 and 77.3 kg (span 0.2, mid 77.2). Floor gives 76.2 – 78.2; D9 snaps to **76.0 – 78.5**; the line's vertical extent is ≤10 % of the plot height — reads flat. Same on `/` and `/graph`.
2. *Real loss, still obvious*: 1M window, Trend lens, 78.4 → 77.4 kg (span 1.0 < 2.0, mid 77.9). Floor gives 76.9 – 78.9; D9 snaps to **76.5 – 79.0**; the line still drops through ~40 % of the chart height — clearly sloped, not flattened away.
3. *Long window, clean edges only*: 6M window, Trend lens, 82.1 → 77.2 kg (span 4.9 ≥ 2.0). Auto-range as before (≈76.7 – 82.6, data min/max plus the engine's ordinary padding), then D9 snaps to **76.5 – 83.0**. The only visible change here is the clean bounds.
4. *Raw week is noise in a band*: 1W window (29 Aug – 4 Sep), Raw lens, daily values 77.0 / 77.4 / 76.9 / 77.3 / 77.1 / 76.8 / 77.2 (min 76.8, max 77.4, span 0.6, mid 77.1). Floor gives 76.1 – 78.1; D9 snaps to **76.0 – 78.5**; the dots occupy ~25 % of the height — visibly jitter, not a sawtooth.
5. *Degenerate window keeps an honest axis*: 1W with a single entry (77.2 kg after a travel week) → 76.2 – 78.2 → **76.0 – 78.5**, not a zero-height line; three identical 77.0 entries → **76.0 – 78.0** (already on the grid).
6. *Awkward midpoint, clean bounds*: a window whose smoothed values run 77.15 … 77.32 (mid 77.235) → floored 76.235 – 78.235 → **76.0 – 78.5**; the axis never shows `76.235`.

##### UAT Scenarios (BDD)

###### Scenario: A stalled month reads flat

- **Given** Clemens's smoothed trend for 5 Aug – 4 Sep 2026 stays between 77.1 and 77.3 kg
- **When** he opens `/graph` and taps **1M** with the Trend lens
- **Then** the y-axis spans at least 2.0 kg (76.0 to 78.5) with every trend point inside it
- **And** the trend line's vertical extent is at most 10 % of the plot height
- **And** the same axis range is shown for the same window on the front-page graph at `/`

###### Scenario: A real month of loss still slopes

- **Given** Clemens's smoothed trend fell from 78.4 kg to 77.4 kg over the last month
- **When** he views the Trend lens at **1M**
- **Then** the y-axis spans 2.5 kg (76.5 to 79.0), its centre within 0.25 kg of the data midpoint
- **And** the trend line descends through roughly 40 % of the plot height — clearly sloped

###### Scenario: A long window keeps its auto-range, with clean edges

- **Given** Clemens's smoothed trend over the last six months runs from 82.1 kg down to 77.2 kg
- **When** he views the Trend lens at **6M**
- **Then** the y-axis range is the ordinary auto-range the chart showed before this feature (data min/max plus the engine's padding, ≈76.7 to 82.6) snapped outward to the 0.5 kg grid: 76.5 to 83.0
- **And** no floor widening is applied

###### Scenario: A raw week is noise inside a band

- **Given** Clemens's entries for 29 Aug – 4 Sep 2026 are 77.0, 77.4, 76.9, 77.3, 77.1, 76.8 and 77.2 kg
- **When** he taps **Raw** at **1W** on either surface
- **Then** the y-axis spans 2.5 kg (76.0 to 78.5) with all seven points inside it
- **And** days without an entry still show no point (gaps stay gaps)

###### Scenario: Toggling lens or scale never changes the zoom rule

- **Given** Clemens is on `/` at **1M** with the Trend lens showing a 76.0 to 78.5 axis
- **When** he taps **Raw**, then **1W**, then **Trend**, then **3M**
- **Then** each rendered axis obeys the same rule — at least 2.0 kg when the plotted span is under 2.0 kg, the ordinary auto-range otherwise, bounds on the 0.5 kg grid in both cases
- **And** the chosen time scale and lens survive each tap exactly as they do today

###### Scenario: Axis bounds are clean numbers

- **Given** a window whose smoothed values run from 77.15 kg to 77.32 kg (midpoint 77.235)
- **When** the chart renders
- **Then** the y-axis bottom is 76.0 and the top is 78.5 — both multiples of 0.5 kg
- **And** no axis bound carries more than one decimal

###### Scenario: The axis is always honest (@property)

- **Given** any window at any scale, in either lens, on either surface — including a single-entry window and an all-equal window
- **When** the chart renders
- **Then** the visible y-span is at least 2.0 kg and contains every plotted value
- **And** both bounds are multiples of 0.5 kg
- **And** when the plotted span is at least 2.0 kg, the range equals the pre-feature auto-range snapped outward to the 0.5 kg grid
- **And** the plotted series values are identical to the pre-feature series (G-3)

##### Acceptance Criteria

- For every rendered window (either lens, either surface, any of 1W/1M/3M/6M/1Y/ALL) the visible y-range spans ≥ 2.0 kg and contains every plotted value.
- When the plotted span (max − min of the values in the current window and lens, ignoring gap nulls) is < 2.0 kg, the range is [midpoint − 1.0, midpoint + 1.0] kg before snapping; after the D9 snap the band is 2.0–3.0 kg wide and its centre lies within 0.25 kg of the data midpoint; any extra pad DESIGN adds is symmetric and never narrows the band.
- When the plotted span is ≥ 2.0 kg, the range is the pre-feature auto-range snapped outward to the 0.5 kg grid — no floor widening (existing graph ATs stay green; the only visible change is clean edges).
- Every rendered axis bound is a multiple of 0.5 kg (snap outward only); tick labels therefore never show floats beyond one decimal.
- Single-point and all-equal windows render an axis of at least 2.0 kg, never a zero-height one.
- One constant, one definition: `/` and `/graph`, Trend and Raw, observe the identical rule; toggling lens or scale preserves the selection exactly as today and changes only the data, never the rule.
- Series values, gaps (raw nulls), trend algorithm and windowing are byte-identical to pre-feature (G-3).
- Guardrails hold: zero added fetches/scripts/taps on `/`; entry screen interactive ≤2 s; zero new external origins; axis/grid at AA contrast in both schemes; no telemetry emitted by the render rule.

### [REF] Out of Scope

Changing the trend algorithm or its parameters; a per-user or per-scale configurable floor; a *shared* y-range across Trend and Raw for the same window (OQ-13, default NO); any x-axis change; tooltips/hover/crosshair; any `/stats` or telemetry change; import of the old app's record; deleting entries; auth. Everything on prior features' out-of-scope lists remains out.

### [REF] Walking Skeleton Strategy

**N/A — brownfield.** The full production vertical exists; both surfaces already render both lenses at every scale through one engine. This feature is one range rule (plus, at DESIGN's option, one pure projection on two existing JSON responses); it deploys through the existing pipeline and is dogfooded on the next morning's ambient glance and a 1M/1W tap on History over the real ~77 kg record.

### [REF] Driving Ports

Behavioral, solution-neutral; DESIGN owns shapes and adapters. Read-only ports must never expose write methods (CLAUDE.md / ADR-005).

- **WeightHistory.entries_in** (driving, read-only, OUT-2) — series contract unchanged. If DESIGN places the rule server-side, the `/entries` response may gain an additive, optional y-range for the windowed entries — a pure projection of the same read; no port method change required.
- **TrendProjection.trend_series_in** (driving, read-only, OUT-3) — series contract unchanged (Kalman+RTS over the full record, output windowed, ADR-004). Same optional additive y-range projection as above, if server-side.
- **Shared chart engine** (`graph.js`, ADR-008) — must apply exactly one y-range rule to whatever it plots, on both mounts. If DESIGN keeps the rule client-side, it is one pure function of (min, max) inside the engine; if server-side, the engine consumes the returned range and computes nothing.
- **Telemetry** — untouched; the rule emits nothing (ADR-009 purity).

### [REF] Pre-Requisites

None blocking DESIGN. Both surfaces, both lenses, all scales, windowing, gaps and the theme palette are delivered and mutation-tested ✅. For DESIGN, two placements are open — **neither is locked here**: (A) client-side, a `scales.y.range` rule in `graph.js` — smallest change, but there is no JS test runner (no `package.json`), so it is assertable only by source/DOM inspection as US-009's palette was (`steps_theme.py::assert_chart_single_palette`); (B) server-side, a pure core function `floored_range(min, max) → (lo, hi)` returned on both `/entries` and `/trend` JSON and consumed by the engine — AT-testable as a pure-function driving-port contract with PBT (the @property scenario maps directly), mirroring ADR-004's server-side windowing. Whichever wins, one definition, two constants (A29, A31). For DISTILL: existing graph ATs (window/gaps/palette) must stay green unchanged — the above-floor path differs from pre-feature only by the outward 0.5 kg snap (A28), and no shipped AT asserts axis bounds; uPlot's default ~10 % pad is bypassed when a range function is supplied, so DESIGN decides explicitly whether the auto-range branch reproduces that pad before snapping (D8/D9) and pins it.

### [REF] Outcome KPIs

**Objective**: The chart tells the truth about movement at every scale — a stalled month looks calm, a real loss looks like a loss, and the trend's noise-removal is never undone by the axis.

Extends the existing registry (KPI-1…8 and G-1…G-5 unchanged; `kpi-contracts.yaml` is DEVOPS/DISTILL-owned and not edited here):

| # | Who | Does What | By How Much | Baseline | Measured By | Type |
|---|-----|-----------|-------------|----------|-------------|------|
| 9 | Clemens | reads a stalled or near-stalled window (trend wobble ≤0.3 kg) as stalled at a glance, without a false-alarm reaction | 0 false-alarm reactions over a 7-morning dogfood window; 100 % of stalled windows self-reported as "reads flat" | today every stalled window misreads as dramatic swings (100 % — the reported defect) | self-reported at dogfood (single-user `measurement_note`); no instrumentation added | Leading |

- **Guardrails (must not degrade)**: KPI-1 entry speed and tap count (the rule adds no fetch, no script, no tap); G-2 interactive ≤2 s on both surfaces; G-3 trend determinism (the series is untouched — only the axis range changes); G-4 contrast AA both schemes with the wider gridlines; G-5 zero new origins/scripts; KPI-3 purity (a render rule emits no telemetry; ambient renders and post-save repaints still add 0).
- **Hypothesis**: We believe an absolute 2.0 kg minimum visible y-span, applied by the shared engine to both lenses on both surfaces, with bounds snapped outward to a 0.5 kg grid, will let Clemens read a stalled month as stalled (0 false alarms over 7 mornings) while leaving steep or long windows as they are today save for clean edges, restoring the noise-vs-signal judgment (`js-2-judge`) the trend was built for.
- **Measurement plan**: dogfood self-report after 7 mornings (next-morning ambient glance on `/`, plus a deliberate 1M/1W tap on `/graph`), recorded in iteration notes; the KPI-9 row is proposed here for DEVOPS to register in `kpi-contracts.yaml` with `gate: soft`.

### [REF] DoR Validation

| DoR Item | US-015 | Evidence |
|----------|--------|----------|
| 1. Problem clear, domain language | PASS | Auto-zoomed axis re-amplifies the noise the trend removed; plateau reads as rollercoaster on both surfaces |
| 2. Persona specific | PASS | `clemens` — phone-first, 06:45, 0.1 kg scale, currently plateaued ~77 kg, judges progress from the trend |
| 3. 3+ domain examples, real data | PASS (6) | Real windows/values (77.1–77.3 stalled 1M; 78.4→77.4 loss; 82.1→77.2 over 6M; seven raw values 76.8–77.4; single 77.2 entry; 77.15–77.32 awkward midpoint) |
| 4. UAT 3–7 scenarios G/W/T | PASS (7) | Stalled-flat, real-loss, long-window-clean-edges, raw-band, lens/scale-parity, clean-bounds, @property honesty |
| 5. AC derived from UAT | PASS | Eight quantified ACs (≥2.0 kg, midpoint ±1.0, centre within 0.25 kg, 0.5 kg bound grid, auto-range-then-snap above floor, ≤2 s, AA, 0 telemetry) |
| 6. Right-sized (1–3 d, 3–7 sc.) | PASS | ~0.25–0.5 d; 7 scenarios (at the ceiling — one rule, one demo); demoable in one session on the phone |
| 7. Technical notes/constraints | PASS | System Constraints + Driving Ports (placement A/B open for DESIGN; floor + grid constants; read-only ports; pad/snap order pinned at DESIGN) |
| 8. Dependencies resolved/tracked | PASS | Shared engine, both lenses, windowing, gaps, palette all delivered ✅; AT-testability route flagged for DESIGN/DISTILL |
| 9. Outcome KPIs, numeric targets | PASS | KPI-9 (0 false alarms / 7 mornings, 100 % reads-flat) + six named guardrails, measurement method named |

**DoR Status: PASSED (1/1 story, 9/9 items).**

**Requirements completeness score: 0.95** — functional behavior fully specified (floor, approximate centring, auto-range-then-snap above the floor, clean 0.5 kg bounds, degenerate windows, parity), NFRs quantified (≤2 s, AA, zero origins/scripts/taps, series identity), business rules explicit (absolute 2.0 kg floor, 0.5 kg bound grid, kg-only). Deductions: the two constants are defaults (OQ-12, OQ-14) and the pad/snap ordering is deliberately left to DESIGN (D8/D9).

### [REF] DoD 9-Item Checklist

Per story, at DELIVER completion (unchanged pattern):

1. All UAT scenarios green (automated), including the @property honesty scenario.
2. Supporting unit/integration tests green — existing graph ATs (window, gaps, palette) unchanged and green (above-floor path differs only by the outward 0.5 kg snap).
3. Code refactored; per-feature mutation gate ≥80 % on modified files.
4. Code reviewed (self-review with reviewer agent — solo project).
5. Merged to main.
6. Deployed to the phone-reachable production URL via the existing pipeline.
7. Dogfooded next morning: ambient glance on `/` over the real record, then a 1M and 1W tap (both lenses) on `/graph`; self-report recorded.
8. Guardrails verified: ≤2 s interactive, zero added scripts/origins/taps, contrast AA both schemes, /stats counters unmoved by renders.
9. Story demonstrable end-to-end on the phone.

### [REF] Wave Decisions Summary

Locked: D1–D5 + D6–D9 (absolute 2.0 kg minimum visible y-span; one rule, both lenses, both surfaces; floor widens, never clips, data centred; bounds snap outward to a 0.5 kg grid on every window). Prior assumptions A1–A24 unchanged and still binding.

New assumptions (chosen during requirements, flagged for confirmation):

- **A25** The floor constant is **2.0 kg, absolute, in kg** (the product is metric-only); it has exactly one definition wherever the rule lives, and is never scaled by window length or lens.
- **A26** "Plotted span" = max − min of the values actually plotted for the current window and lens (raw: stored entries in the window, gap nulls ignored; trend: the windowed smoothed points) — never the whole record, never the other lens.
- **A27** Below the floor the range is [midpoint − 1.0, midpoint + 1.0] before the D9 snap; any extra pad DESIGN adds is symmetric and only ever widens (the ≥2.0 kg guarantee holds regardless; centring is approximate after snapping — band centre within 0.25 kg of the data midpoint).
- **A28** At or above the floor the range is the pre-feature auto-range (uPlot's default range + pad), then snapped outward to the 0.5 kg grid (D9) — no floor widening. The feature is therefore visible on steep/long windows only as clean edges; every existing graph AT stays green unchanged because none asserts axis bounds.
- **A29** Exactly one implementation of the rule, shared by both mounts (ADR-008). Client-side (`graph.js` range function) vs server-side (pure core projection on `/entries` + `/trend`) is DESIGN's call; the AT-testability difference is recorded in Pre-Requisites, not decided here.
- **A30** Lenses keep independent y-ranges for the same window (a raw 1W and a trend 1W may show different bands); no cross-lens range sharing (OQ-13 default).
- **A31** Bound grid = **0.5 kg**; both bounds snap **outward** (`floor(lo/0.5)×0.5`, `ceil(hi/0.5)×0.5`); applied **uniformly** after every range decision (auto or floored), on every window, both lenses, both surfaces. Snapping never narrows, so it can only strengthen the ≥2.0 kg and every-point-inside guarantees.

Open questions (non-blocking; defaults apply unless overridden):

- **OQ-12** Is **2.0 kg** the right honesty constant, or would 1.5 kg (more sensitive to slow loss at 1M) or 3.0 kg (calmer weeks) read better? Default 2.0 — falsifiable at the slice's dogfood (a 1M real loss looking flat, or 6M looking cramped, disproves it).
- **OQ-13** Should Trend and Raw share the *same* y-range for a given window so that toggling the lens is directly comparable? Default **NO** (out of scope): each lens ranges over its own plotted values; the floor alone already makes the two bands identical in the common stalled case (A30).
- **OQ-14** Bound grid step **0.5 kg** (default) vs **0.1 kg**? 0.1 keeps the floored band nearer 2.0 kg but edge gridlines rarely land on ticks and bounds like 76.2 still look arbitrary; 0.5 gives clean edges and tick-aligned bounds at the cost of up to +1.0 kg extra span (band 2.0–3.0 kg). Default 0.5 — judged at the same dogfood as OQ-12.

Risk notes: **product risk** = the two constants — an absolute kg floor and a 0.5 kg bound grid are taste bets (the grid can add up to 1.0 kg of span and blunt a 1M loss slightly, example 2 at ~40 % height); mitigated by keeping both single named constants and by the slice's learning hypothesis (dogfood on the real plateau, a 1M loss view, and the 6M view). **Testability risk** = no JS runner; if the rule stays client-side the @property scenario is assertable only by source/DOM inspection (US-009 precedent), which is why the server-side pure-function placement is offered to DESIGN with equal weight. **Regression risk** = existing graph ATs — mitigated by A28 (above the floor: auto-range then snap, nothing else) and the explicit "long window keeps its auto-range" scenario; uPlot's pad bypass when a range function is supplied, and the pad-then-snap order, must be decided consciously at DESIGN (D8/D9), never discovered at DELIVER. Technical risk negligible (one rule in one module, or one pure function plus one field). JTBD traceability intact (US-015 → `js-2-judge`, secondary `js-4-glance`; no new moment). No DIVERGE — user = customer, D6–D8 taken as routine defaults with the constant flagged (accepted pattern). Density: lean + ask-intelligent; triggers evaluated (AC ambiguity ≥2 stories, ≥3 bounded contexts, ≥3 personas, compliance terms, WS strategy D) — **none fired** → silent lean. Density telemetry skipped: `scripts/shared/telemetry.py` not present in this repository (recorded here in lieu of the event, per prior features).

## Wave: DESIGN

Architect: solution-architect (Morgan), 2026-09-04. Mode: Propose (the one mechanism DISCUSS left open — A29 placement — plus the D8/A28 pad-then-snap order, the degenerate-input rule and the wire shape, analyzed against the live codebase and the vendored uPlot 1.6.32 source; user accepted the recommended defaults at DISCUSS and expects the same here). SSOT updated: `docs/product/architecture/brief.md` (§ Application Architecture — y-axis-floor delta paragraph, ADR index) + new `adr-012-y-axis-range-rule.md`. ADR-001…011 unchanged; **none superseded** (ADR-004's series and ADR-008's one-engine rule are both relied on, not altered). Paradigm not re-decided (ADR-005 / CLAUDE.md: Functional Core / Imperative Shell — the range rule is pure arithmetic and lands in the core). No C4 L1/L2 changes (no new containers, actors, external systems, routes, assets, or origins); no L3 (below the 5-component threshold). Per-wave peer review deferred to the orchestrator's consolidated review at DISTILL (precedent: graph-first-home, entry-date-picker) — no contested ADR, no novel pattern, no unverified performance budget (two floats per response), no security-boundary change (no new route; AccessGate, auth, and origins untouched). Density: lean, Tier-1 [REF] only, no Tier-2 expansions; density telemetry skipped (`scripts/shared/telemetry.py` absent).

### [REF] DDD List

Numbering continues the global DESIGN sequence from D-26 (entry-date-picker); the DISCUSS decisions D1–D9 above are this feature's own local sequence.

- **D-27 Placement = server-side pure core function, projected onto both JSON reads, consumed by the engine** (ADR-012, resolves A29) — **accepted**. `core/axis.py: y_axis_range(values) -> AxisRange | None` is a pure, clock-free, total function over the plotted values; `GET /entries` and `GET /trend` each add one **additive, optional** field `y_range: [lo, hi] | null` computed in the shell from the exact series the route already returns (`shown` at `routes.py:582`, `points` at `routes.py:599`); `graph.js` supplies `scales.y.range` from it and **computes nothing**. Decisive evidence: (1) there is no JS test runner (no `package.json`) — a client-side rule would be assertable only by source-regex inspection, as US-009's palette was (`composition.py:1265-1270` greps the rendered HTML for hex literals; it proves presence, never arithmetic), whereas the @property honesty scenario maps 1:1 onto a Hypothesis test over `y_axis_range` in the shipped PBT style (`properties/test_trend_math_properties.py`); (2) the per-feature mutation gate (≥80 % on modified files, CLAUDE.md) can only bite on Python — a JS rule would carry both product constants outside every gate the project has; (3) ADR-005 says pure arithmetic belongs in the core, and ADR-008's parity-by-construction survives untouched — one definition (core), one consumer (the shared engine); (4) uPlot's own default is unsafe on exactly the degenerate case this feature exists for (span 0 ⇒ pad = |value| ⇒ a 0…154 kg axis, `rangeNum` source below), so a client rule would have to reimplement range logic in JS anyway. Rejected: (A) client-side `scales.y.range` in `graph.js` — smallest diff, untestable arithmetic, constants outside the mutation gate; (C) hybrid (server computes, client re-checks or pads) — two definitions of one rule, forbidden outright by A29 and the journey's `y_axis_floor_kg` integration rule. Disclosed cost: a presentation number now crosses the wire on data endpoints (precedent: `confirmation`/`glance`/`recent` route-level enrichment), and the engine trusts one more server field — contained by D-31's degrade-to-absent guard.
- **D-28 Auto-range branch pinned as an explicit formula, not a uPlot replay** (resolves D8/A28; § Changed Assumptions) — **accepted**. When `span = max − min ≥ FLOOR_KG`: `lo = min − 0.1·span`, `hi = max + 0.1·span`, then the D9 snap. Verified against the vendored bundle (`uplot.iife.min.js`, `rangeNum` = `Z` → `ll`): uPlot's default y-range pads each side by `0.1 × span` **and then rounds outward to a multiple of `10^⌊log10 span⌋ / 10`** (0.1 kg for spans in [1, 10) kg, 1.0 kg for spans ≥ 10 kg). For every span in **[2.0, 10.0) kg** the pinned formula followed by the 0.5 kg snap is *identical* to uPlot-then-snap (⌊·⌋₀.₅ ∘ ⌊·⌋₀.₁ = ⌊·⌋₀.₅); for spans **≥ 10 kg** uPlot's whole-kg pre-rounding can differ from ours by at most 0.5 kg on a bound (≤5 % of such a span). The simple formula is chosen because it is the rule the ATs will state and the property test will oracle; replaying uPlot's magnitude-dependent rounding would import an engine detail into the domain for no user-visible benefit. Below the floor: `[mid − 1.0, mid + 1.0]`, **no extra pad** (A27 permits none; simplest; the snap already widens by up to 1.0 kg).
- **D-29 Degenerate input** — **accepted**. Zero values ⇒ `None` (wire `null`; the engine has already cleared the chart on an empty series, `graph.js:143,155`). One value or all-equal ⇒ span 0 < floor ⇒ the floored band around that value — never a zero-height axis and never uPlot's |value|-sized pad. Raw gap nulls never reach the function: the shell passes `weight_kg` of the windowed entries (`shown`), which by construction are only stored days (A26).
- **D-30 Constants and float discipline** — **accepted**. Exactly one definition each, in `core/axis.py`: `FLOOR_KG = 2.0`, `GRID_KG = 0.5` (A25/A31), plus `AUTO_PAD_FRACTION = 0.1` (the replicated engine default, D-28) — **never duplicated in `graph.js`**, which carries no numeric literal for the rule. Snap = `⌊2x + ε⌋ / 2` and `⌈2x − ε⌉ / 2` with `ε = 1e-9`: every multiple of 0.5 is an exact binary float, so bounds are exact on the wire by construction (`76.5`, never `76.49999…`); ε absorbs float noise from the pre-snap arithmetic so a value within 1e-9 kg of a grid line is treated as on it (three identical 77.0 entries ⇒ `76.0…78.0`, not a spurious `75.5`). Whether the crafter reaches ε via `math.floor` or `Decimal` is implementation; the pinned examples and the property are the contract.
- **D-31 Wire shape + degrade-to-absent** — **accepted**. Field name `y_range` (no prior precedent for an axis field; `{date, weight_kg}` / `trend_kg` set the snake-case, unit-suffix-free-for-pairs convention). Key **always present** on both reads: `[lo, hi]` (two JSON numbers, `lo < hi`) when ≥1 value is plotted, `null` otherwise; existing keys (`entries`, `invite_first_log`, `points`) byte-identical. Engine rule: use `scales: { y: { range: () => [lo, hi] } }` **only if** `y_range` is an array of exactly two finite numbers with `lo < hi`; on absent / null / garbled input, omit the override so uPlot's default auto-range renders — a chart with an imperfect axis, **never a blank chart**. No shipped AT asserts the exact key set of either body (all index by key — verified `composition.py`, `properties/`), so the addition breaks nothing.
- **D-32 Nothing else moves** — **accepted**. No new route; no telemetry (KPI-3 purity, ADR-009 — both reads stay pure reads); no C4 L1/L2 change; no new origin, script or asset; no CLAUDE.md change (paradigm already FP); no port protocol change (`ports.py` untouched — `WeightHistory` / `TrendProjection` gain **no methods at all**; `y_range` is route-level enrichment on the `glance`/`recent` precedent). One consequence the DELIVER step must not miss: `graph.js` is pre-cached in the service-worker APP_SHELL (`sw.js:11`), so its edit requires a `SHELL_CACHE` bump `-v4 → -v5` (the `-v4` precedent bumped for a changed pre-cached response).

### [REF] Component Decomposition

Delta only — authoritative table: `brief.md` § Component Decomposition and Ports.

| Component | Path | Change |
|---|---|---|
| Axis range rule (pure core) | `src/weight_tracker/core/axis.py` | **CREATE NEW**: `FLOOR_KG`, `GRID_KG`, `AUTO_PAD_FRACTION`; `y_axis_range(values: Sequence[float]) -> AxisRange \| None` (frozen pair `lo_kg`, `hi_kg`). No I/O, no clock, imports only `core` (import-linter contract covers it automatically: `source_modules = ["weight_tracker.core"]`). |
| Route `GET /entries` | `src/weight_tracker/web/routes.py:577-586` | EDIT: `"y_range": axis_range_wire(y_axis_range([e.weight_kg for e in shown]))` beside the existing keys. |
| Route `GET /trend` | `src/weight_tracker/web/routes.py:588-604` | EDIT: same field over `[p.trend_kg for p in points]`. |
| Wire helper | `src/weight_tracker/web/routes.py` (next to `entry_wire_pair`, `:323`) | EDIT: one `axis_range_wire(range) -> list[float] \| None` — the ONE place the pair becomes `[lo, hi]` / `null` (D-18 single-source precedent). |
| Shared graph module | `src/weight_tracker/web/static/graph.js` | EDIT: `renderChart(data, lineOptionsFor, yRange)` adds `scales: { y: { range: () => yRange } }` only when `yRange` passes the D-31 guard; `showRaw`/`showTrend` pass `history.y_range` / `trend.y_range`. No constants, no arithmetic. |
| Service worker | `src/weight_tracker/web/static/sw.js` | EDIT: `SHELL_CACHE` `-v4 → -v5` (pre-cached `graph.js` changed). APP_SHELL list unchanged. |
| `ports.py`, `core/types.py`, `core/trend.py`, `core/glance.py`, `core/validation.py`, `composition.py`, `shell/*`, templates, `theme.css`, `uplot.iife.min.js` | — | **UNCHANGED**. |

### [REF] Driving Ports

| Port | Delta |
|---|---|
| `WeightHistory` | **Unchanged; no method added.** `y_range` is a pure projection of the windowed `entries_in` read the route already performs — identical in kind to `recent` (D-19) and the whole-record map (D-21). Read-only stays read-only (strongest form: zero new methods). |
| `TrendProjection` | **Unchanged.** `y_range` over the windowed `trend_series_in` output; ADR-004's series, windowing and determinism (G-3) untouched — the values on the wire are byte-identical to pre-feature. |
| Shared chart engine (`graph.js`, ADR-008) | Consumes `y_range`; applies it through uPlot's `scales.y.range`; computes nothing; degrades to uPlot auto on a failed guard (D-31). One code path, both mounts — parity by construction holds. |
| `WeightLogging`, `AccessGate`, telemetry | Unchanged; no new route to guard; nothing emitted (ADR-009). |

### [REF] Driven Ports + Adapters

**None new — explicitly.** No new I/O, storage, external dependency or clock use ⇒ **no new Earned-Trust probes**; `EntryStorePort.probe()` and the AST probe-presence gate are untouched. The one newly trusted input is the engine's `y_range` from the server — bounded by the D-31 shape guard (array, length 2, finite, `lo < hi`), with the substrate lie "the server sent garbage" contained by falling back to uPlot's own range, never a blank chart. Fault injection for DISTILL: `y_range` key absent / `null` / `[77]` / `["a","b"]` / `[78.5, 76.0]` ⇒ chart still renders with uPlot auto-range; series unaffected.

### [REF] Technology Choices

**Zero new dependencies, zero new external origins, zero new assets, zero new routes.** uPlot 1.6.32 (MIT, vendored, byte-identical) already exposes `scales.y.range` as a function/tuple override — no library change. Enforcement tooling unchanged: import-linter forbids `core → shell/web` and covers the new module by package; mypy strict; AST probe gate (no new adapters). No contract-test annotation change: no application-level third-party API exists (brief.md § External Integrations stands).

### [REF] Range Rule

Input: the plotted values of the current window and lens (raw: `weight_kg` of the windowed stored entries; trend: `trend_kg` of the windowed smoothed points). Output: `[lo, hi]` or none.

1. `n = 0` ⇒ **none** (wire `null`).
2. `min`, `max` over the values; `span = max − min`.
3. **Below the floor** (`span < FLOOR_KG = 2.0`): `mid = (min + max) / 2`; `lo₀ = mid − 1.0`, `hi₀ = mid + 1.0`. No extra pad.
4. **At or above the floor** (`span ≥ 2.0`): `lo₀ = min − 0.1·span`, `hi₀ = max + 0.1·span`.
5. **Snap outward** to `GRID_KG = 0.5`: `lo = ⌊2·lo₀ + ε⌋ / 2`, `hi = ⌈2·hi₀ − ε⌉ / 2`, `ε = 1e-9`.

Guarantees (the @property oracle): `lo ≤ min`, `max ≤ hi`; `hi − lo ≥ 2.0`; `lo`, `hi` ∈ 0.5·ℤ; below the floor `hi − lo ∈ [2.0, 3.0]` and `|(lo + hi)/2 − mid| ≤ 0.25`; at or above the floor `lo = ⌊2(min − 0.1·span)⌋/2` and `hi = ⌈2(max + 0.1·span)⌉/2` exactly; the function is order-invariant, total, and deterministic.

Worked examples (DISCUSS's six, each number re-derived from the steps above — all match the DISCUSS bounds):

| # | Values | span | branch | pre-snap | **axis** |
|---|---|---|---|---|---|
| 1 | 1M trend 77.1…77.3 | 0.2 | floor, mid 77.2 | 76.2 / 78.2 | **76.0 / 78.5** |
| 2 | 1M trend 78.4 → 77.4 | 1.0 | floor, mid 77.9 | 76.9 / 78.9 | **76.5 / 79.0** |
| 3 | 6M trend 82.1 → 77.2 | 4.9 | auto, pad 0.49 | 76.71 / 82.59 | **76.5 / 83.0** (uPlot's own 76.7 / 82.6 snaps to the same) |
| 4 | 1W raw 76.8…77.4 | 0.6 | floor, mid 77.1 | 76.1 / 78.1 | **76.0 / 78.5** |
| 5a | single 77.2 | 0 | floor, mid 77.2 | 76.2 / 78.2 | **76.0 / 78.5** |
| 5b | three × 77.0 | 0 | floor, mid 77.0 | 76.0 / 78.0 | **76.0 / 78.0** (already on grid; ε keeps it there) |
| 6 | 77.15…77.32 | 0.17 | floor, mid 77.235 | 76.235 / 78.235 | **76.0 / 78.5** |
| 7 | boundary: 76.0…78.0 | 2.0 | auto (≥), pad 0.2 | 75.8 / 78.2 | **75.5 / 78.5** |
| 8 | ≥10 kg: 90.3 → 77.2 | 13.1 | auto, pad 1.31 | 75.89 / 91.61 | **75.5 / 92.0** (uPlot would say 75.0 / 92.0 — the one divergence class, § Changed Assumptions) |

Rows 7–8 are DESIGN additions pinning the branch boundary (span exactly 2.0 is auto) and the only class where the formula departs from a uPlot replay.

### [REF] FC/IS Placement (ADR-005)

| Layer | What lands there |
|---|---|
| **Pure core** — `core/axis.py` | `y_axis_range` + the three constants. Total over any finite float sequence, no clock, no I/O; Hypothesis-testable (same style as `core/glance.py` — one ADR, one module). |
| **Shell / route** — `web/routes.py` | Project the already-windowed series into the function; phrase the pair as `[lo, hi]` / `null` in one wire helper. Route-level enrichment, explicitly not a port widening. |
| **Shell / client** — `graph.js` | Guard the field's shape; hand the pair to uPlot; on guard failure hand nothing. No arithmetic, no constants. |
| **Static** — `sw.js` | Cache-name bump only. |

### [REF] Decisions Table

| # | Decision | ADR |
|---|---|---|
| D-27 | Placement = pure core `y_axis_range` projected as `y_range` on `/entries` + `/trend`; engine consumes, computes nothing | ADR-012 |
| D-28 | Auto branch = `min − 0.1·span` / `max + 0.1·span` then snap (explicit formula, not a uPlot replay); floor branch = `mid ± 1.0`, no extra pad | ADR-012 |
| D-29 | 0 values ⇒ none/`null`; 1 value or all-equal ⇒ floored band; gap nulls never reach the function | ADR-012 |
| D-30 | `FLOOR_KG = 2.0`, `GRID_KG = 0.5`, `AUTO_PAD_FRACTION = 0.1` in `core/axis.py` only; snap exact by half-integer construction, ε = 1e-9 grid tolerance | ADR-012 |
| D-31 | Wire: `y_range: [lo, hi] \| null`, key always present, additive; engine guard ⇒ degrade to uPlot auto, never blank | brief.md |
| D-32 | No route / telemetry / C4 / origin / CLAUDE.md / port change; `SHELL_CACHE -v5` | brief.md |

### [REF] Reuse Analysis

Brownfield — **one CREATE NEW** (the pure module), everything else EXTENDs or stays untouched (codebase verified 2026-09-04). Default is EXTEND.

| Existing component | Evidence | Verdict | Contract shape · universe · crafter assertion mechanism |
|---|---|---|---|
| `renderChart` | `graph.js:115-128` — builds uPlot opts; no `scales` key today | **EXTEND** (one optional `scales.y.range` when the guard passes) | shell render · DOM effect at one site · source-level AT (palette-guard precedent) asserting `scales.y.range` is fed from `y_range` and that no numeric floor/grid literal exists in `graph.js` |
| `showRaw` / `showTrend` | `graph.js:140-161` — already hold the parsed body | **EXTEND** (pass `body.y_range` through) | shell · universe ∅ · same source-level AT |
| `history` handler | `routes.py:577-586` — already holds `shown` | **EXTEND** (one key) | read-only route · universe ∅ · `/entries` AT: `y_range` present, equals the pinned example bounds |
| `trend` handler | `routes.py:588-604` — already holds `points` | **EXTEND** (one key) | read-only route · universe ∅ · `/trend` AT: same |
| `entry_wire_pair` | `routes.py:323-327` — the one `{date, weight_kg}` shape | **NO CHANGE**; sibling `axis_range_wire` added beside it (same "one wire shape, one place" discipline) | pure · universe ∅ · wire ATs |
| `entries_in_window` / `window_start` | `core/types.py:65-81` | **NO CHANGE** — windowing is upstream of the rule; the rule takes values, not entries, so it is lens-agnostic | pure · universe ∅ · shipped window ATs stay green |
| `trend_series_in` | `core/trend.py:50-62` | **NO CHANGE** — series byte-identical (G-3) | pure · universe ∅ · shipped determinism PBT |
| `core/glance.py` | ADR-006 pattern: one derivation, one module, constants at top | **PATTERN REUSED** by `core/axis.py` (not extended — a presentation rule does not belong in the glance derivation) | — |
| `core/types.py` | noun module (dataclasses, enums, window helpers) | **NOT EXTENDED** — putting a rendering rule here would couple every core consumer's mutation scope to axis arithmetic; rejected in favour of `core/axis.py` | — |
| `core/trend.py` | ADR-004 determinism module | **NOT EXTENDED** — same reason; ADR-004's constants "changed only by a superseding ADR" must not share a file with a tunable taste constant (OQ-12/14) | — |
| `uplot.iife.min.js` `rangeNum` | `Z`/`ll` in the bundle: pad 0.1·span then round outward to `base/10` | **NOT REUSED** as the rule (unsafe at span 0; JS-only; untestable here); its pad fraction is replicated as `AUTO_PAD_FRACTION` | — |
| `assert_chart_single_palette` | `composition.py:1265-1270` — source/HTML inspection of a client rule | **PATTERN REUSED** for the engine-side guard AT (presence of the `scales.y.range` wiring and absence of constants), while the arithmetic is asserted server-side by PBT | — |
| `sw.js` | `sw.js:6,11` — `graph.js` pre-cached | **EXTEND** (cache-name bump) | static · universe ∅ · shipped APP_SHELL AT |

### [REF] C4 Note

**No diagram changes.** L1/L2 in `brief.md` remain accurate: the rule lives in the App Server's pure core, the two floats ride the existing HTTPS "requests pages and series from" relationship, and the engine already inside the Browser/PWA-shell container applies them. No new container, route, dependency, or external origin. No L3 — below the 5-component threshold.

### [REF] Open Questions / DISTILL–DELIVER Notes

| # | Note | Owner |
|---|---|---|
| R-1 | **Property test is the primary AT for the rule**: Hypothesis over `y_axis_range` with the § Range Rule oracle (containment, ≥2.0, 0.5-grid, floor-band width 2.0–3.0 and centre within 0.25 of `mid`, exact auto formula at/above the floor, order invariance, `None` iff empty). Strategy: lists of floats in [30.0, 250.0] at 0.1 precision for raw plus arbitrary floats in that range for trend; explicit `@example`s for rows 1–8 above. Layer-1 pure-core PBT, `test_trend_math_properties.py` style. | DISTILL |
| R-2 | **Wire ATs on both reads**: `y_range` present on `/entries` and `/trend` for the DISCUSS windows (rows 1–5); `null` on an empty record; existing keys untouched; **no existing AT asserts either body's exact key set** (verified — all index by key), so nothing is renegotiated. Both surfaces fetch the same URLs, so the "same axis on `/` and `/graph`" clause is parity by construction (ADR-008) and needs no second assertion. | DISTILL |
| R-3 | **Engine-side degrade-to-absent** is asserted the way US-009 asserted the palette (source inspection, no browser): `graph.js` wires `scales.y.range` from `y_range` behind a shape guard, and contains **no numeric literal** for the floor, grid or pad (`2.0`, `0.5`, `0.1` as range constants). Fault injection list in § Driven Ports. | DISTILL |
| R-4 | **Outcome registry**: register the new outcome manually (OUT-12 precedent — CLI defect noted in `registry.yaml` header): "Y-axis range projection — pure function over the plotted values, `y_range` on both reads"; amend OUT-2 / OUT-3 output shapes with the additive optional field (OUT-1 amendment precedent). Collision check at DESIGN: see § Outcome Collision Check. | DISTILL |
| R-5 | **`graph.js` consumes `y_range`** through the D-31 guard; **`SHELL_CACHE -v4 → -v5`** in `sw.js` (pre-cached asset changed). | DELIVER |
| R-6 | **Mutation gate** ≥80 % scoped to `core/axis.py` + `web/routes.py` (the modified Python files), per CLAUDE.md per-feature strategy. `graph.js` is outside the gate — which is why the arithmetic does not live there. | DELIVER |
| R-7 | **Resolved at DESIGN**: OQ-12 (2.0 kg) and OQ-14 (0.5 kg) stay at their DISCUSS defaults — both are single named constants in one file, so the dogfood retune is a one-line change; OQ-13 (shared range across lenses) stays NO — each read ranges its own values (A30). | — |

### Outcome Collision Check

`nwave-ai outcomes check-delta docs/feature/y-axis-floor/feature-delta.md` — **executed by the orchestrator (2026-09-04): exit 0, "8 outcomes checked, 0 collisions found"**, with one expected warning, "OUT-12 referenced in delta but not in registry" (DISTILL registers OUT-12; `registry.yaml` not edited here). Manual cross-check agrees: OUT-2/OUT-3 are the series reads this projection rides on (amend, not collide); OUT-5 is trend determinism (depended on, not restated); OUT-7 (glance) is a different derivation; OUT-8…11 are telemetry and entry-screen outcomes. **No collision.**

### Changed Assumptions

**A25, A26, A27, A30, A31 hold as written.** **A29 is resolved, not changed** — placement decided server-side (D-27) with DISCUSS's stated requirements met exactly: one definition, two constants (plus the replicated pad fraction), read-only ports gain no methods, series untouched, zero added fetches/scripts/taps, zero telemetry. OQ-12/13/14 resolved at their defaults (R-7). A1–A24 unchanged.

**A28 is refined.** DISCUSS wrote, in § Wave Decisions Summary: *"**A28** At or above the floor the range is the pre-feature auto-range (uPlot's default range + pad), then snapped outward to the 0.5 kg grid (D9) — no floor widening. The feature is therefore visible on steep/long windows only as clean edges; every existing graph AT stays green unchanged because none asserts axis bounds."* and, in the @property scenario: *"when the plotted span is at least 2.0 kg, the range equals the pre-feature auto-range snapped outward to the 0.5 kg grid"*.

Reading the vendored uPlot 1.6.32 source (2026-09-04) shows the "pre-feature auto-range" is not one formula: `rangeNum` pads by 0.1·span and then rounds outward to a magnitude-dependent increment (`10^⌊log10 span⌋ / 10`), and at span 0 it pads by the value's own magnitude. The observable promise therefore becomes: **"at or above the floor, the range is the data min/max padded by 10 % of the span on each side, then snapped outward to the 0.5 kg grid"** (D-28). For every span in [2.0, 10.0) kg this is byte-identical to uPlot-then-snap; for spans ≥ 10 kg it can differ from a uPlot replay by at most 0.5 kg on a bound. The second half of A28 stands unchanged: no shipped AT asserts axis bounds (verified), so every existing graph AT stays green. Flagged here rather than edited in place, per the never-silent discipline; DISTILL's ATs pin the refined wording, not the original.

## Wave: DISTILL

Acceptance designer, 2026-09-04. Reconciliation gate: all prior wave decisions read (DISCUSS D1–D9 / A25–A31 / OQ-12–14 and the seven UAT scenarios; DESIGN D-27–D-32 + ADR-012 + § Range Rule + § Changed Assumptions; no DEVOPS wave — brownfield on the shipped pipeline, WARN logged, default matrix) — **0 contradictions**. DESIGN's refinement of A28 ("the pre-feature auto-range" → the explicit 10 % pad formula, then snap) is a documented Changed Assumption that keeps every observable DISCUSS promise (≥ 2.0 kg, containment, 0.5 kg grid, no floor widening above the floor, series untouched) — the ATs pin the refined wording. Deliverable type: `application` (no `.nwave/des-config.json`, no global default → FS detection) ⇒ no plugin/skill reviewer routing. Infrastructure policy: `--policy=inherit` — this feature adds **no port and no adapter**, so zero rows are missing; the Architecture of Reference is unchanged (driving = `TestClient` over `build_app`, driven-internal = real SQLite on `tmp_path`, driven-external = `FakeClock` only). Density: lean, Tier-1 `[REF]` only; density telemetry skipped (`scripts/shared/telemetry.py` absent in this repository — recorded here per prior features).

### [REF] Scenario List

Scenario SSOT: `tests/weight-trend-tracker/acceptance/milestone-11-honest-axis.feature` (Slice 01 — US-015). **13 scenarios / 13 executions**, all `@pending` (one-at-a-time, ADR-025). Error/edge share **7/13 ≈ 54 %**.

| Scenario | Tags |
|---|---|
| A stalled month reads flat | `@pending @driving_port @US-015 @contract-shape:pure-function` |
| A real month of loss still slopes | `@pending @driving_port @US-015 @contract-shape:pure-function` |
| A long window keeps its ordinary range, with clean edges | `@pending @driving_port @US-015 @contract-shape:pure-function` |
| A raw week is noise inside a band | `@pending @driving_port @US-015 @contract-shape:pure-function` |
| A missing day stays a gap beneath the honest axis | `@pending @driving_port @error @US-015 @contract-shape:pure-function` |
| Toggling lens or scale never changes the rule | `@pending @driving_port @property @US-015 @contract-shape:pure-function` |
| Axis bounds are clean numbers | `@pending @driving_port @error @US-015 @contract-shape:pure-function` |
| A lone entry still stands on an honest axis | `@pending @driving_port @property @error @US-015 @contract-shape:pure-function` |
| A perfectly steady week is a flat line, never a zero-height axis | `@pending @driving_port @property @error @US-015 @contract-shape:pure-function` |
| An empty window offers no axis | `@pending @driving_port @error @US-015 @contract-shape:pure-function` |
| An empty record invites, and offers no axis | `@pending @driving_port @error @US-015 @contract-shape:pure-function` |
| Exactly two kilograms of movement is where the floor steps aside | `@pending @driving_port @error @US-015 @contract-shape:pure-function` |
| The axis frames the line and never moves it | `@pending @driving_port @property @kpi @US-015 @contract-shape:unbounded-preservation` |

All four `@property` scenarios are layer-3 (real HTTP + real SQLite) ⇒ **example-pinned**, per Mandate 9/11. The lens × scale Cartesian (2 × 6) is a closed world and is **enumerated** by the tour service rather than generated (the falsifier-gate: finite + listable ⇒ parametrize-shape, not PBT). No pure-core PBT is authored here: `y_axis_range` is DELIVER's to write and to pair with its Hypothesis property (ADR-025 split — DISTILL owns ATs, DELIVER owns the paired PBT); importing the unbuilt `core/axis.py` would manufacture a BROKEN where none exists today, so the test-side oracle `expected_range` lives in `steps/composition.py` and the ATs stay RED until production agrees with it. Seeds were calibrated against the **production** series before any bound was written: the Kalman smoother compresses a 0.25–0.3 kg/wk raw decline to ~0.7–0.9 kg of trend at 1M (35 % of a 2.5 kg band), so the "clearly sloped" scenario seeds 0.4 kg/wk (47 %) and asserts ≥ 40 %; raw entries are 0.1 kg-precise, so DISCUSS's 77.15/77.32 midpoint example becomes 77.1/77.4 (midpoint 77.25 → 76.0…78.5, same clean-bounds intent).

AT-completeness audit (`nw-at-completeness-check`, 15 items): **15/15 — COMPLETE**. Asserted: C1a (empty window, empty record), C1b (single value; span exactly 2.0 = branch boundary; 0.6/1.2 kg below it), C2a (documented in the step module: not a state machine — a pure projection with two branches), C3 (0/1/many), C4a (identical reloads of a pure read), C5a+C5b (lens × scale tour; the rule invariant, selection preserved), C6b (`null` on nothing plotted), C6c (closed wire shape `[lo, hi]` asserted on every read). Not applicable with rationale: C2b/C4b (no states, no inverse op — read-only projection), C6a (the field has no input; `scale`/`today` malformed inputs are shipped-AT territory), C7a/b/c (pure arithmetic inside an already-served atomic read; store failure is pinned by the shipped "series read admits trouble"). Zero `SPECIFICATION_AMBIGUITY` findings; audit log: `(y-axis-floor, C1–C7, 0 findings, none)`.

**Deliberately not asserted (client-structural, dogfood-verified — the client-paint precedent D-15):** `graph.js` handing the pair to uPlot's `scales.y.range`, the D-31 shape guard (absent / `null` / `[77]` / `["a","b"]` / `[78.5, 76.0]` ⇒ uPlot's own range, never a blank chart), the absence of numeric rule literals in the engine, uPlot's rendered gridlines, and the `sw.js` `SHELL_CACHE -v5` bump. A browser-less suite cannot falsify what a script does with a number; that is exactly why DESIGN moved the arithmetic server-side, where these scenarios pin it. The "same axis on `/` and `/graph`" clause is parity by construction (ADR-008 — both surfaces fetch the same two URLs; R-2) and carries no second assertion.

### [REF] Walking Skeleton Strategy

**N/A — brownfield (locked D2).** The production vertical and its `@walking_skeleton` scenario (`walking-skeleton.feature`, green) exist; this feature rides them. No strategy negotiation performed; the project policy is inherited unchanged.

### [REF] Adapter Coverage

**No new driven adapters (DESIGN: explicitly none)** ⇒ no new `@real-io` adapter scenarios owed, no new Earned-Trust probes, no schema migration, no new event. Fault-injection coverage per DESIGN's list:

| Fault (DESIGN) | Scenario |
|---|---|
| Nothing plotted ⇒ `y_range` is `null`, key present | An empty window offers no axis; An empty record invites, and offers no axis |
| Garbled pair on the wire ⇒ engine falls back to uPlot's own range | Structural (engine guard, R-3) — the server side is closed by every scenario's read: a pair that is not two finite numbers with `lo < hi` fails `AxisService._band` |
| Series read fails ⇒ chart admits trouble, entry unaffected | Shipped (`A graph hiccup never blocks the log`, milestone-8) — untouched |

### [REF] Driving Adapter Coverage

Every DESIGN entry point exercised over its real protocol (TestClient = the real ASGI/HTTP layer):

| Entry point (DESIGN) | Scenarios |
|---|---|
| `GET /entries?scale=` — additive `y_range` over the windowed raw values | A raw week is noise inside a band; A missing day stays a gap…; Axis bounds are clean numbers; A lone entry…; An empty window…; An empty record…; Exactly two kilograms…; Toggling lens or scale… (raw half of the tour) |
| `GET /trend?scale=` — additive `y_range` over the windowed trend values | A stalled month reads flat; A real month of loss still slopes; A long window keeps its ordinary range…; A perfectly steady week…; The axis frames the line…; both empty scenarios (trend half); Toggling lens or scale… (trend half) |
| `GET /graph?view=&scale=` — unchanged; the tap that chooses a lens/scale | every `he views the … lens at` step opens it first; the tour asserts `data-view`/`data-scale` survive each tap |
| `GET /` — unchanged (the front page fetches the same two URLs) | not re-asserted (parity by construction, ADR-008) |

### [REF] Scaffolds

**Zero production scaffold files needed (Mandate 7 satisfied structurally).** Acceptance tests reach the SUT exclusively over HTTP through the production composition root; no test imports an unbuilt production module (the oracle is test-side by design), so there is no ImportError surface and no BROKEN class. The RED anchors are HTTP-observable absences (see § RED Gate). Test-side infrastructure added — import-clean, every step defined: `steps/steps_honest_axis.py` (19 decorators), `AxisService` + `expected_range` + `AxisReading` + `seed_plateau` / `seed_mornings` in `steps/composition.py`, binding `steps/test_milestone_11.py`, typed vocabulary `AxisBand` / `parse_kg_list` in `steps/domain_types.py` (`ViewMode` / `TimeScale` reused as the lens/scale nouns — no raw strings), marker `us_015` in `pyproject.toml`.

### [REF] Test Placement

`tests/weight-trend-tracker/acceptance/` — the project's single acceptance tree (milestone-N precedent, features 1–10 landed the same way; `pythonpath` already pinned in `pyproject.toml`). Tier B not declared: the journey is one read per scenario (no ≥ 3-scenario chained mutation), and the generative exploration of the rule belongs to the pure-core PBT DELIVER owes.

### [REF] Executable Contracts (DELIVER pre-requisites)

The oracles pin these shapes — the crafter implements TO them:

- **Key name**: `y_range`, on BOTH `GET /entries` and `GET /trend`, **always present**: `[lo, hi]` (two JSON numbers, `lo < hi`) when ≥ 1 value is plotted, `null` when nothing is. Every other key (`entries`, `invite_first_log`, `points`) byte-identical.
- **Input**: the exact windowed series the route already returns — `weight_kg` of `shown` for raw, `trend_kg` of `points` for trend. Gap nulls never reach the rule.
- **Arithmetic** (ADR-012 § Range Rule, mirrored by `expected_range` in the test composition): `span = max − min`; `span < 2.0` ⇒ `lo₀ = mid − 1.0`, `hi₀ = mid + 1.0` (no extra pad); `span ≥ 2.0` ⇒ `lo₀ = min − 0.1·span`, `hi₀ = max + 0.1·span`; then `lo = ⌊2·lo₀ + ε⌋/2`, `hi = ⌈2·hi₀ − ε⌉/2`, `ε = 1e-9`. Span **exactly** 2.0 is the ordinary branch (76.0/78.0 ⇒ `[75.5, 78.5]`, not `[76.0, 78.0]`).
- **Constants**: `FLOOR_KG = 2.0`, `GRID_KG = 0.5`, `AUTO_PAD_FRACTION = 0.1` in `core/axis.py` and nowhere else; `graph.js` carries no numeric literal for the rule.
- **Pinned answers the scenarios expect**: 1M trend of a wobbling 77.2 plateau ⇒ `[76.0, 78.5]`; raw week 76.8…77.4 ⇒ `[76.0, 78.5]`; a steady 77.0 week ⇒ `[76.0, 78.0]` in both lenses (the ε rule: no spurious 75.5); a lone 77.2 ⇒ `[76.0, 78.5]`; 6M trend spanning ~4.7 kg ⇒ the padded range snapped (`[76.5, 82.5]` for the seeded decline).
- **Series untouched (G-3)**: the plotted values equal `trend_series_in` / `entries_in_window` over the current record, before and after — the axis rides beside the line.
- **Reads stay pure**: every view/tour asserts the shared universe (record, frozen counters) unchanged across the reads (Mandate 8); no new event.

### [REF] Inherited-AT Renegotiations (never silent)

**None.** Verified by grep across `tests/`: no shipped scenario, step or property asserts the exact key set of the `/entries` or `/trend` body (every reader indexes by key), so the additive `y_range` key breaks nothing; the shipped window/gap/palette/determinism scenarios stay green unchanged (full suite 219 passed before and after). No step-method wording changed; the two amended outcome shapes (OUT-2 / OUT-3) are additive.

### [REF] RED Gate

`docs/feature/y-axis-floor/distill/red-classification.md`: **12 RED (all `MISSING_FUNCTIONALITY`, AssertionError only — the read carries no `y_range`) / 1 GREEN-preserved / 0 BROKEN**, over 13 executions. Each RED fails at the FIRST axis clause of its scenario after every shipped clause before it (gap read, first-log invite) has passed. One authoring defect was caught before the first run (a "struck from his record" step — deletion is out of scope; the gap is now seeded around an absent day with shipped vocabulary). Two mechanical guards accompany the gate: a wrong-GREEN simulation (scratch plugin injecting the oracle's band at the read boundary, `src/` untouched) under which all 13 go green, and seed calibration against the production series for every pinned bound. Full suite: **219 passed, 13 `@pending` skipped** — pass count unchanged from the baseline.

The single GREEN-preserved scenario ("The axis frames the line and never moves it") is the honest signature of this feature: D2/D-32 pin it as a presentation delta beside a **shipped** series, so the guard that the plotted values are byte-identical must already pass; it is kept as the G-3 regression guard through the enrichment.

### [REF] Registered Outcomes

**OUT-12** (specification: y-axis range rule — pure projection over the plotted values: ≥ 2.0 kg visible span, floor widens never clips, bounds snapped outward to 0.5 kg; related OUT-2, OUT-3, OUT-5) added to `docs/product/outcomes/registry.yaml`; **OUT-2** and **OUT-3** output shapes amended with the additive `y_range: [lo, hi] | null`. Registered manually: `nwave-ai outcomes register` still fails on the mis-packaged `schema.json` (documented upstream tool defect, OUT-7…OUT-11 precedent). `nwave-ai outcomes check-delta` re-check remains owed once fixed upstream (DESIGN's run: 0 collisions, OUT-12 expected-missing warning now resolved).

### [REF] SSOT Updates

`docs/product/kpi-contracts.yaml`:

- **KPI-9 added** (stalled-reads-stalled: 0 false-alarm reactions / 100 % stalled windows read flat over 7 dogfood mornings; self-reported, `gate: soft`, KPI-6 precedent). No instrument: a render rule emits nothing (ADR-009); the arithmetic is AT/PBT-pinned, dogfood measures the constants' taste (OQ-12/OQ-14) — a false alarm retunes `FLOOR_KG`/`GRID_KG` in one line.
- **`events:` trail note** — no new event, no payload change; both reads stay pure (OUT-9), KPI-3 purity untouched.
- **G-3 link** — "The axis frames the line and never moves it" + the DELIVER-owed pure-core PBT; **G-2** — no new scenario owed (zero added fetches/scripts/taps, D-32); **KPI-3** — no link, purity structural.

Mandate-12 evidence (four criteria): (1) `steps/domain_types.py` exists and gains `AxisBand` + `parse_kg_list`; lens and scale reuse the shipped `ViewMode` / `TimeScale` enums; (2) every `AxisService` / seeding signature is typed (`ViewMode`, `TimeScale`, `AxisBand`, `Sequence[float]`, `date`) — no raw `str` where an enum exists; (3) all 19 step bodies are ≤ 2 statements, zero control flow, every assertion in `AxisService`; (4) step-reuse ratio (informational): **66 step invocations / 19 new decorators ≈ 3.47×**, with 21 of the 66 invocations bound to shipped vocabulary (record seeding, gap read, invite, identical reloads, background) — projection-shaped feature, natural ceiling consistent with prior features (3.28× for entry-date-picker).

### [REF] Pre-Requisites for DELIVER

None blocking. Single slice. DELIVER owes:

1. `src/weight_tracker/core/axis.py` — `y_axis_range(values) -> AxisRange | None` with the three constants, **plus its paired Hypothesis property** in `tests/weight-trend-tracker/acceptance/properties/` (containment, ≥ 2.0, 0.5-grid, floor-band width 2.0–3.0 and centre within 0.25, exact ordinary-range formula at/above the floor, order invariance, `None` iff empty; `@example`s for DESIGN rows 1–8). ADR-025 split: the ATs pin the boundary, the PBT pins the arithmetic.
2. `web/routes.py` — one `axis_range_wire` helper beside `entry_wire_pair`; `y_range` on both reads from the exact windowed series; every other key untouched.
3. `graph.js` — consume `y_range` through the D-31 shape guard (`scales: { y: { range: () => [lo, hi] } }` only for two finite numbers with `lo < hi`; otherwise omit); no numeric rule literal; dogfood-verified with the fault list (absent / `null` / `[77]` / `["a","b"]` / `[78.5, 76.0]` ⇒ uPlot's own range, never a blank chart).
4. `sw.js` — `SHELL_CACHE -v4 → -v5` (pre-cached `graph.js` changed); APP_SHELL list unchanged.
5. Mutation gate ≥ 80 % scoped to `core/axis.py` + `web/routes.py` (CLAUDE.md per-feature strategy).
6. Dogfood on the real ~77 kg plateau next morning: ambient glance on `/`, then 1M + 1W in both lenses and 6M on `/graph`; KPI-9 self-report starts.

### [REF] Final Wave Review Gate

Four reviewers dispatched in parallel (Haiku), 2026-09-04.

| Reviewer | Wave | Verdict |
|---|---|---|
| Eclipse (`nw-product-owner-reviewer`) | DISCUSS | **approved** — 0 blocker / 0 high / 0 low. DoR 9/9 with evidence; JTBD traceability intact (US-015 → `js-2-judge`, secondary `js-4-glance`); elevator pitch triplet complete; slice carries one user-visible story; zero LeanUX antipatterns; all 8 DISCUSS ACs mapped to DISTILL scenarios; DISCUSS↔DESIGN checked decision by decision (D6→D-30, D7→D-27/D-32, D8→D-28, D9→D-30/D-31, A28 refined per § Changed Assumptions, A29 resolved) — zero contradictions. |
| Architect (`nw-solution-architect-reviewer`) | DESIGN | **approved** — 0 blocker / 0 high / 0 low. Reuse Analysis hard gate passes (one CREATE NEW, `core/axis.py`, justified on the ADR-006 `core/glance.py` precedent); D-27…D-32 grounded in ADR-012; hexagonal boundary holds (pure core, additive route enrichment, `ports.py` untouched, read-only ports gain no methods); § Range Rule rows 3, 7, 8 re-derived by hand and confirmed; A28 quoted verbatim in § Changed Assumptions; C4 L1/L2 unchanged; `SHELL_CACHE -v5` recorded. |
| Forge (`nw-platform-architect-reviewer`) | DEVOPS/platform | **conditionally approved** — 0 blocker / 0 high / 2 medium / 1 low. External validity PASS on all four dimensions (deployment path: shipped CI/CD; observability: KPI-9 soft + G-2/G-3/G-5 hard; rollback: stateless delta, blue-green; security: zero new routes/origins/deps). Both medium findings are *"the production code does not implement this yet"* — `core/axis.py` + `y_range` wiring absent (the twelve RED anchors) and `SHELL_CACHE` still `-v4` — i.e. the intended DISTILL state, accepted as DELIVER work items restating § Pre-Requisites, not DISTILL defects. Low: OQ-12/OQ-14 constants remain a dogfood bet with a documented one-line retune path. Conditions carried into DELIVER: all 13 milestone-11 scenarios green with the suite unregressed; mutation gate ≥80 % on `core/axis.py` + `web/routes.py`; `/healthz` smoke on first deploy; KPI-9 7-morning self-report recorded. |
| Sentinel (`nw-acceptance-designer-reviewer`) | DISTILL | **approved** — 0 blocker / 0 high / 0 low. Gherkin business-language purity clean across 13 scenarios; entry only through `build_app` over real HTTP; no import of the unbuilt `weight_tracker.core.axis`; Mandate-12 step bodies ≤2 statements, typed parameters, logic in `AxisService`; Mandate 7 satisfied structurally (zero scaffolds, oracle test-side); Mandate 8 read-purity universe guarded; `expected_range` oracle verified non-tautological against § Range Rule rows 1–8; RED gate valid (12 `MISSING_FUNCTIONALITY` / 1 GREEN-preserved G-3 guard / 0 BROKEN); four `@property` scenarios example-pinned at layer 3 (Mandate 9/11); error share 54 %. |

**Cross-wave consistency**: no reviewer surfaced a contradiction another wave's approval concealed; the one refinement in the chain (A28 → D-28 explicit 10 % pad) is documented and pinned by the ATs. Deliverable-type routing: `application` ⇒ no plugin/skill reviewers (N/A). **Gate: PASSED — handoff to DELIVER unblocked.**

## Wave: DELIVER

Executed 2026-09-04 18:34Z → 19:14Z by the nw-deliver orchestrator + `nw-functional-software-crafter` (ADR-005 paradigm, CLAUDE.md routing). 3 roadmap steps across 2 phases, all 3-phase RED→GREEN→COMMIT (ADR-025); DES integrity `exit 0`, "All 3 steps have complete DES traces". Density: lean, Tier-1 `[REF]` only; density telemetry skipped (`scripts/shared/telemetry.py` absent).

### [WHY] Upstream Issues

Three. None is a defect in this feature's shipped code; all three are recorded so the upstream reasoning is corrected before the next feature repeats it.

1. **DISTILL's "Inherited-AT Renegotiations: None" was incomplete — one pin was guaranteed to red.** `properties/test_date_row_dress.py:142` (entry-date-picker's finalize) asserted `SHELL_CACHE == "weight-tracker-shell-v4"` by exact name, and DESIGN D-32 / DISTILL Pre-Requisite 4 mandated `-v5`. DISTILL's sweep looked for readers of the `/entries` / `/trend` body key set — the surface this feature *adds* — and missed the value this feature was *told to change*. Found by the roadmap reviewer, pre-approved as a documented renegotiation, amended in `27c49dc` (02-01) with the intent stated in the test's docstring: the pin means "the cache MOVES when a pre-cached response changes", and it moved again. Correction to carry forward: a renegotiation sweep must cover every shipped assertion over a value the feature is mandated to change, not only the wire shape it extends; and an exact-name pin on a cache version makes every future bump a renegotiation by construction — worth loosening to "moved past the previous name" the next time `sw.js` is touched (not changed here).
2. **The demo's "empty window" probe did not probe an empty window.** The Phase 3.5 script claimed `today=2026-01-10` on `GET /entries?scale=1W` to reach a week before the seeded record, but the device-day claim is skew-clamped by design (`day_frame_or_bad_request`, A5) — the server framed the current week and answered 7 entries, `[76.0, 78.5]`. The empty case is pinned by the two AT scenarios ("An empty window offers no axis", "An empty record invites, and offers no axis"), not by the demo. Recorded honestly: the demo evidence below carries no empty-window read. Correction: an empty-window demo needs a record with a real gap inside the skew frame — the claim cannot move the window, which is precisely the property the clamp exists to guarantee.
3. **Persona SSOT is stale on the one number this feature is about.** `docs/product/personas/clemens.yaml` still reads "typical weight range around 82 kg" while the production record sits at ~77 kg; DISCUSS noted the move in § Persona ID and used the 77.x range for every example, but did not edit the persona. Owned by DISCUSS; not fixed here.

### [REF] Implementation Summary

Shipped US-015 as one slice: both surfaces, both lenses, every scale now render on an honest y-axis — a minimum visible span of 2.0 kg, bounds snapped outward to the 0.5 kg grid — so a plateaued month reads as a calm near-flat stroke instead of re-amplified noise (`js-2-judge`, secondary `js-4-glance`). **Pure core (ADR-012, D-27…D-30)**: `core/axis.py` — `FLOOR_KG = 2.0`, `GRID_KG = 0.5`, `AUTO_PAD_FRACTION = 0.1`, `SNAP_EPSILON = 1e-9` defined there and nowhere else; frozen `AxisRange(lo_kg, hi_kg)`; `y_axis_range(values) -> AxisRange | None`, total, clock-free, order-invariant — `None` on nothing; below the floor `[mid − 1.0, mid + 1.0]`; at or above it `[min − 0.1·span, max + 0.1·span]`; then `⌊2x + ε⌋/2` / `⌈2x − ε⌉/2`, exact half-integers on the wire. **Shell (D-31)**: one `axis_range_wire` helper beside `entry_wire_pair` is the ONE place the pair becomes `[lo, hi]` / `null`; `GET /entries` and `GET /trend` each gained the additive, always-present `y_range` key over the exact windowed series they already return; every other key byte-identical (G-3 guard green throughout). **Engine (D-31/D-32)**: `graph.js` gained a pure `isAxisPair` guard (array, length 2, all finite, `lo < hi`) and `renderChart(data, lineOptionsFor, yRange)` spreads `scales: { y: { range: () => yRange } }` only when it passes — otherwise uPlot's own range, an imperfect axis, never a blank chart; `showRaw` / `showTrend` pass `history.y_range` / `trend.y_range`; no constant, no arithmetic in the client. `sw.js` `SHELL_CACHE -v4 → -v5` because the pre-cached `graph.js` changed; `APP_SHELL` list unchanged. Zero port-protocol changes (`ports.py` untouched, read-only ports gain no methods), zero new adapters, routes, assets, dependencies, external origins, probes, events or migrations.

### [REF] Files Modified

**Production — 4 files, `14a3d14..472667b` over `src/` (8 files, +491/−23 including tests):**

- `src/weight_tracker/core/axis.py` — **NEW** (79 lines): the four constants, frozen `AxisRange`, `y_axis_range` + `_unsnapped_bounds` / `_floor_band` / `_padded_range` / `_snap_outward` (the L1–L6 pass merged the two snap helpers into one `_snap_outward` over a `_Bounds` alias).
- `src/weight_tracker/web/routes.py` — `axis` import; `axis_range_wire(axis) -> list[float] | None` beside `entry_wire_pair`; `y_range` on the history handler over `weight_kg` of `shown` and on the trend handler over `trend_kg` of `points`; one docstring line.
- `src/weight_tracker/web/static/graph.js` — `isAxisPair` guard + comment naming ADR-012/D-31; third `renderChart` argument and the conditional `scales` spread; two call sites pass the served pair.
- `src/weight_tracker/web/static/sw.js` — `SHELL_CACHE` → `weight-tracker-shell-v5` with a v5 comment in the shipped v4 style; `APP_SHELL` unchanged.

**Tests — 4 files:** `acceptance/milestone-11-honest-axis.feature` (13 `@pending` removed across the three steps — 5 / 7 / 1; DISTILL-authored, never re-authored); `properties/test_axis_range_properties.py` (**NEW**, DELIVER-owed paired Hypothesis suite, 17 tests: containment, ≥ 2.0, half-kg grid, floor-band width and centre, exact ordinary formula, order invariance, `None` iff empty, the ADR-012 constants pin, the `@example` rows 1–8, and `test_the_axis_is_an_immutable_value` added at `472667b`); `properties/test_axis_engine_wiring.py` (**NEW**, source-inspection pin over `graph.js` + `sw.js`: `y_range` reference, guard clauses present, no standalone rule literal, `-v5` with APP_SHELL intact — `# bypass:` documented, no JS runner); `properties/test_date_row_dress.py` (the `-v4 → -v5` pin renegotiation, [WHY] 1). Step definitions, `AxisService` + `expected_range` oracle, `domain_types` vocabulary and the `us_015` marker were DISTILL-authored and landed at `14a3d14`.

**Docs:** this file; `deliver/{roadmap,execution-log}.json`; `deliver/mutation/mutation-report.md`; `distill/red-classification.md`; `slices/slice-01-y-axis-floor.md`; `docs/evolution/2026-09-04-y-axis-floor.md`. SSOT — `docs/product/architecture/brief.md` (y-axis-floor delta paragraph + ADR index at DESIGN; Component Inventory paragraph at finalize), `adr-012-y-axis-range-rule.md` (DESIGN, permanent, unchanged here), `kpi-contracts.yaml` (KPI-9 + trail note + links at DISTILL; KPI-9 and G-3 baselines at finalize), `outcomes/registry.yaml` (OUT-12, OUT-2/OUT-3 amendments at DISTILL), `jobs.yaml` / `journeys/daily-weight-tracking.yaml` (DISCUSS).

### [REF] Scenarios Green

**13 of 13 milestone-11 scenarios green (13 executions), zero `@pending` remaining** — 5 unskipped at 01-01, 7 at 01-02, 1 at 02-01 (the lens × scale tour, inherited GREEN-preserved regression clause). Full suite: **255 passed, 0 skipped, 0 failed** at HEAD `472667b`, verified 2026-09-04 (`uv run pytest -q`); baseline 219 → 255 = the 13 scenarios + the 17-test property file + the engine-wiring file. Inherited suites green throughout, including the one consciously renegotiated pin ([WHY] 1). `mypy --strict`, ruff, import-linter (`core → shell/web` forbidden — covers `core/axis.py` by package), `node --check` on both scripts all clean; zero `__SCAFFOLD__` markers.

### [REF] DoD Check

| # | DoD item (DISCUSS) | Status |
|---|---|---|
| 1 | All UAT scenarios green (automated), incl. the @property honesty scenario | **PASS** — 13/13 milestone-11, zero `@pending`; the honesty property is a real Hypothesis test over `y_axis_range` (17 tests) |
| 2 | Supporting tests green; existing graph ATs (window, gaps, palette) unchanged and green | **PASS** — full suite 255 passed; no shipped scenario or step moved; the one renegotiated pin is documented, never silent |
| 3 | Code refactored; per-feature mutation gate ≥80 % on modified files | **PASS** — L1–L6 pass (`643703f`) + mutation 85.8 % raw / 99.6 % effective as run, 100 % after the one survivor was closed (`472667b`) |
| 4 | Code reviewed (self-review with reviewer agent) | **PASS** — `nw-software-crafter-reviewer` **APPROVED, zero findings** |
| 5 | Merged to main | **PASS (locally)** — 5 feature commits + this finalize on `main`, trunk-based; push is a separate user decision because it triggers the deploy pipeline |
| 6 | Deployed to the phone-reachable production URL via the existing pipeline | **OPEN — owned by the user.** Runs on the push; `/healthz` smoke on first deploy (Forge's condition). The local live-server demo below is a server-side proxy, not the deploy |
| 7 | Dogfooded next morning: ambient glance on `/` over the real record, then 1M and 1W (both lenses) on `/graph`; self-report recorded | **OPEN — owned by the user.** Follows the deploy: ambient glance on `/`, 1M + 1W in both lenses + 6M on `/graph`, confirm the `-v5` shell pickup, walk the D-31 fault list (absent / `null` / `[77]` / `["a","b"]` / `[78.5, 76.0]` ⇒ uPlot's own range, never blank), start the KPI-9 7-morning self-report. This is the falsification test for OQ-12 / OQ-14 (2.0 kg / 0.5 kg) |
| 8 | Guardrails verified: ≤2 s interactive, zero added scripts/origins/taps, AA both schemes, `/stats` counters unmoved by renders | **PASS** — no event, no instrumentation needed (KPI-9 is self-reported); demo `/stats` after the series reads showed `trend_study_this_week 1` (the one deliberate `/graph` open) and `home_graph_shown 1` — pure reads added nothing; zero added fetches/scripts/origins by diff; G-2/G-4/G-5 shipped CI gates green |
| 9 | Story demonstrable end-to-end on the phone | **OPEN — owned by the user.** The evidence below is a real-uvicorn, real-SQLite, real-HTTP demonstration; the on-phone demonstration follows the deploy |

Items 1–5 and 8 satisfied. **Items 6, 7 and 9 OPEN**, owned by the user, and deliberately not marked done: no local run substitutes for the deploy, the dogfood, or the phone.

### [REF] Demo Evidence

Phase 3.5 hard gate, 2026-09-04. Captured from a **real `uvicorn` process on 127.0.0.1:8812 over a temp SQLite DB, driven by `curl`** — not the TestClient harness. 183 entries seeded: a six-month decline 82.1 → 77.3 kg, then a stalled month wobbling 77.1–77.3.

- `GET /healthz` 200; `POST /login` → `{"status":"unlocked"}`.
- **The Elevator Pitch's exact "sees"** — `GET /trend?scale=1M` → 30 points, min 77.227 / max 77.413, **span 0.185 kg**, `y_range [76.0, 78.5]`: the stalled month sits as a ≤ 10 %-height stroke inside a clean 2.5 kg band.
- **Raw week is noise in a band** — `GET /entries?scale=1W` → 7 values `77.2, 77.3, 77.1, 77.2, 77.2, 77.2, 77.1`, `y_range [76.0, 78.5]` — the same band in the other lens.
- **Long window keeps its ordinary range with clean edges** — `GET /trend?scale=6M` → 182 points, 77.227…81.799, span 4.572 ≥ floor, `y_range [76.5, 82.5]` (padded 10 % each side, snapped outward; the DISTILL-pinned answer for the seeded decline).
- **Empty-window probe — caveat** — `GET /entries?scale=1W&today=2026-01-10` returned the current week (7 entries, `[76.0, 78.5]`): the out-of-skew claim was clamped by design. The empty case is AT-pinned, not demo-pinned ([WHY] 2).
- `GET /graph` 200; `GET /` mounts `#home-graph` (1) — both surfaces fetch the same two URLs.
- **Served assets** — `graph.js` carries `y_range` (2 refs) and the `scales` / `range` wiring (4 refs); `/sw.js` names `weight-tracker-shell-v5`.
- **KPI-3 purity** — `GET /stats` after the series reads: `trend_study_this_week 1` (the one deliberate `/graph` open), `home_graph_shown 1` (the one `GET /`); the four series reads added nothing.

### [REF] Quality Gates

| Gate | Outcome |
|---|---|
| Roadmap review | **Approved** — `nw-acceptance-designer-reviewer` (Sentinel) + orchestrator gate, 0 blockers / 0 high; 13 scenarios owned exactly once (5 + 7 + 1); 02-01's RED anchor = source-inspection test, the tour attached as an inherited GREEN-preserved clause; the `-v4` pin renegotiation caught here ([WHY] 1); `des-verify-integrity --roadmap-only` exit 0 |
| Per-step TDD (3-phase canon, ADR-025) | **3/3 COMMIT PASS** — `246ff85`, `e4b305d`, `27c49dc`; DES 9/9 events (RED/GREEN/COMMIT × 3) |
| Design compliance | **PASS** — D-27…D-32 honored verbatim: constants in `core/axis.py` only, engine carries no rule literal (pinned by `test_axis_engine_wiring.py`), `ports.py` untouched, series byte-identical (G-3 scenario green before and after), key always present / `null` iff nothing plotted |
| Post-merge integration (3.5) | **PASS** — full suite green + the real-uvicorn/real-SQLite/real-curl demo above |
| Refactor L1–L6 (`643703f`) | **PASS** — `_snap_outward` merge over a `_Bounds` alias, docstring/comment accuracy, PBT strategy fold; 254 green throughout; ruff + `mypy --strict` + import-linter clean |
| Adversarial review (`nw-software-crafter-reviewer`) | **APPROVED — zero findings.** § Range Rule rows 1 / 5b / 7 / 8 re-derived by hand; Testing-Theater 7-pattern scan clean; FC/IS placement confirmed (pure core, wire phrasing in the shell, guard-only client) |
| Mutation (per-feature, cosmic-ray 8.4.3) | **PASS — 224/261 = 85.8 % raw; 224/225 = 99.6 % effective as run; 225/225 = 100 % after the survivor was closed.** 261 executed (git-filter over the delta: `core/axis.py` 237, `routes.py` 24), 36 argued equivalents (33 lazy-annotation `BitOr`, 3 constant-exact floor divisions). The one genuine survivor — `frozen=True → False` on `AxisRange` — was a value-object pin, closed test-side by `test_the_axis_is_an_immutable_value` (`472667b`) with zero production change. `graph.js` / `sw.js` outside the mutable surface (JS), wiring pinned textually. `deliver/mutation/mutation-report.md` |
| Integrity verification | **PASS** — `des-verify-integrity docs/feature/y-axis-floor/deliver/` exit 0, "All 3 steps have complete DES traces" |

### [REF] Pre-Requisites

Five of DISTILL's six pre-requisites discharged: **(1)** `core/axis.py` + its paired Hypothesis property (`test_axis_range_properties.py`, `@example` rows 1–8, the R-1 oracle in full); **(2)** `axis_range_wire` beside `entry_wire_pair`, `y_range` on both reads, every other key untouched; **(3)** `graph.js` consumes the pair through the D-31 guard, no rule literal — the fault list itself is owed to dogfood (DoD 7); **(4)** `SHELL_CACHE -v5`, `APP_SHELL` unchanged; **(5)** mutation gate ≥ 80 % on `core/axis.py` + `routes.py` — cleared at 85.8 % raw, 100 % effective. **(6) Dogfood on the real ~77 kg plateau remains OPEN**, user-owned (DoD 7), together with Forge's `/healthz` smoke on first deploy (DoD 6) and the KPI-9 7-morning self-report (recorded as `pending-dogfood` in `kpi-contracts.yaml` baselines).

Consumed from upstream: DISTILL's 13 scenarios + test-side oracle as the authoritative executable spec (implemented TO `expected_range`, never imported); DESIGN D-27…D-32 verbatim; ADR-012 (ADR-001…011 unchanged, none superseded); DISCUSS D6–D9 at their defaults (OQ-12 / OQ-13 / OQ-14 unretuned — the dogfood decides). Still owed upstream and **not** closed here: the persona weight line ([WHY] 3) and the `nwave-ai outcomes check-delta` re-check, still blocked by the mis-packaged `schema.json` (OUT-7…OUT-12 precedent; OUT-12 registered manually at DISTILL).
