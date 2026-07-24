<!-- markdownlint-disable MD024 -->
# Feature Delta: graph-first-home

## Wave: DISCUSS

### [REF] Persona ID

`clemens` — see `docs/product/personas/clemens.yaml`. Sole customer, sole user, sole developer. Phone-first, half-awake at 06:45, metric units, ~82 kg range. Unchanged from prior features.

### [REF] JTBD One-Liner

Job `track-true-weight-trend` (`docs/product/jobs.yaml`, status: validated). This feature deepens the **ambient orientation moment** (`js-4-glance`: *"see my current trend … at a glance, without navigating anywhere"*) and sharpens the **deliberate judging moment** (`js-2-judge`) by giving each its own surface: the front page becomes the ambient picture (curve + entry + recent record), and "History" becomes the deliberate full-record study.

**Bridge decision**: **no new job-story moment appended.** `js-4-glance` already names the ambient moment — this feature upgrades what that moment delivers from a number+rate line to the full curve, without changing its *when* (just stepped off the scale, eye on the entry screen) or its *so-i-can* (know where I stand before pocketing the phone). `js-2-judge` already names the deliberate moment served by the combined History page. Same job, same moments, richer delivery — a dated note on `js-4-glance` and the feature-list entry in `jobs.yaml` record the extension (per D4; follows the js-4/js-5 precedent for dated comments; no JTBD re-run).

### [REF] Locked Decisions

- **D1** Feature type: user-facing.
- **D2** Walking skeleton: NO — brownfield; the full vertical exists; this feature rides it.
- **D3** UX research depth: lightweight — journey delta, happy path, single persona.
- **D4** JTBD: bridge only to existing validated job `track-true-weight-trend`; no full re-analysis.
- **D5** Density: mode=lean (Tier-1 [REF] only), expansion_prompt=ask-intelligent (triggers evaluated and reported — **none fired**, silent-lean).
- **D6** (user) **Entry primacy kept with the graph above the form**: weight field autofocus + decimal keypad + interactive ≤2 s stay exactly as today. The keypad may cover the graph on open — **accepted, not a failure** (user chose "Keep autofocus" knowing this).
- **D7** (user) **Front-page graph has FULL controls**: lens toggle (Trend/Raw) + scale picker (1W/1M/3M/6M/1Y/All), same as today's `/graph`.
- **D8** (user) **"History" leads to a combined full-history page**: full-control graph on top + the COMPLETE entries list below.
- **D9** (user) **Front-page recent-entries list**: last 7 entries, display-only (date + kg). Editing stays wherever it lives today.

### [REF] Scope Assessment

**PASS — 3 stories, 1 bounded context (weight tracking), estimated ~2 days.** Oversized signals checked: stories 3/10 threshold; bounded contexts 1/3; walking-skeleton integration points N/A (skeleton exists; slices touch existing read surfaces + 2 templates); effort ~2 days ≪ 2 weeks; user outcomes — the front-page restructure and the combined History page are two separable outcomes, **resolved by slicing** (Slice 01 / Slice 02, each independently shippable and dogfoodable). One of five signals arguably brushed, addressed by the split; no further split needed. Reference class: prior slices (US-001…009) each landed in ~0.5–1 day.

### [REF] Journey Summary

SSOT: `docs/product/journeys/daily-weight-tracking.yaml` — **delta only**; step 4 untouched. Changelog entry dated 2026-07-24.

- **Step 1 (Log today's weight)** restructured top-to-bottom: trend graph with full lens + scale controls **above** the entry form; glance line kept (A14); form with autofocus + keypad unchanged; **last-7 entries list** below the form (display-only, A18); History link now promises the full record. After a successful save, graph, glance line, and recent list all refresh in place (A15). New failure modes: ambient graph render counted as deliberate trend study (KPI-3 inflation — must never happen); graph/list fetch blocking or delaying entry readiness (must degrade to absent, ≤2 s holds). Keypad covering the graph on open is **accepted by decision D6**, recorded as such — not a failure mode.
- **Steps 2–3 (Review / Judge)** now *start on the front page*: routine review and the noise-vs-signal verdict are ambient every morning; "History" is the deliberate visit to the combined page (full graph + complete entries list, D8). New step-2 failure mode: complete list and plotted points disagreeing (both must render exactly the stored entries).
- Emotional delta (step 1 exit): "done and oriented" deepens to *done and oriented with the whole picture* — the curve's shape, not just its endpoint, lands at the sink. The Problem Relief beat (raw spike visibly absorbed) now plays out visually without any tap.

### [REF] Story Map

Extends the existing map (same persona, same goal). No new activities; the front page absorbs the ambient halves of Review and Judge.

| Capture weight | Review history | Judge trend | Maintain record |
|---|---|---|---|
| US-001, US-006, US-007, US-008 ✅ | US-001, US-002, US-009 ✅ | US-004, US-005, US-009 ✅ | US-003 ✅ |
| **Graph-first front page (US-010)** | **Recent-7 list below the form (US-011)** | *(US-010 makes the curve ambient at capture)* | *(list is display-only; editing unchanged, D9)* |
| | **Complete record on the History page (US-012)** | *(US-012 hosts deliberate study)* | |

**Walking skeleton**: N/A — exists (delivered 2026-07-23). **Slices** (elephant carpaccio, each ≤1 day, each dogfooded same day):

- **Slice 01** — `slices/slice-01-graph-first-front-page.md`: US-010 + US-011 (front-page restructure incl. KPI-3 purity).
- **Slice 02** — `slices/slice-02-whole-record-history.md`: US-012 (combined full-history page).

### [REF] Priority Rationale

Slice 01 first: highest-frequency surface (365 mornings/year), carries the **riskiest assumption** (a graph above the form must not tax the five-second entry — D6 is falsifiable through dogfood), and **must** carry the KPI-3 purity mechanism (an ambient front-page trend render that reused today's deliberate counter would inflate KPI-3 ~7× from day one). It also ships the entries-list presentation idiom that Slice 02's complete list reuses (abstraction ships first). Slice 01: Value 5 (relocates the product's core payoff — the visible noise-vs-signal curve — to the screen used every morning; feeds KPI-2), Urgency 3 (daily dogfood live; KPI-3 integrity at stake), Effort 2 → score 7.5. Slice 02: Value 3 (completes the History promise; full-record audit), Urgency 2, Effort 1 → score 6. MoSCoW: all Must (explicit user request, decisions D6–D9 locked).

### [REF] System Constraints

- Prior constraints and assumptions **A1–A13 all hold** (range 30.0–250.0 kg, 0.1 kg precision, device-local day incl. read framing, one entry/day, edit-not-delete, single user, passphrase gate, metric only, glance precision/threshold rules).
- **Entry primacy (KPI-1 guardrail, D6)**: entry screen interactive ≤2 s; weight field autofocus + decimal keypad unchanged; the save flow unchanged. Graph and recent-list data must **never block or delay input readiness** — they load without taxing the ≤2 s budget and degrade to absent on failure (the glance's degrade-to-absent pattern extends to both). The keypad covering the graph on open is accepted (D6). Delivery mechanism (server-render vs async fetch) = DESIGN, constrained by these behaviors.
- **Single data source**: front-page graph, History-page graph, glance line, recent-7 list, complete list, and yesterday anchor all render from the same entry store; both graphs render the **same smoothed series** from `TrendProjection` (derived-never-stored; no second algorithm). Shared-artifact rule extension below.
- **Scale/lens semantics per surface (A17)**: each surface (front page, History page) opens at the defaults (Trend lens, 3M — A4 extended) and holds its own selection; within a surface, toggling Trend↔Raw preserves the chosen scale (US-005 rule, now on both surfaces); selections do **not** persist across surfaces or visits.
- **KPI-3 purity (behavioral)**: ambient front-page renders — initial page open at defaults and post-save refresh — must **never** count as deliberate trend study. Deliberate = History-page opens + explicit lens/scale interactions (A19). A morning that only opens `/`, logs, and leaves adds **0** to KPI-3. Event naming/mechanism = DESIGN (structural separation precedent: D-13/D-14).
- **Recent list honesty (A18, D9)**: last 7 **entries** (not days), reverse-chronological, date + kg at 0.1 precision, display-only — no edit/delete affordances; missing days are simply absent (no zeros, no placeholders); fewer than 7 entries → shorter list; 0 entries → no list.
- **Calm-theme constraints carry over** to all new elements: both schemes first-class at WCAG contrast (text ≥4.5:1, non-text ≥3:1), neutral direction presentation (no red/green judgment), touch targets ≥44 px, zero external origins, system fonts only.
- **Constraint supersession flagged**: calm-visual-theme's G-5 pin "0 new entry-screen scripts" cannot survive a front-page graph. The pin's *intent* (no third-party/network cost, no entry tax) stays binding as: zero new external origins (uPlot is already vendored) + entry primacy ≤2 s. The G-5 AT clause must be **consciously renegotiated at DISTILL**, never silently deleted.
- **Read-only surface**: extends read ports only; `WeightHistory`/`TrendProjection` must never expose write methods (CLAUDE.md / ADR-005).

### [REF] User Stories

All stories: `job_id: track-true-weight-trend` (US-010/US-011 at moment `js-4-glance`; US-012 at moment `js-2-judge`). Persona: Clemens.

#### US-010: The morning opens on the whole picture

`job_id: track-true-weight-trend` · Slice 01 · Must · ~0.5–1 day

##### Problem

Clemens's glance line answers "where am I" with a number — but the *shape* of his progress (is the decline steady? did the vacation bump flatten out?) still lives behind a History tap he skips most mornings. He wants the curve itself to greet him at 06:45, above the entry field, without costing the five-second log a single tap or second.

##### Elevator Pitch

- **Before**: Opens `/` → glance line `Trend: 82.3 kg · ↓0.25 kg/week` + entry form. The curve requires tapping History → `/graph` (a context switch he skips most mornings).
- **After**: Opens `/` on Fri 24 Jul 2026 → **above the focused weight field** a graph renders: the Trend lens at 3M with the `Trend | Raw` toggle and `1W 1M 3M 6M 1Y All` scale picker — the same controls as today's `/graph`. He types `82.2`, taps **Save** → "Saved: 82.2 kg — Fri 24 Jul" appears and the curve + glance line refresh in place with today's point absorbed.
- **Decision enabled**: "Is the movement real and *sustained* — stay the course or adjust?" — answered from the curve's shape at the sink, not from a single number or a deliberate graph visit.

##### Domain Examples

1. *Happy path*: Fri 24 Jul 2026, 06:45 — 128 entries since Tue 3 Mar, trend 82.3 kg declining 0.25 kg/week. `/` opens: 3M trend curve above the form, weight field focused, keypad up (covering part of the curve — accepted, D6). He types 82.2, saves; the curve repaints including today.
2. *Deliberate detour*: same morning he wonders about the vacation bump — taps `1Y`, then `Raw`, right on the front page. The graph behaves exactly like `/graph` (lens toggle preserves the 1Y window). Those taps count as deliberate trend study (A19).
3. *Degrade*: the trend/graph data cannot be fetched — the graph area is simply absent; field focused, `82.2` saves and confirms normally (glance degrade pattern, A12/A15).
4. *Empty record*: fresh install, 0 entries — no graph area, no list; the form is the whole screen, exactly as before.
5. *KPI purity*: in a week Clemens opens `/` 7 mornings and taps History twice; he never touches the front-page graph controls. Deliberate trend-study count for the week: 2, not 9.

##### UAT Scenarios (BDD)

###### Scenario: The morning opens on the whole picture

- **Given** Clemens has 128 entries and his smoothed trend is 82.3 kg, declining 0.25 kg/week, on Friday 24 July 2026
- **When** he opens the tracker at 06:45
- **Then** the entry screen shows the trend curve at the 3M scale above the entry form, with the Trend/Raw toggle and the 1W/1M/3M/6M/1Y/All scale picker
- **And** the weight field is focused with the decimal keypad shown, exactly as before

###### Scenario: An ambient morning never counts as deliberate study

- **Given** the deliberate trend-study count for this week is 2
- **When** Clemens opens `/`, logs 82.2 kg, and pockets the phone without touching the graph controls
- **Then** the deliberate trend-study count for the week still reads 2

###### Scenario: Choosing a lens or scale is deliberate study

- **Given** the front-page graph shows the Trend lens at 3M
- **When** Clemens taps "1Y" and then "Raw"
- **Then** the raw entries for the same one-year window are plotted (lens toggle preserves the scale)
- **And** the deliberate trend-study count has increased

###### Scenario: Saving repaints the morning picture in place

- **Given** the front-page graph ends at Thursday 23 July's trend point
- **When** Clemens saves 82.2 kg on Friday 24 July
- **Then** the save confirmation appears as before
- **And** the graph and the glance line refresh in place — without a page reload — to include today's entry

###### Scenario: A graph hiccup never blocks the log

- **Given** the graph data cannot be fetched
- **When** Clemens opens `/` and saves 82.2 kg
- **Then** the graph area is simply absent, the weight field is focused, and the save confirms normally

###### Scenario: An empty record keeps the front page simple

- **Given** the tracker has no entries yet
- **When** Clemens opens the entry screen
- **Then** no graph area is shown and the weight field is focused, exactly as before

###### Scenario: The graph never taxes the entry (@property)

- **Given** Clemens opens the entry screen on his phone over a mobile connection
- **Then** the screen is interactive within 2 seconds with the weight field focused and decimal keypad shown
- **And** the graph's rendering never delays typing readiness or steals focus

##### Acceptance Criteria

- [ ] Entry screen (`/`) renders the graph above the entry form with the full controls of `/graph`: Trend/Raw lens toggle + 1W/1M/3M/6M/1Y/All scale picker; defaults Trend at 3M (A17).
- [ ] Lens/scale behavior identical to `/graph`: toggling the lens preserves the chosen scale; both lenses render from the same stores/series as the History-page graph for the same entry set.
- [ ] Ambient renders (page open at defaults, post-save refresh) add 0 to the deliberate trend-study counter (KPI-3); explicit lens/scale taps register as deliberate study (A19); ambient graph presence is recorded as its own telemetry event (KPI-7).
- [ ] After a successful save, the graph refreshes in place (no reload) to include the new entry; the glance line co-refreshes as today (A15).
- [ ] Graph data failure degrades to an absent graph area; entry, save, and confirmation are never blocked or delayed; 0 entries → no graph area.
- [ ] Entry primacy preserved: interactive ≤2 s, field autofocus + decimal keypad unchanged; keypad covering the graph on open is accepted (D6).
- [ ] New elements honor calm-theme rules: both schemes at WCAG contrast (text ≥4.5:1, non-text ≥3:1), touch targets ≥44 px, zero new external origins.

##### Technical Notes

- All substrate exists: uPlot vendored with token-driven theming (`--chart-*`, ADR-007), `TrendProjection`/`WeightHistory` reads, device-day framing (`?today=`, fix-device-day-reads), inline save flow, `append_event` trail.
- KPI-3 purity likely means the front-page graph cannot reuse `GET /trend` as-is (it emits the deliberate event unconditionally) — surface/mechanism is DESIGN's call; the behavioral requirement is the ambient/deliberate separation (A19), precedent D-13/D-14.
- G-5's "0 new entry-screen scripts" AT clause must be renegotiated at DISTILL (see System Constraints).
- Dependencies: US-002/004/005 (graph + lenses), US-007 (glance), US-009 (chart theming) — all delivered.

#### US-011: The last week of numbers under his thumb

`job_id: track-true-weight-trend` · Slice 01 · Must · ~0.25–0.5 day

##### Problem

"Did I actually log yesterday? What did Tuesday say — was 82.6 real or a typo?" Today those raw-number sanity checks mean opening the graph and squinting at points. Clemens wants the last handful of exact values sitting quietly below the form, where his eye already is.

##### Elevator Pitch

- **Before**: Opens `/` → only yesterday's single value shows (`yesterday: 82.4 kg`); older numbers require the History tap and reading raw points off a chart.
- **After**: Opens `/` → below the Save button: `Thu 23 Jul — 82.4 kg`, `Wed 22 Jul — 82.6 kg`, `Tue 21 Jul — 82.4 kg`, … (his last 7 entries, newest first). After saving, `Fri 24 Jul — 82.2 kg` appears at the top without a reload.
- **Decision enabled**: "Is my record intact and sane — anything to correct before I trust this week's trend?" — a record-integrity check at a glance, no navigation.

##### Domain Examples

1. *Full week*: entries Fri 17 – Thu 23 Jul (Sun 19 missed) plus today's save → after saving on Fri 24 Jul the list reads: 24, 23, 22, 21, 20, 18, 17 Jul — 7 entries spanning 8 calendar days; Sun 19 is simply absent.
2. *Typo spotting*: the list shows `Tue 21 Jul — 28.4 kg`… impossible — it can't: 28.4 would have been rejected at save (A1). Realistic case: `Tue 21 Jul — 83.4 kg` stands out against neighbors at 82.4–82.6 → he corrects it through the existing editing flow (unchanged, D9); on next render the list shows 82.4.
3. *Young record*: 3 entries → 3 rows; 0 entries → no list at all (form is the whole screen).
4. *Display-only*: rows carry no buttons, links, or edit affordances — looking is not touching.

##### UAT Scenarios (BDD)

###### Scenario: The last week of numbers is one look away

- **Given** Clemens has entries on 17, 18, 20, 21, 22, 23 July 2026 and saves 82.2 kg on Friday 24 July
- **When** he looks below the entry form
- **Then** he sees his 7 most recent entries newest first, each as date + weight (e.g., "Fri 24 Jul — 82.2 kg")
- **And** Sunday 19 July appears nowhere — no zero, no placeholder row

###### Scenario: Today's save goes straight to the top

- **Given** the recent list starts with "Thu 23 Jul — 82.4 kg"
- **When** Clemens saves 82.2 kg on Friday 24 July
- **Then** "Fri 24 Jul — 82.2 kg" appears at the top of the list without a page reload

###### Scenario: A young record shows what it has

- **Given** the tracker holds only 3 entries
- **When** Clemens opens the entry screen
- **Then** the list shows exactly those 3 entries
- **And** with 0 entries no list is shown at all

###### Scenario: Looking is not touching

- **Given** the recent list is visible
- **Then** its rows offer no edit or delete affordances
- **And** each displayed value equals the stored entry the graph and yesterday anchor render for that day

##### Acceptance Criteria

- [ ] Below the entry form, the last 7 **entries** (not days) render newest first as date + kg at 0.1 precision; fewer entries → shorter list; 0 entries → no list (A18).
- [ ] Missing days are simply absent — no zeros, placeholders, or interpolated rows.
- [ ] After a successful save, the list refreshes in place (no reload) with the saved entry at the top (A15).
- [ ] Display-only: no edit/delete affordances; the editing flow is unchanged (D9).
- [ ] Values come from the same entry store as the graph and yesterday anchor (single source); list rendering never delays entry readiness (≤2 s guardrail).

##### Technical Notes

- The recent-weights map for the yesterday anchor already ships entries to the page; whether the list reuses/extends that context or the history read is a DESIGN call (read-only either way).
- Rides Slice 01 with US-010; establishes the entries-list presentation idiom that US-012's complete list reuses.

#### US-012: One place holds the whole record

`job_id: track-true-weight-trend` · Slice 02 · Must · ~0.5–1 day

##### Problem

The graph shows the shape of Clemens's record, but the exact values are locked inside raw plot points — the complete numeric record he has been building since March is visible nowhere. When he wants to audit it ("what did I actually weigh through the vacation week? which day holds the typo?"), the tool has no page that simply *shows the record*.

##### Elevator Pitch

- **Before**: Taps History on `/` → `/graph` shows only the chart; no complete numeric record exists anywhere in the UI.
- **After**: Taps **History** → the full-history page shows the full-control graph on top and, below it, his **complete record**: all 128 entries from `Fri 24 Jul — 82.2 kg` back to `Tue 3 Mar — 83.4 kg`, newest first, date + kg.
- **Decision enabled**: "Which exact day and value needs correcting — and can I trust every point this trend is built on?" — the full-record audit that `js-2-judge`'s deliberate study sometimes demands.

##### Domain Examples

1. *Full audit*: 128 entries Tue 3 Mar – Fri 24 Jul 2026 (vacation gap 10–17 Apr) → History page lists all 128, newest first; the April gap days are simply absent from the list, exactly as they are gaps in the raw plot.
2. *Deep link*: his bookmarked `/graph?view=raw&scale=1Y` still opens raw at 1Y — now with the complete list below; back-link to `/` unchanged.
3. *Deliberate study counted*: opening the History page registers one deliberate trend-study session (A19) — this is where KPI-3 now lives.
4. *Empty record*: 0 entries → the empty-invite ("log your first weight") shows, no list, exactly as today.

##### UAT Scenarios (BDD)

###### Scenario: History leads to the whole record

- **Given** Clemens has 128 entries between 3 March and 24 July 2026
- **When** he taps "History" on the entry screen
- **Then** the full-history page shows the graph with its lens toggle and scale picker on top
- **And** below it, all 128 entries newest first, each as date + weight in kg

###### Scenario: The list and the plot tell the same story

- **Given** the full-history page is open with the Raw lens at "All"
- **Then** the list contains exactly the stored entries — the same dates and values the raw plot renders
- **And** days without an entry appear in neither

###### Scenario: Deliberate study is counted where it happens

- **Given** the deliberate trend-study count for this week is 1
- **When** Clemens opens the History page
- **Then** the count for the week reads 2

###### Scenario: Old bookmarks still work

- **Given** Clemens opens the deep link `/graph?view=raw&scale=1Y`
- **Then** the page opens with the Raw lens at the 1Y scale, the complete list below, and the back-link to the entry screen
- **And** toggling the lens still preserves the chosen scale

###### Scenario: An empty record still invites

- **Given** the tracker has no entries yet
- **When** Clemens opens the History page
- **Then** the empty-state invite to log the first weight shows, and no list is rendered

###### Scenario: The full record arrives without a wait (@property)

- **Given** the record holds at least 300 entries
- **When** Clemens opens the History page on his phone over a mobile connection
- **Then** the page is interactive within 2 seconds with the complete list present

##### Acceptance Criteria

- [ ] The History destination shows the full-control graph (lens toggle + scale picker, unchanged behavior) on top and the complete entries list below, newest first, date + kg at 0.1 precision.
- [ ] The list renders exactly the stored entries (same source as the plot); missing days absent from both.
- [ ] Existing `/graph` behaviors preserved: deep links with `?view=`/`?scale=` work unchanged, lens toggle preserves scale, empty-invite on 0 entries, back-link to `/` (A16).
- [ ] Opening the History page registers one deliberate trend-study session (KPI-3, A19).
- [ ] Page interactive ≤2 s on phone with a ≥300-entry list (G-2 extended to the combined page).
- [ ] List presentation follows calm-theme rules in both schemes (contrast, neutral tone).

##### Technical Notes

- A16: the combined page extends the existing `/graph` route/template rather than adding a new route (keeps deep links, back-link, empty-invite by construction) — confirmable at DESIGN if a strong reason emerges for a new route, provided `/graph` deep links keep working.
- The list is a read of the already-fetched entry data (raw lens fetches it today); rendering approach for long lists = DESIGN within the ≤2 s AC.
- Dependencies: US-002/005/009 (delivered); Slice 01's list idiom (presentation reuse, not a hard dependency).

### [REF] Out of Scope

Pagination, search, or filtering of the history list; editing from either list (editing flow unchanged, D9); per-entry annotations/notes; scale/lens persistence across surfaces or visits (A17); moving or removing the glance line (kept, A14 — OQ-7 to override); `/stats` presentation changes; goal lines, predictions, streaks, color judgment; configurable list length; CSV/export. Everything on prior features' out-of-scope lists remains out.

### [REF] Walking Skeleton Strategy

**N/A — brownfield.** The full production vertical (ports → routes → templates → deploy with CI gates) exists. This feature rearranges and extends two existing pages over shipped read surfaces; each slice deploys through the existing pipeline and is dogfooded with the next real morning entry.

### [REF] Driving Ports

Behavioral, solution-neutral; DESIGN owns shapes and adapters. Read-only ports must never expose write methods (CLAUDE.md / ADR-005).

- **WeightHistory** (driving, read-only) — read surface must answer: the N most recent entries (front-page list, N=7) and the complete record (History-page list). Existing `entries_in(ALL)` / recent-map reads may already cover both; shape = DESIGN. Used by US-011, US-012 (and US-010's Raw lens as today).
- **TrendProjection** (driving, read-only) — unchanged: the same single smoothed series feeds the front-page and History-page graphs (and the glance). No second algorithm.
- **WeightLogging** (driving) — unchanged; the save response/refresh flow may carry or trigger the updated graph + recent list, precedent: the glance field (D-13). Never a port widening decision here — DESIGN's call.
- **Telemetry** (driven, established `append_event` trail) — ambient front-page graph presence recorded as its own event (KPI-7); deliberate trend study per A19 (History opens + explicit lens/scale interactions); ambient and deliberate structurally separated (precedent D-13/D-14). Naming = DESIGN.

### [REF] Pre-Requisites

None blocking DESIGN. `home-trend-display` and `calm-visual-theme` delivered 2026-07-23 ✅. For DESIGN: pick the graph-delivery mechanism honoring ≤2 s entry readiness + degrade-to-absent, and the ambient/deliberate telemetry mechanism (A19). For DISTILL: **consciously renegotiate calm-visual-theme's G-5 clause "0 new entry-screen scripts"** (intent preserved as zero external origins + entry primacy; see System Constraints) — never silently break or delete that AT. Production pipeline live; same-day dogfood possible.

### [REF] Outcome KPIs

**Objective**: The whole progress picture becomes the front door — every morning opens on the curve, the entry, and the recent record, with the complete history one deliberate tap away.

Extends the existing registry (KPI-1/2/4/5/6 and G-1…G-5 unchanged except as noted). New and redefined:

| # | Who | Does What | By How Much | Baseline | Measured By | Type |
|---|-----|-----------|-------------|----------|-------------|------|
| 7 | Clemens | sees the trend curve at the moment of logging | graph present on ≥95% of logging days (once entries exist) | 0% (curve only behind the History tap) | ambient home-graph telemetry event paired with `entry.saved` per calendar day, surfaced on /stats | Leading |

**KPI-3 redefinition (required by this feature)**: today `trend.view.opened` fires unconditionally on the trend-series read — an ambient front-page trend render every morning would inflate the "deliberate study" counter ~7×, destroying the metric US-007 deliberately protected. Redefined meaning: **KPI-3 counts deliberate trend-study engagements = History-page opens + explicit lens/scale interactions (either surface)** (A19). Ambient renders (front-page open at defaults, post-save refresh) emit the ambient event feeding KPI-7 instead and add 0 to KPI-3. Target stays ≥3 sessions/week for now, with the standing reviewer note extended: a *further* KPI-3 decline after this ships is an **expected substitution** (ambient curve satisfies routine judging), not a regression; retire or retarget KPI-3 at a later weekly review if it stabilizes near zero.

**KPI-5 semantics**: unchanged. The glance line is kept (A14), still instrumented by its existing event paired with `entry.saved`. The ambient graph does not participate in KPI-5; it has its own presence event (KPI-7).

- **Guardrails (must not degrade)**: KPI-1 entry speed (median ≤5 s, p90 ≤10 s); entry screen interactive ≤2 s **with the graph present**; KPI-3 counter unpolluted by ambient renders (0 added by a log-only morning); trend determinism (G-3); zero lost entries (G-1); contrast AA both schemes for new elements (G-4); zero new external origins (G-5 intent — script-count clause renegotiated at DISTILL, see Pre-Requisites).
- **Hypothesis**: We believe opening the tracker on the trend curve + recent record for Clemens will make full progress-judgment ambient (graph present ≥95% of logging days) without slowing entry (KPI-1 and ≤2 s unchanged), reinforcing the logging habit (KPI-2, North Star) because every morning now shows the payoff of the unbroken record.
- **Measurement plan**: ambient graph event + deliberate-study events via the existing `append_event` trail; pairing computed at read time on /stats (KPI-5 precedent); reviewed in the established weekly /stats cadence. No new instrumentation infrastructure.

### [REF] DoR Validation

| DoR Item | US-010 | US-011 | US-012 | Evidence |
|----------|--------|--------|--------|----------|
| 1. Problem clear, domain language | PASS | PASS | PASS | Curve-shape behind a skipped tap; raw-number sanity checks; no page shows the record |
| 2. Persona specific | PASS | PASS | PASS | `clemens` — phone-first, 06:45, 82 kg range, minimalism values |
| 3. 3+ domain examples, real data | PASS (5) | PASS (4) | PASS (4) | Real dates/values (82.2 on Fri 24 Jul; Sun 19 Jul gap; 128 entries since Tue 3 Mar; 83.4 typo) |
| 4. UAT 3–7 scenarios G/W/T | PASS (7) | PASS (4) | PASS (6) | Happy, KPI-purity, deliberate-interaction, refresh, degrade, empty, @property paths covered |
| 5. AC derived from UAT | PASS | PASS | PASS | AC lists map to scenarios plus quantified rules (≤2 s, 7 entries, 0.1 kg, 0-added-to-KPI-3, ≥300-entry load) |
| 6. Right-sized (1–3 d, 3–7 sc.) | PASS | PASS | PASS | ~0.5–1 d / ~0.25–0.5 d / ~0.5–1 d; 7/4/6 scenarios; each demoable in one session |
| 7. Technical notes/constraints | PASS | PASS | PASS | Notes per story + System Constraints (KPI-3 mechanism = DESIGN; G-5 renegotiation flagged; read-only ports) |
| 8. Dependencies resolved/tracked | PASS | PASS | PASS | US-002/004/005/007/009 all delivered 2026-07-23; slice-02 reuses slice-01's list idiom (soft) |
| 9. Outcome KPIs, numeric targets | PASS | PASS | PASS | KPI-7 (≥95% presence), KPI-3 redefinition with 0-pollution guardrail, measurement methods named |

**DoR Status: PASSED (3/3 stories, 9/9 items).**

**Requirements completeness score: 0.96** — functional behavior fully specified (layout order, controls parity, refresh, degrade, empty states, list rules, deep-link preservation, telemetry separation), NFRs quantified (≤2 s both pages, precision, contrast, determinism, KPI-1 guardrail), business rules explicit (last-7-entries semantics, per-surface scale, ambient/deliberate split). Deductions: A19's "interactions count as deliberate" boundary and A14's keep-the-glance default are analyst-chosen pending user confirmation (OQ-7/OQ-8); front-page default scale 3M is an A17 default (OQ-9).

### [REF] DoD 9-Item Checklist

Per story, at DELIVER completion (unchanged pattern):

1. All UAT scenarios green (automated).
2. Supporting unit/integration tests green — including the consciously amended G-5 clause (no silent breakage of calm-theme ATs).
3. Code refactored; per-feature mutation gate ≥80% on modified files.
4. Code reviewed (self-review with reviewer agent — solo project).
5. Merged to main.
6. Deployed to the phone-reachable production URL via the existing pipeline.
7. Dogfooded same day with a real morning entry on the graph-first front page (slice 01) / a real History-page audit (slice 02).
8. KPI-7 ambient event emitting; KPI-3 purity verified on /stats (log-only morning adds 0); KPI-1/≤2 s guardrails verified.
9. Story demonstrable end-to-end on the phone.

### [REF] Wave Decisions Summary

Locked upstream: D1–D5 + user decisions D6–D9 (entry primacy with keypad-cover accepted; full-control front-page graph; combined full-history page; last-7 display-only list). Prior assumptions A1–A13 unchanged and still binding.

New assumptions (subagent mode — chosen autonomously, flagged for confirmation):

- **A14** The glance text line (`Trend: 82.3 kg · ↓0.25 kg/week`) is **kept** alongside the graph — it carries the exact numbers and the KPI-5 event; the curve shows shape, the line states the verdict. (Override via OQ-7.)
- **A15** The front-page graph and the recent-7 list refresh **in place** after a successful save (consistency with the glance's established in-place refresh); both degrade to absent on data failure and never block entry or save.
- **A16** The History destination is the existing `/graph` page **extended** with the complete entries list (no new route): deep links, lens/scale behavior, empty-invite, and back-link preserved by construction.
- **A17** Both graph surfaces open at the existing defaults (Trend lens, 3M — A4 extended); each surface holds its own lens/scale selection; selections do not persist across surfaces or visits.
- **A18** Front-page list = last 7 **entries** (not last 7 days), reverse-chronological, date + kg at 0.1 precision; missing days simply absent; <7 entries → shorter list; 0 → no list; display-only.
- **A19** KPI-3 redefined: deliberate trend study = History-page opens + explicit lens/scale interactions (either surface). Ambient renders (front-page open at defaults, post-save refresh) never count and are recorded by a separate ambient event (KPI-7). Event naming/mechanism = DESIGN.

Open questions (non-blocking; defaults above apply unless overridden):

- **OQ-7** Keep the glance text line above the form now that the curve is present (A14 default: keep), or retire it in favor of the graph alone (this would also retire/replace KPI-5's instrument)?
- **OQ-8** Confirm the KPI-3 boundary (A19): should front-page lens/scale taps count as deliberate study, or only History-page opens?
- **OQ-9** Confirm the front-page default scale (A17: 3M, matching `/graph` today) — or prefer a tighter ambient window (e.g., 1M)?

Risk notes: **product risk** = entry-screen crowding — a graph, glance line, form, list, and link on one five-second screen (mitigated by the entry-primacy @property AC, calm-theme rules, and D6's explicit acceptance of keypad-cover; falsifiable via slice-01 dogfood). **KPI risk** = KPI-3 inflation if the ambient/deliberate separation ships late or leaky — pinned as a hard behavioral AC in slice 01. **AT-contract risk** = calm-visual-theme's G-5 "0 new entry-screen scripts" clause will fail against a front-page graph — flagged for conscious renegotiation at DISTILL, never silent deletion. Technical risk negligible (all substrate delivered and mutation-tested). JTBD traceability intact (all stories N:1 to the single validated job via existing moments js-4-glance / js-2-judge; no new moment needed). No DIVERGE wave for this delta — consistent with the product's accepted pattern (user = customer; decisions D6–D9 made directly by the user); noted as accepted risk, not a gap. Density: lean + ask-intelligent; triggers evaluated (AC ambiguity ≥2 stories, ≥3 bounded contexts, ≥3 personas, compliance terms, WS strategy D) — **none fired** → silent lean. Density telemetry skipped: `scripts/shared/telemetry.py` not present in this repository (recorded here in lieu of the event, per prior features).

## Wave: DESIGN

Architect: solution-architect (Morgan), 2026-07-24. Mode: Propose (4 open calls analyzed against the live codebase; user accepted all recommendations and confirmed OQ-7/8/9 defaults). SSOT updated: `docs/product/architecture/brief.md` (§ Application Architecture — graph-first-home delta paragraph, ADR index) + new `adr-008-front-page-graph-delivery.md` + new `adr-009-intent-telemetry.md`. ADR-001…007 unchanged; ADR-004/006 not superseded (ADR-009 retires only the `trend.view.opened` *emission*). No C4 L1/L2 changes (no new containers, actors, or external systems); no L3 (below the 5-component threshold). Per-wave peer review deferred to the orchestrator's consolidated review (precedent: home-trend-display DESIGN — no contested ADR, no novel pattern, no security-surface change; the beacon route sits behind the existing AccessGate). Density: lean, Tier-1 [REF] only, no Tier-2 expansions; density telemetry skipped (`scripts/shared/telemetry.py` absent).

### [REF] DDD List

Numbering continues the global DESIGN sequence from D-14 (home-trend-display).

- **D-15 Front-page graph delivery = async fetch via shared extracted `graph.js`** (ADR-008) — **accepted**. One chart code path for both surfaces makes the US-010 lens/scale-parity AC true by construction; input readiness stays server HTML. Rejected: inline-embedded default series (two data paths, two-armed save refresh); server-side SVG (loses D7 controls, second render path).
- **D-16 Intent telemetry route-level; data reads become pure** (ADR-009) — **accepted**. `home.graph.shown` on `GET /` (ambient, KPI-7), `trend.study.opened` on `GET /graph` render, `trend.study.interaction` via beacon `POST /telemetry/trend-study` (closed vocabulary, unknown → 400); `GET /trend` stops emitting (historical rows preserved; /stats `trend_view_opened_count` frozen). Log-only morning adds 0 to KPI-3 structurally. Rejected: separate ambient endpoint keeping `trend.view.opened` (raw-tap undercount + History double-count); History-opens-only (contradicts confirmed A19); `?ambient=` suppression (fragile convention, ADR-006 precedent).
- **D-17 History destination = extended `/graph`** (A16 confirmed) — **accepted**. Deep links, back-link, empty-invite preserved by construction; the complete list is **server-rendered from `all_entries()`** and always shows the whole record — independent of the chart's selected window (US-012: list ≠ chart window). Rejected: new `/history` route + redirect (permanent redirect maintenance, zero behavioral gain).
- **D-18 Read shape = reuse `all_entries()` + pure slicing; zero port changes** — **accepted**. Entries arrive newest-first, so last-7 = `entries[:7]` (pure); the 4-entry `recent_weights_map` (yesterday anchor) keeps its own contract untouched. Rejected: new port method / SQL `LIMIT` (widening for a dataset of hundreds of rows; revisit only on a measured ≤2 s violation).
- **D-19 In-place refresh after save** — **accepted**. `POST /entries` response gains a `recent` field (route-level enrichment, precedent `glance`/`confirmation`; `WeightLogging` universe unchanged); the graph refreshes by refetching at the current lens/scale (telemetry-free per D-16, so a post-non-default-scale save costs nothing); any refresh failure → absent, never stale (D-13 pin extended).
- **D-20 Per-surface lens/scale state** (A17 confirmed) — **accepted**. Front page ignores query params and always opens Trend/3M; `/graph` keeps honoring `?view=`/`?scale=`; no persistence across surfaces or visits. OQ-7 (glance kept), OQ-8 (front-page taps deliberate → beacon exists), OQ-9 (3M default) all confirmed at DISCUSS defaults.

### [REF] Component Decomposition

Delta only — authoritative table: `brief.md` § Component Decomposition and Ports.

| Component | Path | Change |
|---|---|---|
| Shared graph module | `src/weight_tracker/web/static/graph.js` | **CREATE NEW** (extraction of `graph.html`'s inline chart JS — fetch, grid builders, themed uPlot render, lens/scale state, matchMedia re-render; relocated, not rewritten). Only new asset. |
| Entry template | `src/weight_tracker/web/templates/index.html` | EDIT: graph mount + lens/scale controls above the form; last-7 list below (server-rendered Jinja, display-only); deferred `uplot.iife.min.js` + `graph.js`; save handler additionally updates the list from `recent` and triggers the graph refetch. Autofocus/keypad/save flow untouched. |
| History template | `src/weight_tracker/web/templates/graph.html` | EDIT: inline chart JS replaced by the shared module include; complete entries list below the chart (server-rendered Jinja loop over `all_entries()`); wording = DISTILL. |
| Route `GET /` | `src/weight_tracker/web/routes.py` | EDIT: context + `recent_entries` (pure slice of the already-fetched list); appends `home.graph.shown` when entries exist. |
| Route `GET /graph` | `src/weight_tracker/web/routes.py` | EDIT: gains the store read for the complete-list context; appends `trend.study.opened`. |
| Route `GET /trend` | `src/weight_tracker/web/routes.py` | EDIT (narrowing): `trend.view.opened` emission removed → pure read. |
| Route `POST /entries` | `src/weight_tracker/web/routes.py` | EDIT: response + `recent` field (route-level; port untouched). |
| Route `POST /telemetry/trend-study` | `src/weight_tracker/web/routes.py` | **CREATE** (beacon): closed vocabulary → one `trend.study.interaction` append via existing `append_event`; unknown → 400, never 500; behind AccessGate. |
| Route `GET /stats` | `src/weight_tracker/web/routes.py` | EDIT: new rolling-week counters for `home.graph.shown` / `trend.study.*` via existing `count_events_since`; `trend_view_opened_count` stays as frozen historical counter. |
| Theme stylesheet | `src/weight_tracker/web/static/theme.css` | EDIT: entries-list block + front-page chart block, tokens only (both schemes AA, ≥44 px controls). |
| Service worker | `src/weight_tracker/web/static/sw.js` | EDIT: `graph.js` joins APP_SHELL; cache-name bump = DELIVER. |
| `ports.py`, `core/*`, `composition.py`, `shell/*` | — | **UNCHANGED** (± a trivial pure slice helper if the crafter prefers it over template slicing — same component either way). |

### [REF] Driving Ports

| Port | Delta |
|---|---|
| `WeightHistory` | **Unchanged.** Both new read needs (last-7, complete record) are satisfied by the existing `all_entries()` newest-first read + pure slicing — the port gains **no methods at all** (strongest form of "no write methods"). |
| `TrendProjection` / `GlanceProjection` | **Unchanged.** Same single smoothed series feeds both graphs and the glance; no second algorithm, no new windows. |
| `WeightLogging` | **Unchanged.** `recent` response field = driving-adapter (route) concern, precedent D-13; bounded-change universe stays one `{date}` row + one `entry.saved` event. |
| Telemetry beacon (new driving *route*, not a new port) | Drives the existing `EntryStorePort.append_event`; bounded-change universe = exactly one event append from a closed vocabulary. |
| `AccessGate` | Unchanged; guards the beacon like every route. |

### [REF] Driven Ports + Adapters

**None new — explicitly.** No new I/O, storage, clock use, or external dependency ⇒ no new Earned-Trust probes. Fault injection instead (DISTILL): graph fetch failure → absent area, entry/save unblocked; post-save refresh failure → absent, never stale; beacon malformed/unknown payload → 400, never 500, never a trail write; beacon network failure → zero UI effect. `telemetry_store.py` queries are name-parameterised and need no change.

### [REF] Technology Choices

**Zero new dependencies, zero new external origins.** `graph.js` is an extraction of shipped code, not new technology; uPlot stays vendored and byte-identical; system fonts, token theming (ADR-007) carry over. Enforcement tooling unchanged (import-linter layers, mypy strict, AST probe-presence gate — no new adapters to cover).

### [REF] Decisions Table

| # | Decision | ADR |
|---|---|---|
| D-15 | Front-page graph = async fetch via shared extracted `graph.js`; degrade-to-absent; entry readiness server HTML | ADR-008 |
| D-16 | Intent telemetry route-level (`home.graph.shown`, `trend.study.opened`, `trend.study.interaction` beacon); `trend.view.opened` emission retired; data reads pure | ADR-009 |
| D-17 | History = extended `/graph`; complete list server-rendered from `all_entries()`, independent of chart window | brief.md |
| D-18 | Last-7 + complete list via existing `all_entries()` + pure slicing; zero port changes | brief.md |
| D-19 | Save refresh: `recent` response field (route-level) + client refetch at current lens/scale; absent-never-stale | brief.md |
| D-20 | Per-surface lens/scale (front page paramless Trend/3M; `/graph` honors deep links); OQ-7/8/9 at defaults | brief.md |

### [REF] Reuse Analysis

Brownfield — one CREATE-NEW asset (extraction) + one CREATE route; everything else EXTENDs shipped components (codebase verified 2026-07-24).

| Existing component | File | Verdict | Contract shape · universe · crafter assertion mechanism |
|---|---|---|---|
| Chart JS (fetch/render/state/theming) | `web/templates/graph.html` → `web/static/graph.js` | **EXTRACT + REUSE** (2 consumers) | pure render over fetched data · DOM effects bounded to its mount · existing US-002/005/009 ATs re-run on both surfaces |
| Route `GET /` + `index.html` | `web/routes.py`, `web/templates/index.html` | EXTEND | bounded-change · 0–1 `trend.glance.shown` + 0–1 `home.graph.shown` appends per render · AT on rendered HTML + /stats |
| Route `GET /graph` + `graph.html` | `web/routes.py`, `web/templates/graph.html` | EXTEND | bounded-change · one `trend.study.opened` append + store read · AT on rendered HTML + deep-link scenarios |
| Route `GET /trend` | `web/routes.py` | **MODIFY (narrow)** | becomes pure read · empty mutation universe · AT: fetch adds 0 events to the trail |
| Route `GET /entries` | `web/routes.py` | REUSE unchanged | pure read (already emission-free) |
| Route `POST /entries` | `web/routes.py` | EXTEND (response only) | port universe unchanged (one `{date}` row + one `entry.saved`) · `recent` field · AT on save-response JSON |
| `EntryStorePort` / `ports.py` | `ports.py` | REUSE unchanged | `all_entries()` + `append_event` already carry everything |
| Domain core | `core/trend.py`, `core/glance.py`, `core/types.py` | REUSE unchanged | pure-function · no mutation universe · existing PBT suites stand |
| Telemetry queries | `shell/telemetry_store.py` | REUSE unchanged | name-parameterised pure reads |
| Theme stylesheet | `web/static/theme.css` | EXTEND | static asset · empty mutation universe · DISTILL contrast checker (G-4 pattern) |
| Service worker | `web/static/sw.js` | EXTEND | APP_SHELL append + cache bump (DELIVER) |
| Beacon route | `web/routes.py` | **CREATE NEW** | bounded-change · exactly one event append from closed vocabulary · AT: unknown payload → 400 + zero trail writes |

### [REF] C4 Note

**No diagram changes.** L1/L2 in `brief.md` remain accurate: everything lands inside the existing Browser/PWA-shell and App Server containers. No L3 — below the 5-component threshold.

### [REF] Open Questions / DISTILL–DELIVER Notes

| # | Note | Owner |
|---|---|---|
| Q1 | **G-5 renegotiation (flagged since DISCUSS)**: consciously amend calm-visual-theme's "0 new entry-screen scripts" AT clause — `/` gains `uplot.iife.min.js` + `graph.js`, both same-origin vendored; pin the surviving intent as zero new external origins + entry-primacy @property. Never silent deletion. | DISTILL |
| Q2 | KPI-3 /stats counting detail: raw `trend.study.*` event counts vs read-time session-collapse against the "≥3 sessions/week" target — write-time stays raw either way (D-16); pin the read-time rule. | DISTILL |
| Q3 | KPI-7 oracle wording: `home.graph.shown` is a server-side delivery proxy (data-available-at-render, glance precedent), not client paint — phrase oracles accordingly. | DISTILL |
| Q4 | Entry-primacy @property must also assert the graph never steals focus or scroll position on init (D6 keeps keypad-cover accepted, focus theft is not). | DISTILL |
| Q5 | `sw.js` cache-name bump + outcome-registry delta entries (per established convention; `nwave-ai outcomes check-delta` re-check). | DELIVER |

### Changed Assumptions

**None.** A1–A13 and A14–A19 all hold as written; A16 (extend `/graph`) and A17 (per-surface defaults, 3M) moved from assumption to confirmed decision (D-17, D-20) without modification; OQ-7/8/9 resolved at their DISCUSS defaults. No upstream-changes propagation needed.

## Wave: DISTILL

Acceptance designer, 2026-07-24. Reconciliation gate: all wave decisions read (DISCUSS D1–D9/A14–A19, DESIGN D-15–D-20, ADR-008/009; no DEVOPS wave — brownfield, existing pipeline, WARN logged) — **0 contradictions**. Deliverable type: `application` (no `.nwave/des-config.json`, no global default → FS detection). Infrastructure policy: `--policy=inherit`, zero missing ports (all mechanisms already tabled). Density: lean, Tier-1 [REF] only; density telemetry skipped (`scripts/shared/telemetry.py` absent — recorded here per precedent).

### [REF] Scenario List

Scenario SSOT: the two `.feature` files below. 19 scenarios, all `@pending` (one-at-a-time, ADR-025). Error/edge share: 8/19 (@error 6 + degrade/purity clauses inside others) ≈ 42%.

`tests/weight-trend-tracker/acceptance/milestone-8-graph-first-front-page.feature` (Slice 01 — US-010 + US-011, 13 scenarios):

| Scenario | Tags |
|---|---|
| The morning opens on the whole picture | `@driving_port @US-010 @contract-shape:pure-function` |
| An ambient morning never counts as deliberate study | `@driving_port @kpi @real-io @adapter-integration @US-010 @contract-shape:bounded-change` |
| Choosing a lens or scale is deliberate study | `@driving_port @driving_adapter @kpi @real-io @US-010 @contract-shape:bounded-change` |
| Saving repaints the morning picture in place | `@driving_port @US-010 @contract-shape:bounded-change` |
| A graph hiccup never blocks the log | `@driving_port @error @US-010 @contract-shape:bounded-change` |
| An empty record keeps the front page simple | `@driving_port @error @US-010 @US-011 @contract-shape:pure-function` |
| The graph never taxes the entry | `@driving_port @property @kpi @US-010 @contract-shape:pure-function` |
| The last week of numbers is one look away | `@driving_port @US-011 @contract-shape:bounded-change` |
| Today's save goes straight to the top | `@driving_port @US-011 @contract-shape:bounded-change` |
| A young record shows what it has | `@driving_port @US-011 @contract-shape:pure-function` |
| Looking is not touching | `@driving_port @US-011 @contract-shape:pure-function` |
| A garbled study signal is turned away without a mark | `@driving_port @driving_adapter @error @real-io @US-010 @contract-shape:unbounded-preservation` |
| A stranger's study signal leaves no mark | `@driving_port @driving_adapter @error @US-010 @contract-shape:unbounded-preservation` |

`tests/weight-trend-tracker/acceptance/milestone-9-whole-record-history.feature` (Slice 02 — US-012, 6 scenarios):

| Scenario | Tags |
|---|---|
| History leads to the whole record | `@driving_port @US-012 @contract-shape:pure-function` |
| The list and the plot tell the same story | `@driving_port @US-012 @contract-shape:pure-function` |
| Deliberate study is counted where it happens | `@driving_port @kpi @real-io @adapter-integration @US-012 @contract-shape:bounded-change` |
| Old bookmarks still work | `@driving_port @US-012 @contract-shape:pure-function` |
| An empty record still invites | `@driving_port @error @US-012 @contract-shape:pure-function` |
| The full record arrives without a wait | `@driving_port @property @kpi @US-012 @contract-shape:pure-function` |

The two `@property` scenarios are layer-3 (real HTTP + SQLite) → example-pinned per Mandate 9/11; the quantified budgets (≤2 s, ≥300 entries) live in the scenario text. Pure-core PBT suites (trend/glance/validation) stand unchanged — no new domain math shipped (zero new core functions), so no new PBT files; the crafter adds paired PBTs only if a pure slice helper materializes (D-18 note).

### [REF] Walking Skeleton Strategy

**N/A — brownfield (locked D2).** The production vertical and its `@walking_skeleton` scenario (`walking-skeleton.feature`, green) exist; this feature rides them. Per the Architecture of Reference + project policy (inherit): driving = TestClient over `build_app` (production root), driven-internal = real SQLite on `tmp_path` (prod pragmas), driven-external = `FakeClock` only. No strategy negotiation performed.

### [REF] Adapter Coverage

**No new driven adapters (DESIGN: explicitly none)** ⇒ no new `@real-io` adapter scenarios owed and no new Earned-Trust probes. Existing adapters keep their shipped coverage. New *driving* route (beacon) covered below. Fault-injection coverage per DESIGN's list:

| Fault | Scenario |
|---|---|
| Graph/series fetch failure → absent area, entry/save unblocked | A graph hiccup never blocks the log |
| Failed series read leaves no trail mark (pure read, D-16) | A graph hiccup never blocks the log |
| Beacon unknown vocabulary → 400, never 500, zero trail writes | A garbled study signal is turned away without a mark |
| Beacon without session → door, zero trail writes | A stranger's study signal leaves no mark |
| 0 entries → no graph area / no lists / invite preserved | An empty record keeps the front page simple; An empty record still invites |

### [REF] Driving Adapter Coverage

Every DESIGN entry point exercised via its real protocol (TestClient = real HTTP layer, ASGI):

| Entry point (DESIGN) | Scenarios |
|---|---|
| `GET /` (graph mount + controls + recent list + `home.graph.shown`) | milestone-8 scenarios 1, 2, 6, 7, 8, 10, 11 |
| `POST /entries` (+`recent` field, D-19) | Saving repaints…; Today's save goes straight to the top |
| `GET /graph` (complete list + `trend.study.opened`, deep links) | all milestone-9 scenarios |
| `GET /trend` (emission retired → pure read) | An ambient morning… (adds 0); A graph hiccup… (no mark) |
| **`POST /telemetry/trend-study` (CREATE)** — status codes, closed vocabulary, gate | Choosing a lens or scale…; A garbled study signal…; A stranger's study signal… |
| `GET /stats` (new counters) | every `@kpi` scenario |
| `GET /static/graph.js` (new asset, shared engine) | The morning opens on the whole picture |

### [REF] Scaffolds

**Zero production scaffold files needed (Mandate 7 satisfied structurally):** acceptance tests reach the SUT exclusively over HTTP through the production composition root — no test imports any unbuilt production module, so no ImportError surface exists. The RED anchors are HTTP-observable absences, all classified `MISSING_FUNCTIONALITY` by the gate run: missing `#home-graph` mount, missing `#recent-entries` / `#history-entries` lists, beacon 404, `/stats` keys absent, save response `recent` absent. Test-side infrastructure added (import-clean, all steps defined — no BROKEN class): `steps/steps_home_graph.py`, `steps/steps_history_record.py`, four composition services (`HomeGraphService`, `RecentListService`, `HistoryRecordService`, `StudyService`), bindings `test_milestone_8.py` / `test_milestone_9.py`.

### [REF] Test Placement

`tests/weight-trend-tracker/acceptance/` — the project's single acceptance tree (milestone-N precedent, features 6–7 landed the same way; `pythonpath` pinned in `pyproject.toml`). New US markers `us_010/011/012` registered.

### [REF] Executable Contracts (DELIVER pre-requisites)

The oracles pin these shapes — the crafter implements TO them (executable spec):

- **Markup**: front-page graph mounts at `id="home-graph"` carrying `data-view`/`data-scale` (defaults `trend`/`3M`, A17 — mount sits before `<form>`); lens/scale controls reuse the `data-lens`/`data-window` button grammar; recent list = `<ul id="recent-entries">` of `<li>` rows; History complete list = `<ul id="history-entries">` after `id="chart"`. Row grammar everywhere: `Fri 24 Jul — 82.2 kg` (`%a d %b — X.X kg`, no leading zero, 0.1 precision).
- **Save response**: `recent` field = up-to-7 `{date, weight_kg}` newest first (D-19; `glance`/`confirmation` precedent).
- **`/stats` keys** (Q2 resolved — raw rolling-week counts over the same week frame as `trend_views_this_week`, no session collapse): `trend_study_this_week` (deliberate: `trend.study.opened` + `trend.study.interaction`), `home_graph_shown_this_week` (ambient). `trend_view_opened_count` stays frozen.
- **Beacon**: `POST /telemetry/trend-study` accepts `{surface: home|history, control: lens|scale, value: trend|raw|1W|1M|3M|6M|1Y|ALL}` → 2xx + exactly one `trend.study.interaction` append; anything else → 400, no trail write; unauthenticated → door (303/401).
- **Q3 oracle wording applied**: `home.graph.shown` asserted as data-available-at-render delivery (the hiccup scenario deliberately asserts the delivery fires even when the series read fails — entries existed at render).
- **Q4 applied**: entry-primacy property asserts exactly one `autofocus` (the weight field) and no `tabindex` anywhere.
- **A17 note for the crafter**: front page ignores `?view=`/`?scale=` (paramless defaults) — pinned at unit level in DELIVER (no AT scenario spends on it).
- **sw.js**: `graph.js` joins APP_SHELL + cache bump = DELIVER (Q5), covered by existing theme delivery ATs' pattern.

### [REF] Inherited-AT Renegotiations (never silent)

1. **G-5 script clause — amended NOW, green before and after** (Q1 closed): milestone-7 "The finished look costs almost nothing" clause `the morning screen carries no new moving parts` → `every moving part on the morning screen is the tracker's own`; assertion = exactly one inline script + `src` values ⊆ {`/static/uplot.iife.min.js`, `/static/graph.js`} (same-origin sanctioned set). Surviving intent intact: zero external origins, ≤10 KB theme, entry primacy. Recorded in `kpi-contracts.yaml` (G-5 note) and in the feature file header.
2. **milestone-6 deliberate-study scenario — amendment pinned for the DELIVER step that retires the `trend.view.opened` emission** (cannot be form-invariant: any redirect today would red a shipped AT): `GlanceService.study_trend` → History-page opens; `StatsService.assert_trend_views_this_week` → reads `trend_study_this_week`. Scenario wording unchanged; pin lives as a comment on the scenario itself and in `red-classification.md`. milestone-4's "Opening the trend counts toward engagement" is amended in the same step (same mechanism).

### [REF] RED Gate

`docs/feature/graph-first-home/distill/red-classification.md`: **18 RED (all `MISSING_FUNCTIONALITY`, AssertionError only) / 1 GREEN (preserved-behavior guard: empty-record front page) / 0 BROKEN.** First gate run caught two wrong-RED test bugs (step-ordering; JSON oracle vs HTML page) — fixed before classification. Full suite unchanged: 134 passed, 19 `@pending` skipped.

### [REF] Registered Outcomes

OUT-8 (operation: trend-study beacon, closed vocabulary) + OUT-9 (invariant: KPI-3 purity — ambient adds 0 by construction) in `docs/product/outcomes/registry.yaml`. Registered manually: `nwave-ai outcomes register` re-attempted 2026-07-24, still fails on the mis-packaged `schema.json` (documented tool defect, OUT-7 precedent).

### [REF] SSOT Updates

- `docs/product/kpi-contracts.yaml`: three new events (`home.graph.shown`, `trend.study.opened`, `trend.study.interaction`) + `trend.view.opened` emission-retirement note; KPI-3 redefined (instrument switch documented, Q2 rule pinned); KPI-7 added; `at_scenario_links` tightened (KPI-3, KPI-7, G-2 extension, G-5 amended clause).
- Mandate-12 evidence: (1) typed vocabulary reused from `domain_types.py` (TimeScale/ViewMode/parse_* — no new enums needed; row grammar = one `entry_row_text` function); (2) composition services consume typed parameters; (3) step bodies ≤2 statements, zero control flow, all logic in services; (4) step-reuse ratio (informational): 108 step invocations across the two feature files / 45 new decorator lines ≈ 2.4×, with heavy additional reuse of milestones 1–7 vocabulary (record/glance/views/access steps bound as-is) — journey-rich shape, natural ceiling consistent with prior features.

### [REF] Pre-Requisites for DELIVER

None blocking. Slice order stands (01 → 02; KPI-3 redefinition flips once). DELIVER owes: the ADR-009 inherited-AT redirect (see Renegotiations #2) in the same step as the emission retirement; `sw.js` cache bump (Q5); mutation gate ≥80% on modified files; outcome-delta re-check when the CLI is fixed upstream.

Platform-review conditions (Forge, conditionally approved — all DELIVER-scope, accepted as action items):

1. **sw.js cache-name bump verified before deploy** — explicit DoD check when `graph.js` joins APP_SHELL (calm-visual-theme precedent); a forgotten bump degrades to absent-graph on stale shells (acceptable but avoidable).
2. **/stats labels the KPI-3 instrument switch** — `trend_view_opened_count` marked frozen-historical (pre-2026-07-24) beside the live `trend_study_this_week`, so the weekly review can't misread the change.
3. **Beacon error handling = fire-and-forget** — a failed `append_event` inside the beacon is swallowed (structured log only); responses are only 2xx (accepted) or 400 (vocabulary), never 500. The garbled-signal AT already pins the never-500 half; the append-failure half is crafter guidance (D-14 precedent).

### [REF] Final Wave Review Gate

Four reviewers dispatched in parallel (Haiku), 2026-07-24: Eclipse (DISCUSS) **approved 0/0/0**; Architect (DESIGN) **approved 0/0/0, zero cross-wave contradictions**; Forge (platform) **conditionally approved 0 blocker / 0 high** — three conditions pinned above; Sentinel (DISTILL, never skipped) **approved 0 blocker / 0 high / 1 low** (stylistic note on the hiccup scenario's two When/Then pairs — intentional fault-journey shape, accepted). Deliverable-type routing: `application` → no plugin/skill reviewers (N/A). **Gate: PASSED — handoff to DELIVER unblocked.**

## Wave: DELIVER

### [REF] Demo Evidence

Post-merge integration gate 2026-07-24: full suite **165 passed / 0 skipped** (all 19 feature scenarios green, zero `@pending`; milestones 1–7 green incl. amended G-5 + redirected milestone-4/6 clauses). Elevator Pitch demos executed as a subprocess against the REAL production composition (`build_app` + real SQLite + real HTTP via TestClient), 135 seeded entries (3 Mar – 23 Jul 2026, vacation gap 10–17 Apr), device day Fri 24 Jul 2026:

- **US-010** — `/` renders `#home-graph` (`data-view="trend" data-scale="3M"`) above the form with the full `Trend|Raw` + `1W 1M 3M 6M 1Y ALL` control grammar; weight field autofocus + decimal keypad intact; save returns `Saved: 82.2 kg — Fri 24 Jul`.
- **US-011** — save response hands back `recent` with today on top; `/` shows the last-7 list: `Fri 24 Jul — 82.2 kg | Thu 23 Jul — 82.1 kg | Wed 22 Jul — 82.1 kg …`.
- **US-012** — `/graph` lists the complete record (136 rows, top `Fri 24 Jul — 82.2 kg`, bottom `Tue 3 Mar — 83.4 kg`) beneath the full-control graph; deep link `/graph?view=raw&scale=1Y` honored.
- **KPI purity** — log-only morning: `trend_study_this_week` unchanged by ambient renders; one History open moved it 2 → 3; `home_graph_shown_this_week` = 2 (ambient deliveries on the record).

Exit code 0; environment matrix N/A (no DEVOPS wave — brownfield, existing pipeline; clean environment run recorded).

### [REF] Implementation Summary

DELIVER wave executed 2026-07-24 by nw-deliver orchestrator + nw-functional-software-crafter (ADR-005 paradigm). Shipped US-010/011/012: the graph page's inline chart JS extracted into shared `web/static/graph.js` (ADR-008 — one code path renders both surfaces, lens/scale parity by construction; joins the sw.js APP_SHELL with the cache bumped to `-v3`); front-page graph mount with the full `Trend|Raw` + `1W…ALL` controls above the untouched entry form, last-7 recent list below it, and the `recent` field in the `POST /entries` response driving both in-place refreshes (D-18/D-19); `/graph` extended with the complete server-rendered record beneath the full-control chart (D-17); the intent-telemetry flip per ADR-009 — `trend.view.opened` emission retired (`GET /trend` now a pure read, historical rows preserved), replaced by ambient `home.graph.shown`, deliberate `trend.study.opened`, and the closed-vocabulary fire-and-forget beacon `POST /telemetry/trend-study` emitting `trend.study.interaction`, with `/stats` gaining `trend_study_this_week` + `home_graph_shown_this_week` beside the frozen-historical `trend_view_opened_count`. All logic landed as pure helpers in `routes.py`; zero port changes, zero new dependencies. 7 roadmap steps, all RED→GREEN→COMMIT through DES, plus a L1-L6 refactor pass.

### [REF] Files Modified

Production (6 files, diff `653e671..HEAD`): `src/weight_tracker/web/routes.py`; `src/weight_tracker/web/static/graph.js` (NEW — extraction); `src/weight_tracker/web/static/sw.js` (`graph.js` joins APP_SHELL, cache `-v3`); `src/weight_tracker/web/static/theme.css`; `src/weight_tracker/web/templates/index.html`; `src/weight_tracker/web/templates/graph.html`.
Tests: milestone-8/9 feature files (activated, zero `@pending`); 3 new property files (`properties/test_recent_list_properties.py`, `test_save_recent_properties.py`, `test_study_beacon_properties.py`); `steps/composition.py` extended; renegotiated/redirected clauses in `milestone-7-calm-visual-theme.feature` + `steps/steps_theme.py` (G-5) and `milestone-6-home-trend-glance.feature` (study redirect); plus DISTILL-authored `steps/steps_home_graph.py`, `steps/steps_history_record.py`, `steps/test_milestone_8.py` / `test_milestone_9.py` bindings (land with the finalize commit).
Docs: feature-delta.md (this file), `deliver/{roadmap,execution-log}.json`, `deliver/mutation/mutation-report.md`; SSOT — `brief.md` (Component Inventory), `kpi-contracts.yaml` (baselines); ADR-008/009 already permanent in `docs/product/architecture/`.

### [REF] Scenarios Green

**19 of 19 feature scenarios green** (13 milestone-8 + 6 milestone-9), zero `@pending` remaining. Full suite: **165 passed, 0 skipped, 0 failed**, 2026-07-24 — including the consciously amended G-5 clause and the redirected milestone-4/6 study clauses.

### [REF] DoD Check

| # | DoD item (DISCUSS) | Status |
|---|---|---|
| 1 | All UAT scenarios green (automated) | PASS — 19/19 (13 milestone-8 + 6 milestone-9) |
| 2 | Supporting tests green incl. the consciously amended G-5 clause | PASS — full suite 165 passed; amended G-5 + redirected milestone-4/6 clauses green (no silent breakage) |
| 3 | Code refactored; per-feature mutation gate ≥80% on modified files | PASS — L1-L6 pass done (commit `3971ec5`) + mutation 89.1% effective (≥80%) |
| 4 | Code reviewed | PASS — adversarial review APPROVED, 0 blockers |
| 5 | Merged to main | **PENDING USER ACTION** — all commits are on main locally (trunk-based); push owed |
| 6 | Deployed to the phone-reachable production URL | **PENDING USER ACTION** — existing pipeline runs on the push |
| 7 | Dogfooded same day (morning entry on the graph-first front page; History-page audit) | **PENDING USER ACTION** — follows the deploy |
| 8 | KPI-7 emitting; KPI-3 purity + KPI-1/≤2 s guardrails verified on /stats | **PENDING USER ACTION** (production) — instrumentation already verified live in the demo run (`home_graph_shown_this_week` 2; `trend_study_this_week` 2→3 on one History open, unchanged by ambient renders) |
| 9 | Story demonstrable end-to-end on the phone | **PENDING USER ACTION** — production-composition demo evidence above; on-phone demo follows the deploy |

### [REF] Quality Gates

| Phase | Outcome |
|---|---|
| Roadmap + review | Approved (1 review) — 19/19 scenarios mapped across 7 steps |
| Steps 01-01…02-02 | 7/7 COMMIT PASS via 3-phase TDD (`15bc1e6`, `5923768`, `766c6e6`, `8034639`, `416e232`, `b9be06a`, `c7fe18b`); DES: 21/21 events, integrity exit 0 |
| Post-merge integration | PASS — full suite 165 passed + production-composition Elevator Pitch demos (evidence above) |
| Refactor (L1-L6) | PASS — 4 L2 extractions over feature-modified files (`3971ec5`) |
| Adversarial review | APPROVED — 0 blockers |
| Mutation (per-feature, cosmic-ray) | PASS — 41/46 = **89.1% effective** (≥80%); 12 argued equivalents, 2 tolerated status-code constants, 3 genuine survivors routed to `nw-acceptance-designer` as AT-strength findings (beacon append-degrade containment; mixed-intent week for the KPI-3 sum) — see `deliver/mutation/mutation-report.md` |

### [REF] Pre-Requisites

Consumed: DISTILL's 19 scenarios + test-side scaffolds (composition services, step files, bindings — authoritative executable spec); DESIGN pins D-15–D-20 honored verbatim; ADR-008 + ADR-009 (ADR-001…007 unchanged). Forge platform-review conditions all discharged in-flight: **1** (sw.js cache-name bump with `graph.js` in APP_SHELL) DONE in 01-01 (`-v3`); **2** (/stats labels `trend_view_opened_count` frozen-historical beside the live counters) DONE in 01-02; **3** (beacon fire-and-forget — failed append swallowed with structured log, 2xx/400 never 500) DONE in 01-03. Q5's outcome-registry re-check (`nwave-ai outcomes check-delta`) remains blocked by the upstream CLI defect (mis-packaged schema.json, OUT-7 precedent) — OUT-8/OUT-9 registered manually at DISTILL; re-check via CLI when fixed upstream.
