# ADR-006: Glance Weekly Rate — Trailing-7-Day Endpoint Difference of the Smoothed Series

## Status

Accepted (2026-07-23, user-selected; feature `home-trend-display`, US-007). Does **not** supersede ADR-004 — the trend algorithm is unchanged; this ADR derives one number from its output.

## Context

US-007 puts `Trend: 82.3 kg · ↓0.25 kg/week` on the entry screen. The behavioral ACs constrain the rate: deterministic; consistent in sign and magnitude with the displayed trend's movement; kg/week; 0.05-step display with two decimals; glyph from the rounded sign; shown only on a record spanning ≥7 days. ADR-004's local-level model carries **no slope state**, so the rate must be derived from the smoothed series itself. Verified series semantics (`core/trend.py`): daily calendar grid from first to **last entry day** inclusive, gap days present as predict-only smoothed points — so once the entry span reaches 7 days the grid has ≥8 points and a trailing-7-day lookback always exists, even across gaps.

## Decision

`rate_kg_per_week = smoothed[-1] − smoothed[-8]` — the smoothed series' own net change over the trailing 7 grid days, ending at the last entry day. Determinism contract (fixed rules, changed only by a superseding ADR):

- **Visibility threshold**: rate shown only when the record spans ≥7 days, measured as **latest entry date − earliest entry date** (entry-based, not today-based). This threshold and the lookback's data requirement coincide exactly (span ≥7 days ⇔ grid ≥8 points).
- **Quantization**: `round(rate / 0.05) * 0.05`, using Python built-in `round` (banker's rounding: ties at exact 0.025-multiples round half-to-even). Ties are measure-zero in practice; the rule is pinned so a fixed entry set always renders an identical rate (OUT-5 discipline). Displayed with two decimals.
- **Glyph**: from the **rounded** rate's sign — ↓ negative, ↑ positive, → when it rounds to 0.00. Identical neutral styling for all three.
- **Location**: pure function in the Domain Core — `glance(entries) -> GlanceSummary | None` (frozen dataclass: series-end `trend_kg`, `rate_kg_per_week | None`), plus the pure quantize/glyph rule. String formatting (`Trend: … kg · … kg/week`) is shell/template.
- **Delivery** (recorded here for context; mechanism detail in brief.md): glance server-rendered in the `GET /` context (reuses the already-fetched entry list — zero added I/O or HTTP) and included as a `glance` field in the `POST /entries` JSON response for the in-place refresh. KPI-3 separation is structural: the glance never touches `GET /trend` (which emits `trend.view.opened` unconditionally); the glance emits its own `trend.glance.shown` event per delivery.

## Alternatives Considered

- **Least-squares slope over the last N days of the smoothed series**: Rejected. Introduces a free parameter N with no AC to justify it, double-smooths an already-smoothed series, and can disagree in sign with the visible endpoint movement (V-shaped week: net change 0, LS slope ≠ 0) — failing the sign-consistency AC in exactly the cases that matter.
- **Upgrade to a local-linear-trend state model (slope state)**: Rejected. Would supersede ADR-004: new process-noise parameters = new determinism contract, the research-derived AC margins (spike ≤0.3 kg, gap continuity) would need re-derivation, the dogfood-validated feel would be invalidated — a disproportionate rewrite of a shipped algorithm to serve one glance line. LLT slope estimates are also jumpy after gaps/spikes.
- **Delivery via a separate `GET /glance` endpoint**: Rejected. One extra HTTP round-trip on every logging morning against the ≤2 s entry-primacy guardrail; glance pops in after first paint instead of arriving in the initial HTML; first-entry appearance needs a second post-save fetch.
- **Delivery via `GET /trend?glance=1` suppressing the KPI-3 event**: Rejected outright. KPI-3 integrity by query parameter is a fragile convention (one bug or crafted URL flips the deliberate-view counter); full point series is an overweight payload for two numbers.

## Consequences

- Positive: sign-and-magnitude consistency with the displayed trend holds **by construction** — the rate *is* the line's own trailing-week net change; deterministic pure fold, inherits OUT-5; zero change to ADR-004; no new dependencies; gap days on the grid make the lookback total (no special gap handling).
- Negative / disclosed behavior: the rate revises together with the line under RTS retrospective revision (both endpoints move as entries arrive) — coherent by construction, and the DISCUSS sushi example (0.25 → 0.20 after saving 83.6) is exactly this; the rate's window ends at the **last entry day**, not today — on a stale record the glance reports where the line ends, matching the graph (single-source AC).
