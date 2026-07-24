# ADR-008: Front-Page Graph Delivery — Async Fetch via a Shared Extracted Graph Module

## Status

Accepted (2026-07-24, user-selected; feature `graph-first-home`, US-010)

## Context

Decisions D6/D7 put the full-control trend graph (Trend/Raw lens + 1W…All scale picker) on `/` above the entry form. Binding constraints: entry screen interactive ≤2 s with the graph present; graph/list data must never block or delay input readiness; degrade-to-absent on failure; in-place refresh after save (A15); lens/scale behavior byte-for-byte identical to `/graph` (US-010 AC); single data source (same `/trend` `/entries` reads, same smoothed series, no second algorithm); KPI-3 purity — ambient renders add 0 to the deliberate counter (A19). Today the chart logic lives as ~130 lines of inline JS in `graph.html`; `GET /trend` emits `trend.view.opened` unconditionally, which is why it could not be reused "as-is" for an ambient surface.

## Decision

The entry form remains plain server-rendered HTML (input readiness unchanged by construction). The chart JS is **extracted from `graph.html` into one shared static module `web/static/graph.js`** (fetch → grid-series builders → themed uPlot render → lens/scale state on the mount's `data-view`/`data-scale`, matchMedia re-render — all shipped behavior, relocated not rewritten). Both pages load it (deferred, end of body, same origin) and configure it with their mount and initial lens/scale. The front page fetches `/trend?scale=3M` (default, A17) after load — the **same data path as the History page**; explicit taps fetch exactly as `/graph` does today. Post-save in-place refresh = re-run the fetch at the currently selected lens/scale. Fetch failure, render failure, or 0 entries → the graph area is absent (absent-never-stale, D-13 pin); the form, save, and confirmation are untouched. This is only viable because ADR-009 makes `/trend` and `/entries` telemetry-free pure reads — an ambient fetch carries no KPI-3 signal to pollute.

ADR-006's rejection of an extra round trip (for the glance) does **not** transfer: the glance is above-the-fold text that can ride first paint; a canvas chart cannot paint before uPlot executes regardless, and the same-host fetch runs in parallel with script load. Entry primacy is measured on input readiness, which is server HTML either way.

## Alternatives Considered

- **Inline server-embedded default series (hybrid)**: `GET /` embeds the Trend@3M points as JSON (glance precedent); taps fetch. Rejected — creates two data paths (inline bootstrap + fetch-on-interaction) and a two-armed save-refresh (response enrichment *plus* a refetch fallback whenever the pre-save selection differs from the default), buying only ~50–150 ms of chart paint latency that the uPlot script load largely masks. The shared-module reuse gate (one AT surface for lens/scale parity) outweighs it.
- **Server-side rendered SVG/static chart**: Rejected — loses the interactive lens/scale controls (D7), introduces a second render path against the single-source rule, and discards the shipped, mutation-tested uPlot + token-theming substrate (ADR-007).

## Consequences

- Positive: one chart code path serves both surfaces — the US-010 "identical to `/graph`" AC holds by construction; simplest possible refresh; degrade-to-absent falls out of the async shape; per-surface lens/scale state is trivially separate (front page takes no query params; `/graph` keeps honoring `?view=`/`?scale=`, A17).
- Negative / disclosed: the ambient chart paints one fetch after first paint (accepted — ambient surface; the form never waits); the front page gains two same-origin vendored scripts (`uplot.iife.min.js`, `graph.js`) — calm-visual-theme's G-5 "0 new entry-screen scripts" AT clause must be **consciously renegotiated at DISTILL** (the intent — zero new external origins + entry primacy — is preserved).
