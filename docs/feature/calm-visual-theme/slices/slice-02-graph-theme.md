# Slice 02 — Graph theme (controls + chart, light + dark)

**Goal**: `/graph` matches the calm theme; lens/scale controls have an unmistakable pressed state; the uPlot chart is legible in both color schemes.

## IN scope

- `graph.html` layout + controls restyled from the shared stylesheet (slice 01).
- Pressed state for `aria-pressed="true"` buttons distinguishable beyond color, both schemes.
- Chart theming: axis label, gridline, tick, and series stroke colors per scheme (raw + trend lenses). Minimal JS permitted here (`matchMedia("(prefers-color-scheme: dark)")` → uPlot color options; re-render on change).
- Empty-invite and back-link styling.

## OUT scope

- Entry/door screens (slice 01).
- Chart behavior: windowing, gaps (`spanGaps: false`), lens/scale semantics, `data-view`/`data-scale` contract — all untouched.
- New chart features (tooltips, cursors, legends).

## Learning hypothesis

**Disproves, if it fails**: "uPlot can be made dark-legible via color options alone" — if axis/gridline theming through options + CSS proves insufficient, that changes the charting cost assumption (custom build or library swap discussion). **Confirms**: the whole app can be re-skinned without touching domain or acceptance contracts.

## Acceptance criteria

1. Dark scheme: axis labels ≥ 4.5:1; gridlines and both series strokes ≥ 3:1 against background; raw gaps still gaps.
2. Light scheme: equally tuned (no "default uPlot on tinted background" look).
3. Selected scale and lens buttons distinguishable by shape/weight/fill, not color alone; `aria-pressed` markup contract unchanged.
4. Scheme flip mid-session re-themes page and chart without losing selected lens/scale.
5. Graph interactive ≤ 2 s (G-2 guardrail stays green); all existing graph ATs green unmodified.
6. No non-origin requests; JS delta limited to color/scheme wiring.
7. Production data: dogfooded against the real record the day it ships.

## Dependencies / effort / reference class

- Dependencies: slice 01 (shared stylesheet).
- Effort: ~0.5–1 day. Reference class: US-002/US-005 graph slices (~1 day each); theming is smaller.
- Pre-slice SPIKE: none — uPlot color options documented; hypothesis covers the residual risk.
