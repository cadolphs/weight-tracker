<!-- markdownlint-disable MD024 -->
# Feature Delta: numeric-trend-history

## Wave: DISCUSS

### [REF] Persona ID

`clemens` — see `docs/product/personas/clemens.yaml`. Sole customer, sole user, sole developer. Phone-first, half-awake at 06:45, metric units, 0.1 kg scale. The record has moved since the persona was written (~82 kg in July → ~77 kg in September 2026); domain examples below use the production 77.x kg range.

### [REF] JTBD One-Liner

Job `track-true-weight-trend` (`docs/product/jobs.yaml`, status: validated). This feature extends the **judging moment** (`js-2-judge`: *"see a smoothed trend line that absorbs water-weight noise — so I can decide whether to adjust anything based on real movement, not noise"*). Today the trend is a **number exactly once** — the glance line, for today only — and a **shape** everywhere else. "Where was my trend three weeks ago, and how far has it moved since?" is a question about two numbers, and the product currently answers it by asking the user to read pixels off a curve. Secondary moment `js-4-glance` (the front-page recent list sits under the same ambient glance).

**Bridge decision**: **no new job-story moment.** The job statement already names the outcome ("judge real progress"); the entries lists are an existing surface gaining the number they were always missing beside the raw one. A dated note on `js-2-judge` and the feature-list entry in `jobs.yaml` record the delivery (js-3/js-4/js-5/y-axis-floor precedent; no JTBD re-run).

### [REF] Locked Decisions

- **D1** Feature type: user-facing (presentation of the two entries lists).
- **D2** Walking skeleton: NO — brownfield; both lists ship today, the smoothed series ships today; this is a column added to an existing rendering.
- **D3** UX research depth: lightweight — journey delta on steps 1–2 (screen sketch, failure modes), single persona.
- **D4** JTBD: bridge only to existing validated job `track-true-weight-trend`, primary moment `js-2-judge`, secondary `js-4-glance`; no re-analysis.
- **D5** Density: mode=lean (Tier-1 [REF] only), expansion_prompt=ask-intelligent (triggers evaluated — **none fired**, silent-lean).
- **D6** (user, pinned before DISCUSS) **Aligned columns, not an inline row and not a toggle.** Each entry becomes `Date | Raw | Trend`, numbers right-aligned in their own column. Rejected at the user's direction: a one-line row (`Fri 24 Jul — 82.2 kg · trend 82.4`), because scanning a column of trend values down the page is the whole point; and a Raw/Trend lens toggle over the list, because hiding one number to read the other defeats "how far has it moved from the noise".
- **D7** (user, pinned before DISCUSS) **Both lists change together.** The front page's last-7 list (`#recent-entries`, US-011) and the History page's complete record (`#history-entries`, US-012) share one row grammar today (`entry_row_text`). The grammar must not fork: one definition, two surfaces, exactly as ADR-008 holds for the chart engine.
- **D8** (user, pinned before DISCUSS) **The trend number is the existing smoothed series, looked up by day.** Derived from `trend_series` over the **FULL** entry set (ADR-004: derived, never stored; full-record smoothing), read at each entry's own day. No second algorithm, no stored column, no windowed re-smoothing. Every entry day is on the daily grid by construction (the grid spans first→last entry day), so the lookup is **total** — a row can never be missing its trend value for want of a grid point.
- **D9** **Semantic table, not a styled list.** Two columns of numbers under headers is tabular data: `<table>` with `<th scope="col">` headers, so a screen reader announces "Raw, 77.2" per cell instead of a run-on line. The mount ids `#recent-entries` and `#history-entries` are **kept** so the theme and the existing test hooks stay pointed at the same thing.
- **D10** **Each column renders at its own honest precision.** Raw at 0.1 kg, the scale's own resolution. Trend at **0.01 kg** — it is a *derived* value with real resolution below 0.1, and the filter is damped enough that a week of genuine movement is often only ~0.05 kg. A day's trend value is **one value** wherever it appears — the glance line's `Trend: 77.5 kg` is the top row's `77.48` at one decimal, never a second computation (A36). *Retuned at DELIVER dogfood (OQ-15 closed): the original 0.1 kg default printed the same digits down a whole front-page week on a genuinely declining record, which is the precise failure OQ-15 named as its falsifier.*
- **D11** **Retrospective revision is accepted, and is the point.** The RTS smoother revises past trend values when later entries arrive (ADR-004, deliberate), so yesterday's row may read 77.3 today and 77.2 tomorrow. This is honest — the column shows the best current estimate of the past, not a frozen guess — and it is exactly why the values are derived per read rather than stored. Named here so it is never mistaken for a defect.
- **D12** **Degrade to absent, never to stale or fake.** If the trend projection fails, both lists still render their raw column and the trend cells show nothing at all (never a zero, never a copy of the raw value, never a cached older number). The entry form and the save path are untouched — the `glance_or_degrade` precedent (D-13), applied to the lists.

### [REF] Scope Assessment

**PASS — 1 story, 1 bounded context (weight tracking / entries presentation), estimated ~0.5 day.** Oversized signals checked: stories 1/10; bounded contexts 1/3; walking skeleton N/A (exists); effort ≪ 2 weeks; user outcomes — one ("read the trend's history as numbers"). Two surfaces is an AC of that one outcome (D7), not a second story: splitting by surface would ship the row grammar twice, which is the specific thing D7 forbids. No signal fired; no split needed. Reference class: US-012 (complete record list on the History page) landed in well under a day; this adds one pure lookup and one column to that same rendering, plus the client-side repaint path US-011 already owns.

### [REF] Journey Summary

SSOT: `docs/product/journeys/daily-weight-tracking.yaml` — **screen-sketch and failure-mode delta on steps 1 and 2**; no new step, no new flow, no new tap. The `current_trend_display` shared artifact gains two consumers (the two lists); one new `integration_validation` rule (the trend number for a given day is one value across the glance line, both lists, and the chart). Changelog entry dated 2026-09-09.

- **Step 1 (Log today's weight)** — the last-7 list beneath the form gains its trend column. The exit emotion "done and oriented" sharpens: today's trend value stops being a lone number with nothing to compare against and becomes the newest of seven. Tap count, autofocus, keypad and the ≤2 s budget are unchanged; the values ride the `all_entries()` read the page already performs.
- **Step 2 (Review raw history)** — the complete record below the chart gains the same column. A deliberate History visit can now answer "how much has the trend actually moved since mid-August" by subtracting two printed numbers rather than by eye.
- **Step 3 (Judge the trend)** unchanged in mechanism; this feature is the numeric counterpart of the curve it already renders. Gains one failure mode: the list and the chart disagreeing about the same day.
- Emotional delta: the trend stops being something one *reads off a picture* and becomes something one can *quote*. For a plateau — the current production state — that is the difference between "it looks flat-ish" and "77.2, 77.2, 77.3, 77.2, 77.1".

### [REF] Story Map

Extends the existing map (same persona, same goal). No new activities; the story sits across the Review and Judge columns because one row grammar serves both surfaces.

| Capture weight | Review history | Judge trend | Maintain record |
|---|---|---|---|
| US-001, US-006, US-007, US-008, US-010 ✅ | US-001, US-002, US-009, US-011, US-012, US-015 ✅ | US-004, US-005, US-009, US-010, US-015 ✅ | US-003, US-013, US-014 ✅ |
| *(recent list gains the column)* | **The trend has a readable history (US-016)** | *(same numbers as the curve — one series)* | |

**Walking skeleton**: N/A — exists. **Slice** (elephant carpaccio, ~0.5 day, dogfooded next morning):

- **Slice 01** — `slices/slice-01-trend-column.md`: US-016 (one row grammar carrying both surfaces and the client-side repaint; splitting by surface would fork the grammar and break D7).

### [REF] Priority Rationale

Single slice — the priority question is only *whether now*. Yes: the record is plateaued around 77 kg, which is precisely the state where "is it moving at all?" needs digits rather than a shape, and where the just-shipped y-axis floor (US-015) deliberately makes small movement look small. The two features are complements: the chart now refuses to exaggerate, so the numbers must be available when the eye cannot resolve them. Value 4 (completes the noise-vs-signal judgment at the point of reading), Urgency 3 (user-requested today; the plateau is live), Effort 1 → score 12. MoSCoW: Must (explicit user request; D6–D8 pinned by the user before the wave opened).

### [REF] System Constraints

- **One series, one number** (G-3, ADR-004): the column shows values from the **same** smoothed series the chart plots and the glance line reports. No second algorithm, no rounding path that makes the same day read differently on two surfaces.
- **Derived, never stored** (ADR-004): the trend column is recomputed from the full entry set on every read. No schema change, no migration, no column in SQLite.
- **Read-only ports** (`WeightHistory`, `TrendProjection`) must never gain write methods (CLAUDE.md / ADR-005). Any per-day trend lookup is a **pure projection** of the `all_entries()` read the two pages already perform.
- **Functional core / imperative shell** (ADR-005): the day→trend lookup is pure core arithmetic; the row wording, the alignment and the markup are shell.
- **One row grammar, two surfaces** (D7, Mandate-12): exactly one definition of a row, consumed by `/` and `/graph` and by the client-side post-save repaint. Three renderers of the same row (server front page, server History, client repaint) must be provably in step.
- **Entry primacy** (KPI-1, G-2): zero added fetches, zero added scripts, zero added taps; entry screen interactive ≤2 s. The values come from the read already performed.
- **Phone-first legibility** (G-4): three columns must fit a 360 px viewport without horizontal scroll or truncated numbers; numerals tabular so the columns align on the decimal point; theme tokens only, AA contrast in both schemes (ADR-007). The header row is real markup (`<th scope="col">`), not a visual convention.
- **Metric only**: the unit label `kg` appears once per column header, not once per cell (`unit_label_kg` artifact gains a consumer, keeps a single source).
- **Zero new external origins** (G-5); no new script, no chart library involvement — the lists are plain server-rendered markup.
- **KPI-3 purity** (ADR-009): rendering a list emits no telemetry. Ambient front-page renders and post-save repaints add 0 to the deliberate-study counters by construction.
- **The History list stays the whole record** (D-17): the trend column is **not** windowed by the chart's selected scale. Tapping 1W changes the chart and nothing else, exactly as today.

### [REF] User Stories

All stories: `job_id: track-true-weight-trend`, moment `js-2-judge` (secondary `js-4-glance`). Persona: Clemens.

#### US-016: The trend has a readable history

`job_id: track-true-weight-trend` · Slice 01 · Must · ~0.5 day

##### Problem

Clemens can see his trend weight as a number for exactly one day — today, on the glance line. Every other trend value in his record exists only as a pixel on a curve. When the scale reads 77.6 on a Tuesday and 76.9 on a Wednesday, the question he actually wants answered is "what has the *trend* done over the last week, and over the last month" — a subtraction of two numbers. Today he answers it by squinting at a line whose y-axis was just deliberately widened (US-015) so that small movements look small. The entries lists sitting directly under both charts show the raw numbers he already distrusts, and nothing else.

##### Elevator Pitch

- **Before**: Opens `/` on Wed 9 Sep 2026 at 06:45. The glance line reads `Trend: 77.2 kg · ↓0.05 kg/week`. The list beneath the form reads `Tue 8 Sep — 77.6 kg`, `Mon 7 Sep — 76.9 kg`, … — seven raw values and no trend value but today's. To ask "where was the trend a month ago" he must open `/graph`, tap `1M`, and estimate a pixel height.
- **After**: Opens `/` → the list beneath the form is a three-column table, `Date | Raw | Trend`, and reads `Wed 9 Sep | 77.1 | 77.2`, `Tue 8 Sep | 77.6 | 77.2`, `Mon 7 Sep | 76.9 | 77.3` — the raw column jumping 0.7 kg while the trend column moves 0.1. Tapping **History** shows the same two columns for every day on record.
- **Decision enabled**: "Has the trend actually moved, and by how much?" — answered by subtracting two printed numbers instead of measuring a line, on the surface he is already looking at.

##### Domain Examples

Values below are the smoothed series for the stated entries; the exact digits DELIVER asserts come from the shipped Kalman+RTS parameters (ADR-004), not from these illustrations.

1. *Noisy week, steady trend* (front page, last 7): raw `77.1 / 77.6 / 76.9 / 77.4 / 77.0 / 77.3 / 77.2`, trend column reading within a 0.2 kg band across all seven rows. The raw column swings 0.7 kg; the trend column shows the swing was noise — the feature's whole reason for existing, now legible without a chart.
2. *Top row equals the glance* (front page): the newest row's trend cell and the glance line above it both read `77.2`. One number for one day, twice on one screen — never 77.2 above and 77.3 below.
3. *A month of real loss* (History page): rows from 9 Aug (`78.4`) to 9 Sep (`77.2`) — the trend column falls 1.2 kg monotonically enough to subtract, while the raw column crosses its own path a dozen times.
4. *Gap days stay gaps*: Clemens skipped 5 and 6 Sep. The lists show **no rows** for those days (entries, not calendar days — A18); the trend series has grid points for them, and those points are simply not rendered. A gap is never a row with a trend value and an empty raw cell.
5. *First morning*: a record of exactly one entry (`77.2`) renders one row with raw `77.2` and trend `77.2` — the smoother's diffuse-prior start is the observation itself. Not blank, not zero.
6. *Backfilled day, revised past* (D11): Clemens backfills Sun 6 Sep at 76.8 kg. After the save, the rows for 7, 8 and 9 Sep show trend values revised by up to ~0.1 kg from what they showed a minute earlier, and the 6 Sep row appears with its own trend value. The list repaints in place from the save response — no reload.
7. *Degraded trend* (D12): the trend projection raises. Both lists still render `Date | Raw` with every raw value intact and the trend cells empty; the save completes, the confirmation shows, the entry flow is untouched.

##### UAT Scenarios (BDD)

###### Scenario: A noisy week reads as a steady trend, in numbers

- **Given** Clemens's last seven entries are 77.1, 77.6, 76.9, 77.4, 77.0, 77.3 and 77.2 kg on consecutive days
- **When** he opens the entry screen
- **Then** the recent-entries list shows one row per entry with a date, a raw weight and a trend weight
- **And** the raw column spans at least 0.7 kg while the trend column spans at most 0.3 kg
- **And** every trend value equals the smoothed series value for that row's day

###### Scenario: The newest row and the glance line agree

- **Given** Clemens's smoothed trend for his most recent entry day is 77.2 kg
- **When** he opens the entry screen
- **Then** the glance line reads `Trend: 77.2 kg` and the top row's trend cell reads `77.2`
- **And** the same day's trend value on the History page reads `77.2`

###### Scenario: The whole record carries the column

- **Given** Clemens has 45 entries between March and September 2026
- **When** he opens the History page and taps **1W**
- **Then** the complete-record table below the chart still lists all 45 entries, newest first, each with its raw and trend value
- **And** the trend values are unchanged by the tap — the chart windowed, the record did not

###### Scenario: Missing days are absent, not empty rows

- **Given** Clemens logged nothing on 5 and 6 September 2026
- **When** he views either list
- **Then** no row exists for those two days
- **And** every rendered row has both a raw and a trend value

###### Scenario: A backfilled day revises the rows above it, in place

- **Given** the entry screen is open and the recent list shows 7, 8 and 9 September
- **When** Clemens selects 6 September, saves 76.8 kg, and the confirmation appears
- **Then** the list repaints without a reload to include 6 September with its own trend value
- **And** the trend values for 7, 8 and 9 September are recomputed from the record including the new entry

###### Scenario: A failing trend leaves the raw record standing

- **Given** the trend projection fails for this render
- **When** Clemens opens the entry screen
- **Then** the recent list still shows every raw value with its date
- **And** the trend cells are empty rather than zero, stale, or a copy of the raw value
- **And** the entry field is focused and the save path works exactly as before

###### Scenario: The columns line up and fit the phone (@property)

- **Given** any record, on either surface, in either colour scheme, at a 360 px viewport
- **When** a list renders
- **Then** the table has one header row naming Date, Raw and Trend with the kg unit stated once per weight column
- **And** the numbers are right-aligned on tabular figures so decimal points align down each column
- **And** no row wraps, is truncated, or forces horizontal scrolling
- **And** header and cell text meet AA contrast against the page background in both schemes

##### Acceptance Criteria

- Both entries lists render as a table with a header row (`Date`, `Raw`, `Trend`; `kg` stated once per weight column) and one row per **entry**, newest first, on `/` (last 7) and `/graph` (the complete record).
- Every rendered trend value is the smoothed-series value for that row's own day, computed from the **full** entry set (ADR-004) — equal, to the rendered precision, to the value the chart plots and, for the newest entry day, to the glance line.
- The raw column renders at 0.1 kg and the trend column at 0.01 kg; a day's trend value is the same value on the front page, the History page, the glance line and the chart, each at its own pinned precision.
- The History list stays the complete record at every time scale; selecting a scale changes the chart only.
- Missing days produce no row; a row never carries a raw value without a trend value, or a trend value without a raw value (except under degrade, below).
- After a save, the front-page list repaints in place from the save response — new row present, revised trend values above it, no reload and no extra fetch.
- Degrade-to-absent: a failing trend projection leaves both lists rendering their raw column with empty trend cells; no zero, no stale value, no copy of the raw value; entry and save are unaffected.
- One row definition serves both server surfaces and the client repaint; there is no second wording, no second precision rule, and no second lookup of a day's trend.
- Guardrails hold: zero added fetches, scripts, origins and taps on `/`; entry screen interactive ≤2 s; AA contrast in both schemes at 360 px; no telemetry emitted by rendering a list; entry store schema unchanged.

### [REF] Out of Scope

A per-row delta column (raw minus trend, or day-over-day change); sorting, filtering, paging or search over the lists; any per-row affordance — links, edit buttons, delete (looking is not touching, A18/D9 stand); CSV/export; the weekly-rate number appearing per row; changing the trend algorithm, its parameters, or the windowing; changing the chart, the y-axis rule (US-015), the glance line's own wording, or `/stats`; a Raw/Trend toggle over the lists (explicitly rejected, D6); import of the old app's record; auth. Everything on prior features' out-of-scope lists remains out.

### [REF] Walking Skeleton Strategy

**N/A — brownfield.** Both lists, the smoothed series, the save-response repaint path and the theme all ship today. This feature adds one pure day→trend lookup and one column to an existing rendering; it deploys through the existing pipeline and is dogfooded on the next morning's entry screen over the real ~77 kg plateau, plus one History visit.

### [REF] Driving Ports

Behavioral, solution-neutral; DESIGN owns shapes and adapters. Read-only ports must never expose write methods (CLAUDE.md / ADR-005).

- **TrendProjection** (driving, read-only, OUT-3) — the series contract is unchanged (Kalman+RTS over the full record, ADR-004). What the lists need is a **per-day lookup** over the full-record series, which is a pure projection of the same computation, not a new port method. DESIGN decides whether that is a core function (`trend_by_day(entries) -> mapping`) consumed by the shell, or a row-level pairing built in the composition of the two page routes.
- **WeightHistory** (driving, read-only, OUT-2) — unchanged. The lists already read `all_entries()`; both pages perform exactly one such read today and must still perform exactly one after this feature.
- **Entry-row rendering** (shell, `entry_row_text` today) — becomes a **row of cells** rather than a single string, with one definition serving `/`, `/graph` and the client repaint. Whether the trend rides the existing `{date, weight_kg}` wire pair as an additive optional `trend_kg` (which would also reach `GET /entries`, the chart's raw lens) or is enriched only on the save response's `recent` hand-back is **DESIGN's call** — the binding constraint is D7 plus the three-renderer parity above.
- **Telemetry** — untouched; rendering a list emits nothing (ADR-009 purity).

### [REF] Pre-Requisites

None blocking DESIGN. The smoothed series, both lists, the save-response repaint and the theme are delivered and mutation-tested ✅.

Two things DESIGN must decide consciously rather than discover at DELIVER:

- **(a) Wire shape.** `entry_wire_pair` is the single `{date, weight_kg}` shape shared by `GET /entries` and the save response's `recent` (D-18). Adding `trend_kg` there gives the lists one source and keeps the two surfaces in step, but it also puts a trend number on the raw-lens endpoint, where the chart does not need it. The alternative — enriching only the save's hand-back — keeps `GET /entries` pure but creates a second place a row's trend can come from. Pick one and pin it.
- **(b) Existing acceptance tests will move, by design.** The row grammar `"Fri 24 Jul — 82.2 kg"` is asserted in `tests/.../properties/test_recent_list_properties.py` (`ROW_GRAMMAR`, the golden row, and the `recent_entry_rows` identity), in `tests/.../steps/composition.py` (`RECENT_LIST_BLOCK` matches `<ul id="recent-entries">`, the History list block, and the post-save repaint assertion at ~line 2054), and in `tests/.../properties/test_entry_hint_wiring.py`, which greps the inline script for the literal source of `entryRowText`. `theme.css` styles `#recent-entries li` / `#history-entries li`. These are **intended** changes under D6/D9, not regressions — but the em-dash day wording is **shared** with `Saved.confirmation` and the entry hint line (`domain_types.py`), and those two must keep their current wording. DISTILL should treat "the confirmation and the hint are byte-identical to pre-feature" as an explicit guard.

### [REF] Outcome KPIs

**Objective**: The trend is readable as a series of numbers, not only as a shape — on the surface the user is already looking at, at the moment he is asking how much has actually changed.

Extends the existing registry (KPI-1…9 and G-1…G-5 unchanged; `kpi-contracts.yaml` is DEVOPS/DISTILL-owned and not edited here):

| # | Who | Does What | By How Much | Baseline | Measured By | Type |
|---|-----|-----------|-------------|----------|-------------|------|
| 10 | Clemens | answers "how much has my trend moved over the last week / month?" with two quoted numbers, without opening the chart or estimating from a line | 100 % of attempts answered from a list, in ≤10 s, over a 7-morning dogfood window; 0 attempts requiring the chart | today: impossible — exactly one trend value (today's, on the glance line) exists as a number anywhere in the product | self-reported at dogfood (single-user `measurement_note`); no instrumentation added | Leading |

- **Guardrails (must not degrade)**: KPI-1 entry speed and tap count (no added fetch, script or tap); G-2 interactive ≤2 s on both surfaces; G-3 trend determinism (the same series, rendered — no second algorithm and no stored copy); G-4 contrast AA both schemes and no horizontal scroll at 360 px; G-5 zero new origins; KPI-3 purity (rendering emits no telemetry).
- **Hypothesis**: We believe that showing each entry's smoothed trend value beside its raw value, in aligned columns on both lists, will let Clemens judge real movement by subtraction rather than by eye (KPI-10), and will make a plateau legible as a plateau even where the deliberately-widened y-axis (US-015) makes it visually small.
- **Measurement plan**: dogfood self-report after 7 mornings (front-page list at 06:45, plus one deliberate History visit), recorded in iteration notes; the KPI-10 row is proposed here for DEVOPS to register in `kpi-contracts.yaml` with `gate: soft`.

### [REF] DoR Validation

| DoR Item | US-016 | Evidence |
|----------|--------|----------|
| 1. Problem clear, domain language | PASS | The trend exists as a number for exactly one day; every other trend value is a pixel. "How far has it moved" is a subtraction the product cannot serve |
| 2. Persona specific | PASS | `clemens` — phone-first, 06:45, 0.1 kg scale, currently plateaued ~77 kg, judges progress from the trend |
| 3. 3+ domain examples, real data | PASS (7) | Noisy week vs steady trend; top row = glance; a month of loss; gap days; first morning; backfill revising the rows above; degraded projection |
| 4. UAT 3–7 scenarios G/W/T | PASS (7) | Noisy-week, glance-agreement, whole-record-at-any-scale, gaps-absent, backfill-repaint, degrade-to-absent, @property layout/contrast |
| 5. AC derived from UAT | PASS | Nine ACs (table + headers, same-series equality, 0.1 kg precision, unwindowed History list, gaps, in-place repaint, degrade, one row definition, guardrails) |
| 6. Right-sized (1–3 d, 3–7 sc.) | PASS | ~0.5 d; 7 scenarios; demoable in one session on the phone |
| 7. Technical notes/constraints | PASS | System Constraints + Driving Ports; wire shape (a) and the test-surface delta (b) named for DESIGN/DISTILL |
| 8. Dependencies resolved/tracked | PASS | Series, both lists, repaint path, theme all delivered ✅; the AT/CSS surfaces that move are enumerated in Pre-Requisites |
| 9. Outcome KPIs, numeric targets | PASS | KPI-10 (100 % answered from a list in ≤10 s over 7 mornings, 0 chart fallbacks) + six named guardrails, measurement method named |

**DoR Status: PASSED (1/1 story, 9/9 items).**

**Requirements completeness score: 0.96** — functional behavior fully specified (which value, from which series, at which precision, on which surfaces, under gaps, degradation and post-save repaint), NFRs quantified (≤2 s, AA, 360 px, zero fetches/scripts/taps/origins), business rules explicit (one series, derived never stored, complete record unwindowed, looking is not touching). Deduction: the rendered precision is a default (OQ-15) and the wire shape is deliberately left to DESIGN (Pre-Requisites (a)).

### [REF] DoD 9-Item Checklist

Per story, at DELIVER completion (unchanged pattern):

1. All UAT scenarios green (automated), including the @property layout scenario to the extent it is machine-assertable (markup/structure/tokens; visual alignment self-verified at dogfood).
2. Supporting unit/integration tests green; the confirmation line and the entry hint line are byte-identical to pre-feature (explicit guard, Pre-Requisites (b)).
3. Code refactored; per-feature mutation gate ≥80 % on modified files.
4. Code reviewed (self-review with reviewer agent — solo project).
5. Merged to main.
6. Deployed to the phone-reachable production URL via the existing pipeline.
7. Dogfooded next morning: read the seven trend values on `/` over the real record, then subtract two numbers a month apart on `/graph`; self-report recorded.
8. Guardrails verified: ≤2 s interactive, zero added fetches/scripts/origins/taps, AA contrast both schemes, no horizontal scroll at 360 px, `/stats` counters unmoved by renders.
9. Story demonstrable end-to-end on the phone.

### [REF] Wave Decisions Summary

Locked: D1–D5 + D6–D12 (aligned `Date | Raw | Trend` columns; both lists together, one grammar; values from the existing full-record smoothed series by day; semantic table; per-column precision — raw 0.1 kg, trend 0.01 kg, retuned at DELIVER; retrospective revision accepted; degrade to absent). Prior assumptions A1–A31 unchanged and still binding.

New assumptions (chosen during requirements, flagged for confirmation):

- **A32** A row's trend value is `trend_series(all_entries)` evaluated at that row's own day. The grid spans first→last entry day, so every entry day has a point and the lookup is **total** — no fallback branch exists or is needed.
- **A33** The lists remain **entry**-based, never calendar-based (A18 stands). Grid days without an entry have trend values and are deliberately not rendered; a gap is an absent row, never a half-filled one.
- **A34** The History page's complete-record table is **never** windowed by the selected scale (D-17 stands); the trend column therefore does not change when the chart's scale changes.
- **A35** The columns render at **different** precisions, deliberately: raw at 0.1 kg (the scale's own — a second digit there would be invented), trend at 0.01 kg (derived, and too slow to read at one). Two named constants, `RAW_DECIMALS` / `TREND_DECIMALS`, in one place.
- **A36** A given day's trend value is **one** value across every surface that shows it — the glance line, the front-page list, the History list and the chart. Each surface renders it at its own pinned precision, and every one of them is checked against the **series**, never against another rendering, so a re-rounding of an already-rounded number cannot pass by looking self-consistent. Any disagreement is a defect, and this is the feature's sharpest falsifiable claim.
- **A37** Degradation is **per render, per surface**: a failing trend projection empties the trend cells of the list being rendered and nothing else. The raw column, the chart, the entry field and the save path are all unaffected.
- **A38** Exactly one row definition is consumed by three renderers (server front page, server History page, client post-save repaint). The client repaint receives its trend values from the save response; it never computes a trend and never holds a second precision rule.
- **A39** The lists stay display-only: adding a column adds no affordance, no handler and no per-row markup beyond the cells themselves (A18/D9, and 02-02's lean-row budget on the History page).

Open questions (non-blocking; defaults apply unless overridden):

- **OQ-15** ~~Is 0.1 kg the right precision for the trend column?~~ **CLOSED at DELIVER (2026-09-09): no — it ships at 0.01 kg.** The falsifier fired on the first real render: over a month declining ~0.04 kg/day, the smoothed trend moved 0.05 kg across the front page's seven rows, so every row printed `77.5` and the column read frozen while the curve visibly sloped. Two decimals show the motion (77.53 → 77.48); the glance line keeps its ADR-006 one decimal and states the same value. Raw stays at 0.1 kg — the scale never measured a second digit. See D10/A35.
- **OQ-16** Should the front-page list stay at 7 entries now that it carries more information per row, or is a taller list more useful? Default: **7, unchanged** (A18) — the front page is the entry screen first.
- **OQ-17** Does the History page's complete record want a scroll container or a "show older" affordance once it carries three columns? Default: **no** — the page scrolls, the rows stay lean (A39), and any affordance is out of scope here.

Risk notes: **regression risk** is the main one and it is concentrated in the tests and the theme, not the domain — the row grammar is asserted in three test modules and styled by two CSS rules, all enumerated in Pre-Requisites (b); the mitigation is to treat the grammar change as an intended AC delta while explicitly guarding the *shared* day wording used by the confirmation and the hint. **Consistency risk** = three renderers of one row (A38), mitigated by one definition plus the A36 equality AC, which is directly testable. **Product risk** is small and named: the precision default (OQ-15) may make a slow trend look frozen. **Performance risk** negligible: both pages already perform the `all_entries()` read, and the History page already smooths the full record on every `/trend` call; the added cost is one dictionary build. **Testability**: the whole feature is server-rendered markup over pure functions, so it maps onto the shipped AT + PBT style with no JS-runner problem (unlike US-015's rejected client-side option). JTBD traceability intact (US-016 → `js-2-judge`, secondary `js-4-glance`; no new moment). No DIVERGE — user = customer, and D6–D8 were pinned by the user before the wave opened. Density: lean + ask-intelligent; triggers evaluated (AC ambiguity ≥2 stories, ≥3 bounded contexts, ≥3 personas, compliance terms, WS strategy D) — **none fired** → silent lean. Density telemetry skipped: `scripts/shared/telemetry.py` not present in this repository (recorded here in lieu of the event, per prior features).

## Wave: DESIGN

Architect: solution-architect (Morgan), 2026-09-09. Scope: **application / components** (no new container, actor, external system or infrastructure concern; no bounded-context change — the domain model is one job, one aggregate, unchanged since bootstrap). Mode: **Propose** — the user pinned the product shape (D6–D8) before DISCUSS opened and expects the mechanism decided here, as at y-axis-floor. SSOT updated: `docs/product/architecture/brief.md` (§ Application Architecture — trend-column delta paragraph, ADR index) + new `adr-013-entry-row-trend-delivery.md`. ADR-001…012 unchanged; **none superseded** (ADR-004's series, ADR-006's glance and ADR-010's inline-map precedent are all relied on, not altered). Paradigm not re-decided (ADR-005 / CLAUDE.md: Functional Core / Imperative Shell — the day→trend view is a pure projection and lands in the core). No C4 L1/L2 changes; no L3 (below the 5-component threshold). Outcome collision check: `nwave-ai outcomes check-delta` → **exit 0, no collisions**. Per-wave peer review deferred to the consolidated review at DISTILL (precedent: graph-first-home, entry-date-picker, y-axis-floor) — no contested ADR, no novel pattern, no unverified performance budget, no security-boundary change. Density: lean, Tier-1 [REF] only; no `ask-intelligent` triggers are declared for DESIGN, so no menu is emitted. Density telemetry skipped (`scripts/shared/telemetry.py` absent).

### [REF] DDD List

Numbering continues the global DESIGN sequence from D-31 (y-axis-floor). The DISCUSS decisions D1–D12 above are this feature's own local sequence.

- **D-32 The day→trend view is a pure core projection, `core/trend.py: trend_by_day(entries) -> dict[date, float]`** (resolves DISCUSS open item (b), core half) — **accepted**. Two lines over the shipped `trend_series`: `{point.day: point.trend_kg for point in trend_series(entries)}`. Total (an empty record yields an empty mapping), clock-free, order-invariant, and by construction defined at **every** entry day, because the grid it is built from spans first→last entry day (A32). It lands **in `core/trend.py`, not a new module** — unlike `y_axis_range`, which earned `core/axis.py` because an axis rule is a different concern, a day-keyed view of the trend series *is* the trend series. Rejected: recomputing per row (O(n) smoothings for n rows, and n chances to disagree); a `Mapping` returned by a new port method (read-only ports gain no methods, ADR-005 / CLAUDE.md).
- **D-33 The projection is injected at the composition root as a third read-only callable, `TrendByDayProjection`** — **accepted**. `Callable[[Sequence[Entry]], Mapping[date, float]]`, wired beside `trend_series_in` and `glance_summary_of` (ADR-006's "second injected pure callable" precedent). Injection is not ceremony here: it is what makes D-34's containment testable by fault injection, exactly as the glance's is. `ports.py` is **untouched** — this is a driving-side pure callable, not a port protocol.
- **D-34 Degradation is contained in one shell function that returns an empty mapping** (resolves DISCUSS open item, degrade boundary) — **accepted**. `trend_by_day_or_degrade(entries)` in the router closure, the exact sibling of `glance_or_degrade` (D-13), logging `trend.rows.degraded` on the structured trail and returning `{}`. The row builder then needs **no degrade branch at all**: it looks a day up with `.get(day)` and renders an empty cell on a miss, so "a failing trend empties the trend cells and nothing else" (A37) is structural rather than conventional. One mechanism covers both the injected-failure case and the impossible-by-A32 missing-day case.
- **D-35 One row definition: `EntryRow`, a frozen three-cell shape built by one shell function** (resolves DISCUSS open item (b), rendering half) — **accepted**. `routes.py` gains `EntryRow(day_text, raw_text, trend_text)` and `entry_row(day, weight_kg, trend_kg | None) -> EntryRow`; `recent_entry_rows` and `complete_record_rows` keep their names and signatures-plus-one-argument, both mapping over `entry_row`. The single string `entry_row_text` is **retired with its grammar** (D6 changes what a row is; keeping a second string-row function beside the cell-row function is precisely the fork D7 forbids). Templates iterate rows and place `row.day_text / row.raw_text / row.trend_text` into `<td>`s; no formatting survives in Jinja.
- **D-36 The day wording gets one definition: `core/types.py: day_label(day) -> str`** — **accepted**. `"Fri 24 Jul"` is currently written three times (the row grammar in `routes.py`, `Saved.confirmation` in `core/types.py`, `dayLabel` in the inline script). Since the row grammar is being rewritten anyway, the format moves to a pure core helper that `Saved.confirmation` and `entry_row` both call. `confirmation`'s **output is byte-identical** — a DoD guard, not a hope. The client keeps its own `dayLabel` (no shared runtime exists across the language boundary); the existing wiring test that pins its source stands.
- **D-37 Wire: the save response's `recent` pairs gain an additive, always-present, nullable `trend_kg`; `GET /entries` is untouched** (resolves DISCUSS open item (a)) — **accepted**. `entry_wire_pair` stays the pure `{date, weight_kg}` base shape and remains the single definition of it; `recent_entries_payload` — the one call site that feeds the list repaint — extends each pair with `trend_kg: float | null`. Decisive evidence: (1) `GET /entries` is the **raw lens's** data source and `GET /trend` is the trend lens's; putting smoothed values on the raw endpoint gives the chart two paths to one series and invites exactly the drift A36 forbids; (2) `GET /entries` today is a pure windowed filter — adding `trend_kg` there would run a full Kalman+RTS pass on every raw-lens fetch for a consumer that discards it, against entry primacy and G-2; (3) what D-18 actually protects is that the server-rendered recent list and the save's hand-back tell the same story, and they still do — both derive from `recent_head` **and the same `trend_by_day` mapping**, then render through the same grammar. Rejected: `trend_kg` on `entry_wire_pair` itself (costs above, no consumer); handing back pre-formatted row strings instead of numbers (the client's `mergedRecord` reads `weight_kg` out of `recent` to keep the prefill map fresh — ADR-010 — so the numbers must stay).
- **D-38 Markup: a semantic `<table>` keeping the two mount ids and the existing `aria-label`** (resolves DISCUSS open item, markup contract) — **accepted**. `<table id="recent-entries" aria-label="Recent entries">` / `<table id="history-entries" aria-label="Complete record">`, one `<thead>` row of `<th scope="col">Date / Raw (kg) / Trend (kg)</th>`, one `<tr>` of three `<td>` per entry. The ids are kept so the theme and every existing test hook stay pointed at the same element. `aria-label` rather than `<caption>`: a visible caption duplicates the heading already above the History list, and hiding one would need a new utility class, which ADR-007 forbids ("state via attributes, never new classes"). `kg` appears once per column header, never per cell (`unit_label_kg` keeps a single source).
- **D-39 Presentation stays in `theme.css` on the existing ids** — **accepted**. The two `li` rules become `th`/`td` rules on the same selectors: full-width `border-collapse: collapse`, hairline `border-top` per row, muted ink, numeric columns `text-align: right` with `font-variant-numeric: tabular-nums` so decimal points align down a column (the @property AC). Existing tokens only; no new class, no new asset, no new origin.
- **D-40 Service worker: `SHELL_CACHE` bumps `-v5 → -v6`** — **accepted**. `/` is itself pre-cached and its response changes; the APP_SHELL **list** is unchanged (no new asset). Same trigger and same reasoning as entry-date-picker's `-v4` and y-axis-floor's `-v5`: a changed pre-cached response, not a new file.
- **D-41 Nothing else moves** — **accepted**. No port protocol change (`ports.py` untouched; `WeightHistory` / `TrendProjection` gain no methods), no new route, adapter, container, dependency, external origin, event name, Earned-Trust probe or schema migration. The trend column emits **no telemetry**: rendering a list is not intent (ADR-009). Both pages still perform **exactly one** `all_entries()` read.

### [REF] Component Decomposition

| Component | Path | Change |
|---|---|---|
| Trend core | `src/weight_tracker/core/trend.py` | **EXTEND** — add pure `trend_by_day(entries)` beside `trend_series` / `trend_series_in` |
| Domain types | `src/weight_tracker/core/types.py` | **EXTEND** — add pure `day_label(day)`; `Saved.confirmation` calls it (output byte-identical) |
| Routes (shell) | `src/weight_tracker/web/routes.py` | **EXTEND** — `EntryRow` + `entry_row`; `recent_entry_rows` / `complete_record_rows` take the mapping; `trend_by_day_or_degrade` closure; `recent_entries_payload` adds `trend_kg`; `entry_row_text` retired |
| Composition root | `src/weight_tracker/composition.py` | **EXTEND** — wire `trend_by_day` as the third read-only projection; route-contract docstring updated |
| Entry screen | `src/weight_tracker/web/templates/index.html` | **EXTEND** — recent list becomes a table; `entryRowText` → cell builder; `refreshRecentList` builds rows of cells |
| History page | `src/weight_tracker/web/templates/graph.html` | **EXTEND** — complete record becomes a table |
| Theme | `src/weight_tracker/web/static/theme.css` | **EXTEND** — the two list rules become table rules on the same ids |
| Service worker | `src/weight_tracker/web/static/sw.js` | **EXTEND** — `SHELL_CACHE` `-v5` → `-v6` |
| Ports | `src/weight_tracker/ports.py` | **UNTOUCHED** |
| Entry store / schema | `src/weight_tracker/shell/entry_store.py` | **UNTOUCHED** — derived, never stored |
| Chart engine | `src/weight_tracker/web/static/graph.js` | **UNTOUCHED** — the lists are plain markup; the chart is not involved |

### [REF] Driving Ports

- **`WeightHistory`** (read-only, OUT-2) — **no method added**. Both pages already call `all_entries()` once; the rows are a pure projection of that read.
- **`TrendProjection`** (read-only, OUT-3) — **no method added**. `trend_series_in` is unchanged and still serves `GET /trend`. The row column is served by the third injected pure callable (D-33), which reads the same `trend_series` (G-3: one series, one algorithm).
- **`WeightLogging`** (OUT-1) — bounded-change universe unchanged: one `{date}` row + one `entry.saved` event. `trend_kg` on the response's `recent` is route-level enrichment on the `confirmation` / `glance` / `recent` / `y_range` precedent.
- **HTTP surfaces** — `GET /` and `GET /graph` change their rendered markup; `POST /entries` gains one additive nullable key inside each `recent` pair; `GET /entries`, `GET /trend`, `/stats`, `/healthz` and the beacon are **byte-identical**.

### [REF] Driven Ports and Adapters

None added or changed. `EntryStore` (SQLite) and `Clock` are untouched; no new driven adapter ⇒ **no new Earned-Trust probes**. No migration: `CODE_SCHEMA_VERSION` stays 1 and the `entries` table gains nothing (D8 — derived, never stored).

### [REF] Technology Choices

No change. Python 3.12 / FastAPI / Jinja2 / vanilla JS, exactly as pinned in the brief. No new dependency, no new asset, no new external origin (G-5). The table is plain HTML; `font-variant-numeric` is CSS the theme already has the tokens for.

### [REF] Decisions Table

| ID | Decision |
|---|---|
| D-32 | Pure `trend_by_day` in `core/trend.py` (not a new module, not a port method) |
| D-33 | Injected at the composition root as a third read-only pure callable |
| D-34 | `trend_by_day_or_degrade` returns `{}`; the row builder has no degrade branch |
| D-35 | One `EntryRow` three-cell shape; `entry_row_text` retired with its grammar |
| D-36 | `day_label` in `core/types.py`; `Saved.confirmation` output byte-identical |
| D-37 | `trend_kg` additive and nullable on the save's `recent` pairs only; `GET /entries` untouched |
| D-38 | Semantic `<table>`, same ids, `aria-label`, `kg` once per column header |
| D-39 | Table rules in `theme.css` on the existing ids; tabular right-aligned numerals |
| D-40 | `SHELL_CACHE` `-v5` → `-v6` (changed pre-cached response, list unchanged) |
| D-41 | No port, route, adapter, dependency, event, probe or migration change |

### [REF] Reuse Analysis

| Existing Component | File | Overlap | Decision | Justification |
|---|---|---|---|---|
| `trend_series` | `core/trend.py` | produces exactly the values a row needs | **EXTEND** | A two-line day-keyed projection over the shipped series; a second computation would break G-3 and A36 by construction |
| `entry_row_text` | `web/routes.py` | *is* the row grammar being replaced | **EXTEND (in place)** | D6 redefines a row; a second row function beside it is the fork D7 forbids. Same call sites, same names, richer return type |
| `recent_entry_rows` / `complete_record_rows` | `web/routes.py` | the two list projections | **EXTEND** | Both already delegate to one row builder; keep the shape, pass the mapping |
| `recent_head` | `web/routes.py` | the one seven-entry slice | **REUSE unchanged** | Still the single source shared by the render and the hand-back |
| `entry_wire_pair` | `web/routes.py` | the base wire shape | **EXTEND at one call site** | `recent_entries_payload` adds `trend_kg`; the base pair stays single-source and `GET /entries` stays a pure filter (D-37) |
| `glance_or_degrade` | `web/routes.py` | shell containment of a failing pure projection | **EXTEND the pattern** | Identical need; a new containment mechanism would be a second answer to a solved question |
| `GlanceProjection` wiring | `composition.py` | read-only pure callable injected at the root | **EXTEND** | ADR-006's precedent, third callable, same `partial`-free shape |
| `Saved.confirmation` day format | `core/types.py` | duplicate `"Fri 24 Jul"` wording | **EXTEND** | Extracting `day_label` removes a fork while keeping the output byte-identical |
| `#recent-entries` / `#history-entries` rules | `static/theme.css` | list row styling | **EXTEND** | Same ids, same tokens, `li` rules become `th`/`td` rules |
| `dayLabel` / `entryRowText` | `templates/index.html` | client row grammar | **EXTEND** | One grammar across three renderers; `dayLabel` is reused untouched |
| `y_axis_range` / `core/axis.py` | `core/axis.py` | a pure projection over series values | **CREATE NOTHING** | Different concern (axis bounds); no overlap with a day-keyed lookup |

**Zero CREATE NEW decisions.** Every component in the change set extends something shipped.

### [REF] Open Questions

- **OQ-15** (from DISCUSS) rendered trend precision — **closed at DELIVER**: the 0.1 kg default was falsified on the first real render and the column ships at 0.01 kg (`TREND_DECIMALS`, one place). See D10/A35 and the DELIVER section.
- **OQ-18** (DISTILL) how much of the @property layout scenario is machine-assertable. The structure is (table, header cells, `scope="col"`, one row per entry, `kg` once per weight column, the theme rules present); *visual* alignment and no-wrap at 360 px are not, in a browser-less suite — the y-axis-floor precedent applies: assert the structure and the tokens, verify the pixels at dogfood. DISTILL pins the split.
- **OQ-19** (DELIVER) whether `recent_entry_rows` and `complete_record_rows` collapse into one function once both take `(entries, trend_by_day)` and differ only by the slice. Left to the L1–L6 refactor pass with the tests green; the two names are load-bearing in the ATs today.

### [REF] Changed Assumptions

DISCUSS Pre-Requisites (a) offered two wire shapes and asked DESIGN to pin one. Original text (`docs/feature/numeric-trend-history/feature-delta.md`, § Pre-Requisites):

> Adding `trend_kg` there gives the lists one source and keeps the two surfaces in step, but it also puts a trend number on the raw-lens endpoint, where the chart does not need it. The alternative — enriching only the save's hand-back — keeps `GET /entries` pure but creates a second place a row's trend can come from.

**New assumption (A40)**: the second horn does not bite. There is no second place a row's trend comes from, because both the server render and the save's hand-back read the **same `trend_by_day` mapping** for the same request and hand it to the **same row builder** (D-35); the wire carries a number the client formats through the same grammar, and never a second lookup. `GET /entries` therefore stays a pure windowed filter (D-37), and the single-source guarantee D-18 protects is preserved by the mapping rather than by the wire shape.

## Wave: DISTILL

Acceptance designer, 2026-09-09. Reconciliation gate: all prior wave decisions read (DISCUSS D1–D12 / A32–A39 / OQ-15–17 and the seven UAT scenarios; DESIGN D-32–D-41 + ADR-013 + § Reuse Analysis + § Changed Assumptions; no DEVOPS wave — brownfield on the shipped pipeline, WARN logged, default matrix) — **0 contradictions**. DESIGN's refutation of Pre-Requisite (a)'s second horn (A40: both renderers read one mapping in one request, so the wire shape is free to keep `GET /entries` pure) keeps every observable DISCUSS promise. Deliverable type: `application` ⇒ no plugin/skill reviewer routing. Infrastructure policy: `--policy=inherit` — this feature adds **no port and no adapter**, so zero rows are missing; the Architecture of Reference is unchanged (driving = `TestClient` over `build_app`, driven-internal = real SQLite on `tmp_path`, driven-external = `FakeClock` only). Density: lean, Tier-1 `[REF]` only; density telemetry skipped (`scripts/shared/telemetry.py` absent).

### [REF] Scenario List

Scenario SSOT: `tests/weight-trend-tracker/acceptance/milestone-12-trend-in-the-record.feature` (Slice 01 — US-016). **12 scenarios / 12 executions**. Error/edge share **5/12 ≈ 42 %**.

| Scenario | Tags |
|---|---|
| A noisy week reads as a steady trend, in numbers | `@driving_port @US-016 @contract-shape:pure-function` |
| The newest row and the glance line agree | `@driving_port @US-016 @contract-shape:pure-function` |
| The whole record carries the column at every scale | `@driving_port @property @US-016 @contract-shape:pure-function` |
| Missing days are absent, not empty rows | `@driving_port @error @US-016 @contract-shape:pure-function` |
| A backfilled day revises the rows above it, in place | `@driving_port @US-016 @contract-shape:bounded-change` |
| A failing trend leaves the raw record standing | `@driving_port @error @US-016 @contract-shape:pure-function` |
| A first morning stands on its own trend | `@driving_port @error @US-016 @contract-shape:pure-function` |
| An empty record shows no table at all | `@driving_port @error @US-016 @contract-shape:pure-function` |
| Both lists speak one grammar | `@driving_port @property @US-016 @contract-shape:pure-function` |
| The columns are announced, not merely aligned | `@driving_port @US-016 @contract-shape:pure-function` |
| Looking is still not touching | `@driving_port @US-016 @contract-shape:pure-function` |
| The second column costs nothing at the door | `@driving_port @kpi @US-016 @contract-shape:unbounded-preservation` |

**The oracle is the chart's own endpoint.** Every expected trend value is re-derived from `GET /trend` at `ALL` and compared cell by cell. That is what makes A36 a claim rather than a tautology: a second algorithm, a second rounding path, or a windowed re-smoothing on either surface fails at this assertion instead of in a comment. The two `@property` scenarios are layer-3 (real HTTP + real SQLite) ⇒ **example-pinned**, per Mandate 9/11; the lens × scale Cartesian (2 × 6) is a closed, listable world and is **enumerated** by the unwindowed-record tour rather than generated.

Two pure-core PBT modules pair the ATs (ADR-025 split — DISTILL owns ATs, DELIVER owns the paired PBT): `properties/test_trend_by_day_properties.py` (7 properties over the new core projection) and the rewritten `properties/test_recent_list_properties.py` (12 properties over the row definition and the slice, including the positional-zip falsifier and the frozen-row guard added to close a mutant).

AT-completeness audit (`nw-at-completeness-check`, 15 items): **15/15 — COMPLETE**. Asserted: C1a (empty record, both surfaces; single entry), C1b (the seven-entry slice boundary; a first morning; a gap-bounded record), C2a (documented in `steps_trend_rows.py`: EMPTY → TABLE → RAW-ONLY under degrade, plus backfill and lens/scale events), C3 (0/1/many), C4a (identical reloads of a pure read; the unwindowed tour re-reads twelve times), C5a+C5b (the lens × scale tour; the record invariant, selection preserved), C6b (empty trend cells, never a zero or a stand-in), C6c (the closed row shape — three cells, no half rows). Not applicable with rationale: C2b/C4b (no inverse op — read-only projection), C6a (the column takes no user input), C7a/b/c (pure arithmetic inside an already-served atomic read; store failure is pinned by the shipped "series read admits trouble"). Zero `SPECIFICATION_AMBIGUITY` findings; audit log: `(numeric-trend-history, C1–C7, 0 findings, none)`.

### [REF] Inherited-Test Renegotiation

The single-string row grammar retires with D6/D-35, which moves five shipped assertions. Each is an **intended AC delta**, renegotiated in the open rather than silently rewritten, and each fails loudly if the intent is broken:

| Shipped assertion | Was | Now | Why it is a delta, not a break |
|---|---|---|---|
| `composition.py` `RECENT_LIST_BLOCK` / `HISTORY_LIST_BLOCK` / `LIST_ROW` | `<ul>` of `"Fri 24 Jul — 82.2 kg"` `<li>`s | `<table>` on the same two ids; rows parsed as three cells into a `Row` NamedTuple | D6 changed what a row *is*. The ids are deliberately unchanged so every other hook still points at the same element |
| `properties/test_recent_list_properties.py` `ROW_GRAMMAR` + golden row | one regex, one decimal | `DAY_CELL` / `RAW_CELL` / `TREND_CELL`, two precisions | the grammar is the thing under change; the module was rewritten around the new one, not deleted |
| `properties/test_entry_hint_wiring.py` day-grammar grep | source of `entryRowText` | source of `entryRowCells`, whose first cell is `dayLabel(` | the intent ("the hint and the rows cannot fork into two calendar wordings") is preserved verbatim; only the function it reads changed |
| `properties/test_save_recent_properties.py` hand-back equality | pair `==` `{date, weight_kg}` | pair minus `trend_kg` `==` `{date, weight_kg}`, **plus** a new assertion that `GET /entries` carries no `trend_kg` | the additive key is D-37; the new assertion is what makes "the raw read stays untouched" falsifiable rather than asserted in prose |
| `test_axis_engine_wiring.py` + `test_date_row_dress.py` `SHELL_CACHE` pins | `-v5` | `-v6` | the pins' stated intent is "the cache MOVES when a pre-cached response changes"; `/` changed, so it moved (D-40) |

**Guarded against**: `Saved.confirmation` and the entry hint line are **byte-identical** to pre-feature, despite both now calling the extracted `core/types.py: day_label`. That is the explicit DoD guard DISCUSS Pre-Requisite (b) asked for.

**Deliberately not asserted (client-structural, dogfood-verified — the client-paint precedent D-15):** the in-browser repaint building `<tr>`/`<td>` from the hand-back, the rebuilt header on a first morning's save, `font-variant-numeric: tabular-nums` producing visually aligned decimal points, no-wrap at a 360 px viewport, and the `sw.js -v6` bump taking effect. A browser-less suite cannot falsify what a script paints or what a font does; the markup, the headings, the theme rules and the cache name are pinned textually, and the pixels are owed to dogfood.

## Wave: DELIVER

Functional software crafter, 2026-09-09. Slice 01 shipped in two commits (`95794e0` waves 1–3, `a38e8fa` implementation). Suite: **278 passed** (255 before, +23). Static gates all green: `ruff check`, `ruff format --check`, `mypy --strict` on `src/`, `lint-imports` (functional-core contract kept), the AST probe-presence gate. Mutation: **effective 20/20 = 100 %**, raw 20/31 — report at `deliver/mutation/mutation-report.md`.

### [REF] What Shipped

- **`core/trend.py: trend_by_day(entries) -> dict[date, float]`** — the shipped series keyed by day, total over the record by construction (D-32/A32).
- **`core/types.py: day_label(day)`** — the `"Fri 24 Jul"` wording, now with one definition; `Saved.confirmation` calls it and its output is byte-identical (D-36).
- **`web/routes.py`** — frozen `EntryRow` + `entry_row` at two named precisions; `entry_rows` / `recent_entry_rows` / `complete_record_rows` over the mapping; `trend_by_day_or_degrade` (returns `{}`, logs `trend.rows.degraded`); `ENTRY_COLUMN_HEADINGS`; `recent_entries_payload` carrying the additive `trend_kg`; `entry_row_text` retired (D-34/D-35/D-37).
- **`composition.py`** — `trend_by_day` wired as the third read-only projection (D-33).
- **`index.html` / `graph.html`** — both lists rendered as semantic tables on their existing ids; the client repaint builds rows of cells and rebuilds the header when the table did not exist (D-38).
- **`theme.css`** — the two `li` rules became `th`/`td` rules on the same selectors, numeric columns right-aligned on tabular figures (D-39). **`sw.js`** — `SHELL_CACHE` `-v5` → `-v6` (D-40).
- **Untouched, as designed**: `ports.py`, `entry_store.py` and the schema, `graph.js`, `GET /entries`, `GET /trend`, `/stats`, `/healthz`, the beacon, every event name, every driven adapter and probe.

### [REF] Changed Assumptions

**A35 (rendered precision) was retuned by the first real render.** DISCUSS D10 pinned both columns at 0.1 kg, and named its own falsifier in OQ-15: *"if a week of rows reads as an identical number seven times while the curve visibly slopes, the default is wrong."* Original text (§ Locked Decisions, D10):

> **Trend renders at 0.1 kg, like every other weight on the screen.** One decimal, matching the glance line (`Trend: 77.2 kg`), the raw column, the confirmation and the hint.

It fired immediately. Over a month declining ~0.04 kg/day, the smoothed trend moves ~0.05 kg across the front page's seven rows, so every row printed `77.5` and the column read frozen:

| Date | Raw (kg) | Trend at 0.1 | Trend at 0.01 |
|---|---|---|---|
| Wed 9 Sep | 77.3 | 77.5 | 77.48 |
| Tue 8 Sep | 77.3 | 77.5 | 77.48 |
| Mon 7 Sep | 77.0 | 77.5 | 77.49 |
| Sun 6 Sep | 77.6 | 77.5 | 77.50 |
| Sat 5 Sep | 77.2 | 77.5 | 77.50 |
| Fri 4 Sep | 77.1 | 77.5 | 77.52 |
| Thu 3 Sep | 77.1 | 77.5 | 77.53 |

**New assumption (A35, revised)**: the columns render at **different** precisions on purpose — raw at 0.1 kg, trend at 0.01 kg. The asymmetry is the honest one, not the inconsistent one: the scale measured the raw weight to a tenth and never measured a hundredth, so a second raw digit would be invented; the trend is *derived* and has real resolution below 0.1. The glance line keeps its ADR-006 single decimal and states the same value, which is why A36 was sharpened at the same time: every rendering is checked against the **series**, never against another rendering, so a re-rounding of an already-rounded number cannot pass by looking self-consistent. Two named constants, `RAW_DECIMALS` / `TREND_DECIMALS`, in one place. **OQ-15 closed.**

### [REF] Open Questions Carried Forward

- **OQ-16** front-page list depth — ships at 7 (A18 unchanged); the column added information per row without adding rows.
- **OQ-17** a scroll container or "show older" on the History table — still **no**; the page scrolls and the rows stayed lean (A39).
- **OQ-19** (DESIGN) collapsing `recent_entry_rows` and `complete_record_rows` — **not taken**. With both now delegating to `entry_rows`, the two names carry only a slice and are two lines each; they remain the vocabulary the acceptance tests and the templates speak. Merging them would trade a named surface for two saved lines.
- **Owed to dogfood** (D-15 client-paint precedent): the in-browser repaint's `<tr>`/`<td>`, the rebuilt header after a first morning's save, decimal alignment under `tabular-nums`, no wrap at 360 px, and the `-v6` cache bump taking effect on the phone.
