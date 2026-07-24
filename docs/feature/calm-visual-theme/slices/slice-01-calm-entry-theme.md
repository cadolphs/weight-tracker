# Slice 01 — Calm entry theme (entry + door, light + dark)

**Goal**: The two form screens (`/` and `/login`) render as a calm-minimal, system-scheme-following theme with zero behavior change.

## IN scope

- One shared stylesheet under `/static` (mechanism per DESIGN — hand-written or classless base, D9 pins apply).
- `index.html`: layout, typography, spacing, weight field, Save button, glance line, yesterday reference, save-feedback styling.
- `door.html`: same theme applied; keep ≥ 44 px targets.
- Light AND dark palettes via `prefers-color-scheme`; contrast AA everywhere.
- `manifest.webmanifest` theme/background color alignment (only if trivially needed for consistency).

## OUT scope

- `graph.html` and chart theming (slice 02).
- Any JS changes on the entry screen (hard requirement: zero new JS).
- Fonts, icons, animations, layout restructuring, `/stats`.

## Learning hypothesis

**Disproves, if it fails**: "Following the system scheme is sufficient for the 06:45 dim-bathroom case" — if real mornings still greet Clemens with a bright screen (phone in light mode at dawn), D7 is wrong and a dark-only theme or manual toggle becomes the follow-up. **Confirms, if it succeeds**: a themed presentation can land with zero KPI-1 regression and zero behavior change.

## Acceptance criteria

1. Dark scheme: `/` and `/login` render dark bg / light text; all text ≥ 4.5:1, non-text UI ≥ 3:1.
2. Light scheme: same layout, light palette, same contrast standard.
3. Entry flow unchanged: autofocus + decimal keypad, ≤ 2 s interactive, save/reject/glance-refresh behavior identical; all existing ATs green unmodified.
4. Zero new entry-screen JS; zero requests to non-origin hosts; added CSS ≤ 10 KB uncompressed.
5. With the stylesheet unavailable, logging still works end-to-end.
6. Touch targets ≥ 44 px on both screens.
7. Production data: dogfooded on a real morning log the day it ships.
8. Service-worker cache coordination (Forge review condition, binding): same commit appends `/static/theme.css` to `sw.js` APP_SHELL AND bumps `SHELL_CACHE` to `-v2`; post-deploy dogfood verifies theme.css served on first visit with old cache evicted.

## Dependencies / effort / reference class

- Dependencies: none (first slice; ships the stylesheet slice 02 consumes).
- Effort: ~0.5–1 day. Reference class: prior template-touching slices (US-006, US-007) each ~0.5–1 day.
- Pre-slice SPIKE: none — no unknown mechanism.
