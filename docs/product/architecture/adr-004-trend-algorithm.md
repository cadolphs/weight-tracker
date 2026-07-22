# ADR-004: Trend Algorithm — Local-Level Kalman Filter + RTS Smoother, Fixed Parameters, Huberized

## Status

Accepted (2026-07-22, user-selected; supersedes the DESIGN-draft entry-sequence EMA). Evidence: `docs/research/algorithms/weight-trend-smoothing-comprehensive-research.md` (Nova, 16 sources, Spec A).

## Context

US-004 behavioral ACs: +1.5 kg one-day spike moves trend ≤0.3 kg; ≤7-day gaps cause no discontinuity or jump; sustained 0.5 kg/week change visible within 7 days; deterministic (same entries → same line); backfills/corrections recompute affected range. User explicitly prefers the retrospective, slow-moving feel observed in PLTNM (past trend values refine as new entries arrive). Research confirms the smoothed (two-sided) estimate is statistically optimal — strictly lower MSE than any causal filter (research Finding 4). The Raw toggle (US-005) provides the immutable ground-truth view.

## Decision

Local-level state-space model on the **daily calendar grid** (first entry → last entry): `x_t = x_{t−1} + η_t, η∼N(0,q)`; `y_t = x_t + ε_t, ε∼N(0,r)`. Kalman filter forward pass; Rauch–Tung–Striebel backward pass; **display the smoothed series** — retrospective revision of recent trend values is intentional and desired. Fixed constants (never re-estimated from data, preserving determinism):

- `r = 0.20 kg²` (σ_ε ≈ 0.45 kg daily scale noise)
- `q = r·α²/(1−α)` with `α = 0.10` → `q ≈ 0.00222 kg²` (steady-state forward gain = Hacker's Diet α = 0.1)
- Huber clip `δ = 1.0 kg` on innovations
- Missing days = prediction-only step (no update); no interpolation.

Full-series recompute (forward + backward, O(n) scalar ops) on every read and after every edit — microseconds at this scale; satisfies the correction-recompute AC structurally, no cache invalidation. Pure, dependency-free function (~45 lines) in the Domain Core; `TrendProjection` port stays read-only, derived-never-stored. Smoothed variance `Ps` yields an optional uncertainty band — deferred to DELIVER. Determinism framing: a *fixed* entry set always renders an identical line (the AC as written); the line changes only when the entry set changes.

AC margins (research arithmetic): spike ≈ +0.05–0.08 kg ≤ 0.3 (4–6× margin, clip caps any spike); 7-day gap bridged smoothly by construction (prediction variance grows, smoother interpolates optimally — no jump/kink); 0.5 kg/week visible at curve end within ~7 days; deterministic pure fold + backward pass.

## Alternatives Considered

- **Entry-sequence EMA α = 0.1 (Hacker's Diet; the earlier DESIGN draft)**: Rejected in favor of Spec A. Passes all ACs, but time-stretches across gaps (absorbs real change 7× slower in calendar time after a 7-day gap) and lacks the retrospective refinement the user wants. Survives as the algorithm's own forward pass and as the documented fallback (research Spec C, ~10-line delta) if dogfooding rejects revision.
- **Gap-scaled EMA (`α_eff = 1−(1−α)^Δt`, Libra-style)**: Rejected. Post-7-day-gap gain ≈ 0.52 → a post-gap +1.5 kg spike moves the trend ≈ +0.78 kg — fails the ≤0.3 kg AC outright (research Finding 7).
- **Interpolate-then-EMA (TrendWeight)**: Rejected. Gap-day trend snaps into place when the gap closes (unexplained large revision — the risky kind) and a post-gap outlier back-propagates into interpolated days (research Findings 3, 9).
- **LOESS / kernel regression**: Rejected. Needs dense data (NIST), high endpoint variance exactly where the user looks daily, opaque span/degree parameters, whole-curve refit cost (research Finding 6).
- **Centered 7-day moving average**: Rejected. Unstable/incomplete at the series end; a spike becomes a 7-day plateau artifact (research Findings 6, 7).

## Consequences

- Positive: every US-004 AC met with margin; statistically optimal estimate; PLTNM-like feel matches stated preference; free uncertainty band; pure function fits the FP core; fallback to causal EMA is a ~10-line change sharing the same forward pass.
- Negative: past trend values revise (bounded, geometrically decaying — only ~2–3 recent weeks move perceptibly; disclosed behavior, precedent: Happy Scale's recommended default); DISTILL gap/revision oracles must assert *smoothed continuity of the current line*, not immutability of previously rendered values; trend has values on gap days (trend line ≠ raw points — US-002's "no interpolated raw points" is unaffected, raw view never changes).

## Validation Gates

- **Dogfood gate (DELIVER, slice 04)**: revision-UX evidence is Low-Medium confidence (research Gap 2 — product practice + stated preference, no HCI study). Validate empirically: render Spec A (smoothed) vs Spec C (causal EMA, same forward pass) on the same real production history for one dogfood session. If revision feels unsettling, fall back to Spec C — a ~10-line delta (drop backward pass, display `x_filt`), captured as a superseding ADR; no architecture rework.
- **Parameter versioning protocol**: constants (r, q/α, δ) are part of the determinism contract. Post-dogfood sanity pass: compute `std(first differences of real entries)/√2`; if it deviates from σ_ε ≈ 0.45 kg by >20%, change r via a superseding ADR + explicit version bump (historical renderings shift once, knowingly). NEVER auto-estimate parameters from data at runtime.
