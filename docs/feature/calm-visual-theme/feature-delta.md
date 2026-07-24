<!-- markdownlint-disable MD024 -->
# Feature Delta: calm-visual-theme

## Wave: DISCUSS

### [REF] Persona ID

`clemens` — see `docs/product/personas/clemens.yaml`. Sole customer, sole user, sole developer. Phone-first, half-awake at 06:45, often in a dim bathroom. Unchanged from prior features.

### [REF] JTBD One-Liner

Job `track-true-weight-trend` (`docs/product/jobs.yaml`, validated). This feature serves the job's **emotional dimension** ("satisfaction of owning a tool that does exactly one thing well") at every moment of use. New job-story moment `js-5-quality` appended to `jobs.yaml` (2026-07-23): *When I open the tracker every morning of the year, I want a calm, deliberately designed screen — legible in the dim bathroom — instead of default browser HTML, so the daily habit feels like using a finished product and I can cancel the old subscription without hesitation.* Same job, new moment — no JTBD re-run.

### [REF] Locked Decisions

- **D1** Feature type: user-facing (presentation layer only; zero behavior change).
- **D2** Walking skeleton: NO — brownfield; full vertical exists; this feature rides it.
- **D3** UX research depth: lightweight — journey delta only, single persona.
- **D4** JTBD: bridge to existing validated job via new moment `js-5-quality`.
- **D5** Density: mode=lean, expansion_prompt=ask-intelligent — triggers evaluated, **none fired**, silent-lean.
- **D6** Visual direction: **calm minimal** (user, 2026-07-23) — quiet, spacious, typographic; matches persona value "single-purpose minimalism". Not native-app card chrome, not dashboard, not playful.
- **D7** Color scheme: **follow system** (`prefers-color-scheme`) — both light and dark fully styled; the 06:45 dim-bathroom case is expected to land on dark automatically.
- **D8** Scope: all three screens — entry (`index.html`), graph (`graph.html`), door (`door.html`).
- **D9** Build approach: no preference expressed — hand-written CSS vs classless framework is a **DESIGN-wave decision**. Requirement-level pins regardless of choice: no CDN/network dependency, no web-font downloads (system font stack), total CSS ≤ 10 KB uncompressed.

### [REF] Scope Assessment

**PASS — 2 stories, 1 bounded context (web presentation), estimated ~1–2 days total.** Oversized signals: stories 2/10, contexts 1/3, skeleton integration points 0 (no new ports), effort ≪ 2 weeks, one user outcome (the tool looks/feels finished). Zero of five signals fired.

### [REF] Journey Summary

SSOT: `docs/product/journeys/daily-weight-tracking.yaml` — **presentation delta only; no step, flow, or artifact changes.** All four steps keep their actions, shared artifacts, and integration checkpoints verbatim. Deltas recorded:

- Step 1 failure mode added: *bright light-theme screen in a dark bathroom at 06:45* (must follow system scheme).
- Step 2/3 failure mode added: *chart axes, gridlines, or series strokes illegible in dark scheme*.
- Emotional delta: the arc's start ("zero cognitive load tolerated") is **protected**, not changed — styling must not add friction; exit gains "the tool feels made on purpose".
- Changelog entry dated 2026-07-23.

### [REF] Story Map

Extends the existing map. Styling is a **cross-cutting quality of the existing activities** — no new activity column; recorded as a polish row.

| Capture weight | Review history | Judge trend | Maintain record |
|---|---|---|---|
| US-001, US-006, US-007 ✅ | US-001, US-002 ✅ | US-004, US-005 ✅ | US-003 ✅ |
| **Calm theme: entry + door (US-008)** | **Calm theme: graph (US-009)** | **(US-009 covers trend lens)** | *(edit uses entry screen — US-008)* |

**Slices** (elephant carpaccio, each ≤ 1 day, each dogfooded the same day):

- **Slice 01** — `slices/slice-01-calm-entry-theme.md`: shared theme + entry & door screens, light + dark. (US-008)
- **Slice 02** — `slices/slice-02-graph-theme.md`: graph screen controls + chart theming, light + dark. (US-009)

Taste tests: no slice ships 4+ components; no new abstraction (shared stylesheet is slice 01's deliverable, slice 02 consumes it — abstraction ships first); slice 01 disproves the "follow-system is enough at 06:45" pre-commitment if it fails; both slices dogfood on production data (real morning logs); slices are not scale-duplicates. **All pass.**

### [REF] Priority Rationale

Slice 01 first: highest-frequency screen (365 mornings/year), carries the dark-mode learning hypothesis, and ships the shared stylesheet slice 02 depends on. Slice 02 second: dependency + lower frequency (KPI-3 target is 3 visits/week). Door rides slice 01 because it is the same form idiom sharing the same rules — a separate door slice would be a scale-duplicate (taste test 5).

### [REF] Requirements & Constraints

- **Zero behavior change**: DOM ids, form semantics, fetch flow, telemetry events, and all existing acceptance tests stay untouched and green. Styling is additive (stylesheet + class/markup-neutral hooks); `#trend-glance`, `#save-feedback`, `aria-pressed` contracts preserved.
- **Entry-speed guardrail (KPI-1)**: entry screen interactive ≤ 2 s on phone; autofocus + decimal keypad preserved; **no new JavaScript on the entry screen**. Slice 02 may add minimal JS only for scheme-reactive chart colors (`matchMedia`).
- **Self-contained assets**: no CDN, no web fonts, no network dependency (system font stack). Total added CSS ≤ 10 KB uncompressed. App must remain fully usable when the stylesheet fails to load (progressive enhancement).
- **Both schemes are first-class**: light and dark via `prefers-color-scheme`; every text ≥ 4.5:1 contrast (WCAG AA), non-text UI (button borders, chart strokes, gridlines) ≥ 3:1, in **both** schemes.
- **Touch targets** ≥ 44 px (already pinned on door; now uniform everywhere).
- **Selected state beyond color**: graph scale/lens buttons must show the pressed state through more than color alone (weight/border/fill), in both schemes.
- **Neutral tone**: direction glyphs and trend data stay judgment-free — no red/green good/bad coloring (persona: information, not alarm).

### [REF] User Stories

Both stories: `job_id: track-true-weight-trend` (moment `js-5-quality`). Persona: Clemens.

#### US-008: The 06:45 screen is calm, dark when the bathroom is, and deliberately made

`job_id: track-true-weight-trend` · Slice 01 · Must · ~0.5–1 day

##### Problem

The entry and door screens are default browser HTML: Times-ish serif on white, unstyled inputs, a bare Save button. At 06:45 in a dim bathroom the white page is a small flashbang, and every morning the tool he built to replace a $30/month product greets him looking like a prototype.

##### Elevator Pitch

- **Before**: Opens `/` at 06:45 — bright white default-HTML page, unstyled form, browser-default button.
- **After**: opens `/` on a phone whose system is in dark mode → sees a dark, calm, typographic screen: generous spacing, a large legible weight field, a clearly tappable Save, the glance line quietly prominent — same content, same speed. `/login` matches.
- **Decision enabled**: "Is this tool finished enough to be the permanent replacement?" — the daily impression now supports cancelling the old subscription (KPI-4) without the nagging "my thing still looks half-done".

##### Domain Examples

1. *Dark morning*: phone in system dark at 06:45 → `/` renders dark background, light text, all contrast AA; types 82.4, saves — flow identical to today.
2. *Light afternoon correction*: phone in light mode → same layout in the light palette; nothing about the flow differs between schemes.
3. *Stylesheet lost*: CSS fails to load → the form still works end-to-end (plain but functional).
4. *Door*: session expired → `/login` shows the same theme; passphrase field and Unlock button styled to the same rules.

##### UAT Scenarios (BDD)

###### Scenario: A dark bathroom gets a dark screen

- **Given** Clemens's phone reports the dark color scheme at 06:45
- **When** he opens the tracker's entry screen
- **Then** the page renders with a dark background and light text, every text element at ≥ 4.5:1 contrast
- **And** the weight field is focused with the decimal keypad, interactive within 2 seconds, exactly as before

###### Scenario: Light mode is equally deliberate

- **Given** Clemens's phone reports the light color scheme
- **When** he opens the entry screen
- **Then** the same layout renders in the light palette at the same contrast standard

###### Scenario: Styling never taxes the entry

- **Given** the themed entry screen
- **When** Clemens logs a weight the way he always has
- **Then** the save confirmation, glance refresh, and rejection flows behave byte-for-byte as before
- **And** no additional JavaScript executes on the entry screen and no network request leaves the app's own origin

###### Scenario: The door wears the same clothes

- **Given** Clemens is logged out with the dark scheme active
- **When** he opens any page and lands on the door
- **Then** the passphrase screen renders in the same theme with ≥ 44 px touch targets

#### US-009: The graph reads clearly in any light

`job_id: track-true-weight-trend` · Slice 02 · Must · ~0.5–1 day

##### Problem

The graph page has minimal ad-hoc CSS: underlined-bold pressed buttons, default uPlot colors tuned for white backgrounds. In dark mode (post-US-008 theme) the chart would sit as a white-ish island with near-invisible axis text; the pressed state is easy to miss at a glance.

##### Elevator Pitch

- **Before**: Opens `/graph` — plain buttons where the selected scale is just underlined, chart hard-coded to light colors.
- **After**: opens `/graph` in dark mode → sees themed Trend/Raw and scale buttons with an unmistakable pressed state, and a chart whose axes, gridlines, and series strokes are legible on the dark background; light mode equally tuned.
- **Decision enabled**: the noise-vs-signal verdict (`js-2-judge`) is readable in evening/dim conditions, not just daylight — trend judging stops being a daytime-only activity.

##### UAT Scenarios (BDD)

###### Scenario: The chart is legible in the dark

- **Given** Clemens has 45 entries and his phone reports the dark scheme
- **When** he opens the graph and views both the Trend and Raw lenses
- **Then** axis labels meet ≥ 4.5:1 and gridlines/series strokes ≥ 3:1 contrast against the dark background
- **And** gaps in the raw series still render as gaps

###### Scenario: The selected scale is obvious beyond color

- **Given** the graph page in either scheme
- **When** the "3M" scale is active
- **Then** the 3M button is distinguishable from its neighbors by shape/weight/fill, not color alone, and `aria-pressed` semantics are unchanged

###### Scenario: Scheme flips mid-session are honored

- **Given** the graph is open in light mode
- **When** the system switches to dark mode
- **Then** the page and the rendered chart adopt the dark palette without losing the selected lens and time scale

### [REF] Outcome KPIs

| ID | Name | Target | Instrument |
|---|---|---|---|
| KPI-6 | finished-feel | Self-reported ≥ 4/5 after 7 dogfood mornings; recorded in iteration notes | Manual (persona `measurement_note`: single-user, self-reported) |
| G-KPI-1 | entry-speed unchanged | 7-day median entry_ms ≤ 5000 post-ship (no regression vs pre-ship window) | Existing `entries.entry_ms` / `/stats` (KPI-1 contract) |
| G-4 (new) | contrast-AA both schemes | 0 violations: text ≥ 4.5:1, non-text ≥ 3:1, light + dark | Acceptance-level check (mechanism = DISTILL; manual audit acceptable fallback) |
| G-5 (new) | asset budget | Added CSS ≤ 10 KB uncompressed; 0 external requests; 0 new entry-screen JS | Byte count + request log in AT |

No new events table entries; KPI-6 is manual per the single-user measurement note.

### [REF] Out of Scope

- Logo, branding, app icon redesign; manifest theme colors may be touched only to match the palette.
- Animations/transitions beyond trivial (e.g. button press feedback); no micro-delight system.
- Web fonts or icon fonts (system stack only).
- Layout restructuring, new screens, navigation changes, `/stats` presentation.
- Manual theme toggle (system-follow only; a toggle is a future feature if the D7 hypothesis fails).
- Historical-data import, and everything else not named.

### [REF] WS Strategy

N/A — walking skeleton exists (delivered `weight-trend-tracker`, 2026-07-23). Strategy A: extend the existing vertical. No new ports, no new adapters; one static asset joins the existing `/static` mount.

### [REF] Driving Ports

Unchanged: `GET /` (entry), `GET /graph`, `GET /login` + door POST. New driven surface: none (static stylesheet served by the existing StaticFiles mount). Read-only ports untouched (ADR-005 guard holds trivially — no domain code in scope).

### [REF] Pre-requisites

- `home-trend-display` delivered (glance line is part of the entry screen being styled) — ✅ done 2026-07-23.
- No other dependencies. Domain core untouched; mutation-testing scope expected ~nil (templates/CSS), confirm at DELIVER.

### [REF] Definition of Done

1. Both slices shipped to production and dogfooded ≥ 1 real morning each.
2. All pre-existing acceptance tests green, unmodified.
3. New ATs for US-008/US-009 scheme scenarios green.
4. Contrast audit clean in both schemes (G-4).
5. Asset budget respected (G-5).
6. KPI-1 7-day median shows no regression (G-KPI-1).
7. SSOT updated (jobs, journey, persona) — done at DISCUSS, verified at finalize.
8. Feature archived via nw-finalize after completion.
9. KPI-6 self-report recorded after 7 mornings.

### [REF] DoR Validation

1. ✓ Value articulated — elevator pitches with decision-enabled lines (US-008: cancel-with-confidence; US-009: any-light judging).
2. ✓ Job traceability — both stories `job_id: track-true-weight-trend`, moment `js-5-quality` added to `jobs.yaml`.
3. ✓ ACs testable — contrast ratios, byte budgets, request counts, scheme emulation, unchanged-behavior assertions; no "looks nice" criteria.
4. ✓ Sized — 2 slices, each ≤ 1 day, briefs in `slices/`.
5. ✓ Dependencies — slice 02 depends on slice 01's stylesheet; nothing external.
6. ✓ Out-of-scope explicit — section above.
7. ✓ KPIs measurable — table with numeric targets and instruments.
8. ✓ SSOT updated — jobs.yaml (js-5-quality), journey changelog + failure modes, persona.
9. ✓ Journey coherence — no flow changes; emotional arc protected (zero-friction start) and extended (finished-feel exit).

Requirements completeness: 2 stories × (problem, pitch, examples/scenarios, ACs, KPIs, out-of-scope) — no known open questions; score ≈ 0.97 (residual: exact palette values and CSS mechanism are deliberately deferred to DESIGN per D9).

### [REF] Wave Decisions Summary

- [D6] Calm minimal direction: matches "single-purpose minimalism" persona value (user-locked).
- [D7] Follow-system color scheme: dim-bathroom 06:45 case; hypothesis explicitly falsifiable via slice 01 dogfood — if mornings still land bright, revisit as dark-only or manual toggle.
- [D8] All three screens: door included with entry (same form idiom) to avoid a scale-duplicate slice.
- [D9] CSS mechanism deferred to DESIGN; requirement-level pins: ≤ 10 KB, zero external requests, zero entry-screen JS, progressive enhancement.

**Upstream changes**: none — no DISCOVER/DIVERGE artifacts exist; SSOT extended, not contradicted.

**Density record**: lean + ask-intelligent; triggers evaluated (AC ambiguity, cross-context, multi-stakeholder, compliance, WS-D) — none fired → silent lean. Telemetry `DocumentationDensityEvent(choice=skip, expansion_id=*)` **not emitted**: `scripts/shared/telemetry.py` helper not present in this repository; recorded here in lieu of the event.

## Wave: DESIGN

Scope: application (user, 2026-07-23) → nw-solution-architect (Morgan), propose mode. Proposal authored by Morgan; finalization transcribed by the orchestrator after the subagent was twice interrupted by API server errors (content unchanged). SSOT integration: `brief.md` Web UI row + theming paragraph, `adr-007-theming-mechanism.md`.

### [REF] DDD List

- **DDD-1** D9 resolved: hand-written design-token stylesheet `web/static/theme.css`, ~4.7 KB est. (ceiling ~6 KB) vs ≤ 10 KB budget — **accepted** (user, after byte-arithmetic comparison). Pico.css classless ~70–80 KB (7–8× over) and Simple.css ~12–13.5 KB with overrides (over budget) — rejected.
- **DDD-2** Structure convention: **CUBE-lite adopted** (user-requested CUBE CSS evaluation). Layers: Tokens → Global → Composition (one flow primitive) → Utility (*deliberately empty*) → Block (element/id-keyed, zero new classes) → Exception (`aria-pressed`/`hidden` attribute states — CUBE's own exception mechanism). Byte impact ≈ 0; no template class churn.
- **DDD-3** uPlot theming: tokens as single source; `renderChart` reads `--chart-*` via `getComputedStyle`; one `matchMedia` change listener re-renders through existing `showGraph` (lens + scale preserved). ~8 lines JS, graph page only. Pure-CSS chart theming rejected (canvas unreachable; fails mid-session flip).
- **DDD-4** Token set: light `#FAFAF8`/`#1A1A1A`, dark `#14161A`/`#E8E6E3`; full palette + contrast arithmetic in § Design Tokens below (G-4 contract). Neutral tone held — no red/green judgment colors; pressed state = fill + weight, not color alone.
- **DDD-5** PWA alignment: manifest colors → `#FAFAF8`/`#1A1A1A`; `theme.css` appended to `sw.js` APP_SHELL (cache-name bump = DELIVER).
- **DDD-6** No new ports/adapters/containers; no C4 changes; ADR-005 untouched (no domain code in scope).

### [REF] Component Decomposition

| Component | Path | Change |
|---|---|---|
| Theme stylesheet | `src/weight_tracker/web/static/theme.css` | **CREATE NEW** (only new artifact; served by existing static route, zero shell-code change) |
| Entry template | `src/weight_tracker/web/templates/index.html` | EDIT: add `<link>` to theme.css; zero JS change |
| Graph template | `src/weight_tracker/web/templates/graph.html` | EDIT: add `<link>`, delete inline `<style>` (migrated), replace hard-coded `#1f6feb`/`#d29922` with token reads + matchMedia listener |
| Door template | `src/weight_tracker/web/templates/door.html` | EDIT: add `<link>`, delete inline `<style>` (44 px rule goes global) |
| Service worker | `src/weight_tracker/web/static/sw.js` | EDIT: append `/static/theme.css` to APP_SHELL |
| PWA manifest | `src/weight_tracker/web/routes.py` (`PWA_MANIFEST`) | EDIT: two color fields aligned to palette |
| Vendored uPlot | `src/weight_tracker/web/static/uplot.*` | UNCHANGED (byte-identical; theming via opts + page CSS only) |

### [REF] Driving Ports

**Unchanged — explicitly.** `GET /`, `POST /entries`, `GET /graph`, `GET /login` + door POST, `GET /static/{asset_name}`: same routes, same JSON/HTML contracts, same DOM ids, same `aria-pressed` semantics. Existing ATs must stay green unmodified.

### [REF] Driven Ports + Adapters

**None new — explicitly.** No I/O, no state, no clock, no storage touched. `theme.css` is a pure static asset (empty mutation universe); no startup probe applies. Fault injection instead: stylesheet-loss AC (app usable unstyled) and `matchMedia`-absent degradation (chart colors fixed at load-time scheme; page CSS still flips).

### [REF] Technology Choices

**Zero new dependencies.** CSS custom properties, `prefers-color-scheme`, `matchMedia` — all platform-native, evergreen-mobile-safe. System font stack (no downloads). No build step, no preprocessor, no vendored framework.

### [REF] Decisions Table

| ID | Decision |
|---|---|
| DDD-1 | theme.css hand-written token stylesheet; frameworks rejected on byte arithmetic |
| DDD-2 | CUBE-lite layer convention; Utility layer empty; Exceptions via aria attributes |
| DDD-3 | Chart colors from tokens via getComputedStyle + matchMedia re-render through showGraph |
| DDD-4 | Palette pinned with hand-computed AA ratios (table below = DISTILL G-4 contract) |
| DDD-5 | Manifest colors aligned; theme.css into APP_SHELL |
| DDD-6 | No port/adapter/container/C4/paradigm changes |

### [REF] Reuse Analysis

| Existing component | File | Overlap | Decision | Justification |
|---|---|---|---|---|
| Entry template | `web/templates/index.html` | Gets themed | EXTEND | One `<link>` tag; ids `#trend-glance`/`#save-feedback`/`#yesterday-reference` are the styling hooks as-is; zero new JS (D-9 pin) |
| Graph inline `<style>` | `web/templates/graph.html` | 6 lines duplicate theme concerns | EXTEND (migrate & delete) | Fold `#scale-picker`/`#view-toggle` rules into theme.css; underline/bold pressed style superseded by fill treatment |
| Graph chart JS | `web/templates/graph.html` | Hard-coded stroke hexes must theme | EXTEND | Token reads + one matchMedia listener calling existing `showGraph` — reuses render path, preserves lens/scale state |
| Door inline `<style>` | `web/templates/door.html` | 44 px rule goes global | EXTEND (migrate & delete) | Promote to global rule (uniform touch targets requirement) |
| Static route | `web/routes.py` `GET /static/{asset_name}` | Serves new asset | EXTEND (as-is, zero code) | New file in `web/static/` served automatically |
| Service worker | `web/static/sw.js` | New asset joins app shell | EXTEND | Append to APP_SHELL; cache bump = DELIVER |
| PWA manifest | `web/routes.py` `PWA_MANIFEST` | Colors must match palette | EXTEND | Bounded to two color fields; explicitly carved into scope at DISCUSS |
| Vendored uPlot | `web/static/uplot.*` | Chart look | EXTEND (do not patch) | Theming via opts + page CSS; vendor files byte-identical |
| Theme stylesheet | `web/static/theme.css` | n/a | **CREATE NEW** | Only new artifact; no existing stylesheet exists beyond vendored uplot.min.css (grep-confirmed) |

### [REF] Design Tokens (G-4 contract)

Font: `system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`; base 16 px / 1.5; weight input 1.5 rem; glance 1.125 rem. Spacing `--space-1..5` = 0.25/0.5/1/1.5/2.5 rem; global `input, button { min-height: 44px }`.

| Token | Light | vs light bg | Dark | vs dark bg | Req |
|---|---|---|---|---|---|
| `--bg` | `#FAFAF8` | — | `#14161A` | — | — |
| `--text` | `#1A1A1A` | 16.6:1 | `#E8E6E3` | 14.5:1 | ≥4.5 |
| `--text-muted` | `#555555` | 7.1:1 | `#A5A29C` | 7.1:1 | ≥4.5 |
| `--border` | `#767676` | 4.3:1 | `#6B6F76` | 3.6:1 | ≥3 |
| `--link` | `#1F5C99` | 6.6:1 | `#7FB0E8` | 8.0:1 | ≥4.5 |
| `--btn-bg`/`--btn-text` | `#1A1A1A`/`#FAFAF8` | 16.6:1 | `#E8E6E3`/`#14161A` | 14.5:1 | ≥4.5 |
| `--chart-axis` | `#444444` | 9.3:1 | `#A5A29C` | 7.1:1 | ≥4.5 |
| `--chart-grid` | `#8A8A8A` | 3.3:1 (tightest) | `#6B6F76` | 3.6:1 | ≥3 |
| `--chart-raw` | `#2E5E9E` | 5.6:1 | `#6FA8DC` | 7.2:1 | ≥3 |
| `--chart-trend` | `#8F5B00` | 5.5:1 | `#D9A441` | 8.0:1 | ≥3 |

Ratios hand-computed (WCAG relative luminance); DISTILL's checker is authoritative — any flagged pair shifts one hex step.

### [REF] C4 Note

**No diagram changes.** L1/L2 in `brief.md` remain accurate; the stylesheet lives inside the existing "Browser / PWA shell" container. No L3 (< 5 components per container).

### [REF] Open Questions (deferred)

| # | Question | Owner |
|---|---|---|
| Q1 | G-4 mechanical instrument: computed-style contrast arithmetic in ATs vs axe-core vs manual audit | DISTILL |
| Q2 | Gridline strictness: 3:1 default; may reclassify decorative (WCAG 1.4.11) if dogfood finds it heavy | DISTILL/DELIVER |
| Q3 | `sw.js` cache-name bump strategy when APP_SHELL grows | DELIVER |
| Q4 | Per-scheme `<meta name="theme-color">` + manifest `background_color` single-value choice | DELIVER |
| Q5 | Micro-typography taste (input size, h1 letter-spacing) | DELIVER dogfood (KPI-6) |
| Q6 | Hex nudges if DISTILL checker disagrees with hand arithmetic (tightest: light `--chart-grid` ~3.3:1) | DISTILL |

## Wave: DISTILL

Authored 2026-07-23 (Quinn, nw-acceptance-designer). Scenario SSOT: `tests/weight-trend-tracker/acceptance/milestone-7-calm-visual-theme.feature` (11 scenarios). Reconciliation: DISCUSS vs DESIGN — **0 contradictions** (DDD-3's graph-only JS is explicitly permitted by DISCUSS; the entry-screen zero-JS pin is AT-asserted). DEVOPS wave section absent — warned, project-default infra applied (policy inherit). Q1 + Q6 resolved as directed: the WCAG relative-luminance checker in the ATs (pure Python, `domain_types.py`) is the authoritative G-4 instrument, pinned to required **ratios**, never hex values — one-hex-step nudges stay green.

### [REF] Scenario list

| # | Scenario | Tags | Shape |
|---|---|---|---|
| 1 | The calm look arrives with the morning screen | @walking_skeleton @driving_port @driving_adapter @real-io @US-008 | pure-function |
| 2 | The new clothes never slow the morning down | @pending @driving_port @property @US-008 | pure-function |
| 3 | A save lands exactly as it always has | @pending @driving_port @US-008 | bounded-change |
| 4 | A rejected save is turned away exactly as before | @pending @driving_port @error @US-008 | unbounded-preservation |
| 5 | The door wears the same clothes | @pending @driving_port @US-008 | pure-function |
| 6 | A wrong passphrase is refused as plainly as ever at the themed door | @pending @driving_port @error @US-008 | unbounded-preservation |
| 7 | The graph dresses from the same palette | @pending @driving_port @US-009 | pure-function |
| 8 | Ink and surface keep their contrast promise in any light | @pending @driving_port @kpi @US-008 @US-009 | pure-function |
| 9 | Dim light is never served the daylight palette by accident | @pending @driving_port @error @US-008 | pure-function |
| 10 | The finished look costs almost nothing | @pending @driving_port @kpi @US-008 @US-009 | pure-function |
| 11 | A missing theme never blocks the morning weigh-in | @pending @driving_port @error @US-008 | bounded-change |

Error/edge share: 4 @error + 2 guardrail-boundary (8, 10) = 6/11 ≈ 55% error+edge (strict @error alone = 36% — honest shortfall vs the 40% target, accepted: presentation-only feature, zero new behavior; behavioral error paths are inherited from milestones 1–6, which must stay green unmodified per DoD-2).

### [REF] WS strategy

Architecture-of-Reference inherit (`docs/architecture/atdd-infrastructure-policy.md`, `--policy=inherit`): TestClient over production `build_app`, real SQLite on tmp_path, FakeClock — no policy rows added (no new ports).

### [REF] Adapter coverage (Mandate 6)

| Adapter | @real-io scenario | Covered by |
|---|---|---|
| *(none new)* | — | No new driven adapters (DESIGN DDD-6). The theme is a static asset served by the EXISTING `GET /static/{asset_name}` driving surface, exercised with real FS I/O by WS scenario 1 (`@driving_adapter @real-io`). |

### [REF] Scaffolds (Mandate 7)

**None needed.** Zero new Python production modules (the only new artifact is `theme.css`, DELIVER-owned). Absence of `theme.css` is itself the RED signal: the theme fetch runs through a tolerant client (`raise_server_exceptions=False`), so the missing file surfaces as a non-200 status failing the 200-assertion — **AssertionError = RED, never a raised RuntimeError/ImportError = BROKEN**. All step imports resolve without the asset existing (verified: full suite collects and runs).

### [REF] Test placement

Project precedent (home-trend-display → milestone-6 in the same tree): `tests/weight-trend-tracker/acceptance/milestone-7-calm-visual-theme.feature` + `steps/steps_theme.py` + `steps/test_milestone_7.py` (bindings mirroring `test_milestone_6.py`). `domain_types.py` extended (ColorScheme, ContrastClass, ColorPairing, Screen, CONTRAST_CONTRACT, WCAG luminance/contrast + scheme-token parsing — pure functions); `composition.py` gains `ThemeService` (Mandate-12: all logic in composition services).

### [REF] Driving adapter coverage

| Entry point | Exercised by |
|---|---|
| `GET /` (entry screen) | Scenarios 1, 2, 3, 4, 11 |
| `GET /` while locked (the door — **no `GET /login` route exists**; the access middleware answers any locked HTML navigation with the door page, and `/login` is POST-only) | Scenarios 5, 6 |
| `POST /login` | Scenario 6 (wrong passphrase) + every unlocked scenario's login |
| `GET /graph` | Scenario 7 |
| `GET /static/theme.css` | Scenarios 1, 8, 9, 10 (and 5's touch-target probe); 11 exercises its ABSENCE |
| `POST /entries` | Scenarios 3, 4, 11 |

### [REF] Pre-requisites

DESIGN driving ports unchanged (explicit DDD list); `home-trend-display` delivered (glance steps reused verbatim). DEVOPS delta: none for this feature (existing CI runs the acceptance tree).

### [REF] RED classification (fail-for-the-right-reason gate, RED_GATE_ALL=1)

All 11 scenarios FAIL with `AssertionError` = **MISSING_FUNCTIONALITY (genuine RED)**; zero IMPORT_ERROR / FIXTURE_BROKEN. `test_milestone_6.py` re-run: 17 passed (nothing broken).

| # | Failing assertion (one-liner) |
|---|---|
| 1–4, 11 | "the entry screen must wear the calm theme … but its page carries none" |
| 5, 6 | "the door must wear the calm theme … carries none" |
| 7 | "the graph page must wear the calm theme … carries none" |
| 8, 9, 10 | "the calm theme must be delivered by the tracker itself at /static/theme.css, got 500" |

Default (non-gate) run: 1 failed (WS enabled), 10 skipped `@pending` — one-scenario-at-a-time discipline intact.

### [REF] Step-reuse ratio (informational, Mandate-12 criterion 4)

63 step invocations in the feature / 18 new step decorators in `steps_theme.py` = **3.50×** natural ceiling; ~24 of the 63 invocations reuse milestones-1–6 vocabulary at zero new decorators (record, access, glance, views). All four mechanical criteria met: typed vocabulary in `domain_types.py`; `ThemeService` signatures consume `Screen`/`ContrastClass` enums; every step body ≤2 statements ending in a `composition.<service>.<method>(...)` call, zero control flow; ratio documented here, not gated.

### [REF] Completeness audit (nw-at-completeness-check)

14/15 passing → **COMPLETE** (≥13). Passing with rationale: C2a/C2b (theme delivery is stateless; DRESSED/BARE degradation modeled, inherited machines documented in `steps_theme.py` docstring), C4a/C4b + C7b/C7c (no new mutating op, single-user by claim — N/A with rationale), C5a/C5b (scheme = the mode flag; both exercised + flow-invariance asserted), C6a/C6b (rejected input on themed screen; missing-asset contract), C7a (asset-missing = degraded resource). Partial: C6c relies on the inherited closed rejection set (milestone-1 scenarios) rather than a new AT — counted as the 1 gapless-but-inherited item. Zero SPECIFICATION_AMBIGUITY findings.

### [REF] DELIVER dogfood note (TestClient limitation)

US-009 "Scheme flips mid-session are honored" is **not HTTP-drivable** (no browser, no `matchMedia` in TestClient). Covered structurally by scenarios 7–9 (single-source palette: no hard-coded colors in the graph page; both appearances in the one asset) — the live flip (open graph, toggle OS dark mode, chart re-renders keeping lens+scale) is a mandatory **DELIVER dogfood verification** before DoD sign-off. Q2 (gridline strictness) stays at 3:1 in the checker; relaxing to decorative requires editing `CONTRAST_CONTRACT` with a wave-decision note.

### [REF] Final Wave Review Gate (2026-07-23)

| Reviewer | Wave | Verdict |
|---|---|---|
| Eclipse (`nw-product-owner-reviewer`) | DISCUSS | **approved** — 0 findings; DoR 9/9 re-verified |
| Architect (`nw-solution-architect-reviewer`) | DESIGN | **approved** — 0 findings; contrast arithmetic spot-checked, single CREATE NEW justified |
| Forge (`nw-platform-architect-reviewer`) | DEVOPS (skip audit) | **conditionally approved** — skip justified; conditions below |
| Sentinel (`nw-acceptance-designer-reviewer`) | DISTILL | **conditionally approved** — 1 high (scenario 9 missing `@kpi` tag) — **FIXED** same session |

**DELIVER handoff conditions (from Forge — binding, in DELIVER scope):**

1. **Service-worker cache coordination (critical)** — Slice 01 DoD: in the SAME commit, (a) append `/static/theme.css` to the `APP_SHELL` array in `sw.js`, (b) bump `SHELL_CACHE` `weight-tracker-shell-v1` → `-v2`, (c) dogfood-verify post-deploy that theme.css loads on first visit and the old cache is evicted. Shipping the asset without the bump strands stale clients.
2. **Ownership** — condition 1 is part of Slice 01 (`slice-01-calm-entry-theme.md` scope: sw.js edit was already listed in the DESIGN decomposition); the crafter executes it, this note is the checklist.
3. **Optional (accepted as future item, not blocking)** — synthetic availability check for `/static/theme.css` (e.g. `/healthz` extension or external monitor URL). Deferred: single-user app; unstyled degradation is functional by design and AT-asserted.

## Wave: DELIVER

### [REF] Demo Evidence (Phase 3.5 gate, 2026-07-24)

Live production-composition server (`uvicorn weight_tracker.main:app`, real env contract: `PASSPHRASE_HASH`, `SESSION_SIGNING_KEY`, `DB_PATH`), driven by curl:

- **US-008 door**: locked `GET /` with `Accept: text/html` → door page carries `href="/static/theme.css"` + "Unlock your record".
- **US-008 entry**: after real `POST /login` → `GET /` carries the theme link with `autofocus` and `inputmode="decimal"` intact (zero-friction pin held).
- **Theme asset**: `GET /static/theme.css` → 200, **3,394 bytes** (G-5: ≤ 10,240), 66 custom-property lines, `prefers-color-scheme: dark` block present.
- **US-009 graph**: `GET /graph` carries the theme link + `matchMedia` scheme wiring; zero hard-coded hexes (`#1f6feb`/`#d29922` absent from the page).
- **Save flow invariant**: `POST /entries` → `{"outcome":"saved","confirmation":"Saved: 82.4 kg — Thu 23 Jul", …, "glance":"Trend: 82.4 kg"}`.

Full suite at gate: **123 passed, 0 skipped** (all 11 milestone-7 scenarios live). CI + production environments deferred to the existing push-to-main pipeline.

### [REF] Finalize record (2026-07-23)

| Gate | Outcome |
|---|---|
| Roadmap review | Approved — 11/11 scenarios / 4 steps, 0 orphans, avg 9.38/10, mandates 3/3 |
| Per-step TDD | 4/4 RED→GREEN→COMMIT PASS (`f8d8f4f`, `8053a4b`, `1602f57`, `4cafaf7`); DES integrity exit 0 |
| Post-merge gate (3.5) | PASS — full suite 123/0 + live-server demo (evidence above) |
| Phase 3 refactor | Empty scope — CSS/template/manifest data only; no Python refactor warranted |
| Adversarial review (Phase 4) | APPROVED — zero findings |
| Mutation (Phase 5, per-feature) | Scope nil — skip: sole Python production diff = two `PWA_MANIFEST` color literals in `routes.py`; zero logic, empty effective mutation universe |

**Outstanding post-ship items** (weekly /stats review; DoD 1/6/9 open until closed):

1. Live scheme-flip dogfood on the open graph (TestClient can't drive `matchMedia`) — lens + scale must survive the flip.
2. Post-deploy sw.js `-v2` cache-eviction verification on the real phone (Forge condition 1c).
3. KPI-6 self-report after 7 dogfood mornings (baseline `pending-dogfood` in `kpi-contracts.yaml`).
4. D7 hypothesis check — does follow-system actually land dark at 06:45? If not, revisit dark-only / manual toggle.

Archived: `docs/evolution/calm-visual-theme-evolution.md`. SSOT updated at finalize: `brief.md` Component Inventory paragraph, `kpi-contracts.yaml` measured baselines (G-4, G-5, KPI-6).
