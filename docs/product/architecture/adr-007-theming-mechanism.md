# ADR-007: Theming mechanism — hand-written design-token stylesheet, CUBE-lite structure

Status: Accepted (2026-07-23, DESIGN wave of `calm-visual-theme`)

## Context

Feature `calm-visual-theme` restyles all three screens (entry, graph, door) calm-minimal, following the system color scheme. DISCUSS pinned: ≤ 10 KB added CSS uncompressed, zero external requests, no web fonts, zero new entry-screen JS, WCAG AA in both schemes (text ≥ 4.5:1, non-text ≥ 3:1), progressive enhancement, DOM id / `aria-pressed` contracts untouched. The build mechanism was deferred to DESIGN (DISCUSS D9). uPlot renders axes/grid/series on canvas — CSS cannot restyle canvas pixels.

## Decision

1. **One hand-written stylesheet** `src/weight_tracker/web/static/theme.css` (~4.7 KB est., ceiling ~6 KB) built on CSS custom properties as design tokens: a `:root` token block and a `@media (prefers-color-scheme: dark)` override block. Served by the existing `GET /static/{asset_name}` route — zero shell-code changes.
2. **Structure: CUBE-lite** (user-requested evaluation; adopted). CUBE CSS's philosophy — global-first, token-driven, lean on the cascade — matches this design exactly; its layers map without inventing classes:
   - **Tokens** — custom properties, light + dark.
   - **Global** (CUBE's global styles) — reset, typography, base elements.
   - **Composition** — one main-column flow primitive.
   - **Utility** — *empty layer, deliberately*: 3 templates, ~15 element types, stable ids; utility classes would be churn without benefit.
   - **Block** — element/id-keyed rules (`#trend-glance`, `#save-feedback`, `#scale-picker`, `#view-toggle`, `#door-rejection`, …) — existing ids are the hooks; no new class attributes in templates.
   - **Exception** — state via attributes (`aria-pressed`, `hidden`, `:focus-visible`) — CUBE's own recommended exception mechanism; the pressed-state fill treatment lives here.
   Byte impact of the convention: ≈ 0 (layer comments only).
3. **Chart theming**: tokens are the single source of truth. `renderChart` reads `--chart-axis`, `--chart-grid`, `--chart-raw`, `--chart-trend` via `getComputedStyle` at build time; one `matchMedia('(prefers-color-scheme: dark)')` change listener calls the existing `showGraph(page.dataset.scale)` (preserves lens + scale by construction). ~8 lines of new JS, graph page only. Hard-coded `#1f6feb`/`#d29922` in `graph.html` are replaced by token reads. Vendored uPlot files stay byte-identical.
4. **PWA alignment**: `PWA_MANIFEST` colors align to the palette (`#FAFAF8`/`#1A1A1A`); `theme.css` joins the `sw.js` APP_SHELL precache (cache-name bump = DELIVER detail).

## Alternatives considered

- **Pico.css v2 classless (vendored)** — rejected: ~70–80 KB minified uncompressed, 7–8× over the 10 KB budget; slim builds still ~30 KB+.
- **Simple.css v2 (vendored)** — rejected: ~10–11 KB minified before overrides; est. 1.5–2.5 KB overrides needed (no `aria-pressed` styling, no 44 px guarantee, no chart tokens, unaudited palette) → ~12–13.5 KB total, over budget, with the overrides carrying most of the calm-minimal identity anyway.
- **Hybrid: vendored micro-reset (~1 KB) + hand-written rest** — rejected: a normalize layer buys ~nothing for 3 templates on evergreen mobile browsers; vendoring overhead for ~300 B of rules we would write anyway.
- **Full CUBE CSS with utility/block classes** — rejected in favor of CUBE-lite: class machinery forces template churn at a scale where ids and elements already cover every hook.
- **Pure CSS-variable chart theming (no JS)** — rejected: canvas internals unreachable by CSS; load-time-only token reads would fail the mid-session scheme-flip scenario (US-009).

## Consequences

- G-4 contrast compliance is arithmetic we own: the token table in `docs/feature/calm-visual-theme/feature-delta.md` (§ Design Tokens) lists every pair with computed ratios; tightest pair is light `--chart-grid` at ~3.3:1 (≥ 3:1 non-text). DISTILL's checker is authoritative; any flagged pair shifts one hex step.
- No new dependencies, licenses, or vendor files to track. No new ports, adapters, containers, or C4 changes; ADR-005 (functional core) untouched — no domain code in scope.
- Degradations: stylesheet load failure → unstyled but fully functional app (US-008 AC); missing `matchMedia` support → chart colors fixed at load-time scheme while page CSS still flips (accepted).
- Entry screen keeps zero new JS; the only JS delta is the graph-page scheme wiring.
