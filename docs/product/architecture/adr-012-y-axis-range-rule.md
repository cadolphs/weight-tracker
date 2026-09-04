# ADR-012: Y-Axis Range Rule — Pure Core Projection Served on Both Series Reads

## Status

Accepted (2026-09-04, Propose mode, recommended default; feature `y-axis-floor`, US-015). Does not supersede any prior ADR; relies on ADR-004 (series untouched), ADR-005 (pure core), ADR-008 (one shared engine).

## Context

The smoothed trend removes daily noise, but the chart's auto-zoomed y-axis puts it back: a month that moved 0.2 kg fills the full 320 px and reads as dramatic swings, on the ambient front-page curve and on the History page alike (`js-2-judge`, the moment the product exists for). DISCUSS locked the rule (D6–D9): a **minimum visible y-span of 2.0 kg, absolute**, applied identically to both lenses on both surfaces at every scale; below the floor the axis becomes `[mid − 1.0, mid + 1.0]`; at or above it the ordinary auto-range is kept; in both cases the bounds snap **outward** to a 0.5 kg grid so no axis ever reads `77.42234`. Two constants, one definition (A25/A29/A31; journey integration rule `y_axis_floor_kg`).

DISCUSS left **where the rule executes** open with equal weight: (A) a `scales.y.range` function in the shared `graph.js`, or (B) a pure core function served on `/entries` and `/trend` and consumed by the engine. Three facts about this codebase decide it:

- **The acceptance suite has no browser and the repository has no JS test runner.** The only precedent for asserting a client-side rule is US-009's palette guard, which greps rendered HTML for hex literals — it proves presence, never arithmetic. The @property scenario ("for any window the span is ≥ 2.0, contains every value, bounds on the 0.5 grid, auto-then-snap above the floor") is a Hypothesis test if the rule is Python and an unfalsifiable comment if it is JavaScript.
- **The per-feature mutation gate (≥ 80 % on modified files) only reaches Python.** A client-side rule would carry both product constants — the ones OQ-12/OQ-14 expect to retune after dogfood — outside every gate the project has.
- **uPlot's own default range is unsafe on exactly the case this feature repairs.** Reading the vendored 1.6.32 bundle: `rangeNum` pads by 10 % of the span and rounds outward to `10^⌊log10 span⌋ / 10`; at span 0 (single or all-equal values) it pads by the value's own magnitude, producing a 0…154 kg axis for a 77 kg entry. Any client placement would therefore reimplement range logic in JS anyway.

Constraints binding either option: series values byte-identical (G-3), read-only ports gain no write methods (CLAUDE.md / ADR-005), zero added fetches/scripts/taps on `/` (KPI-1, G-2/G-5), zero telemetry from a render (ADR-009), parity by construction (ADR-008), never a blank chart.

## Decision

**The rule is a pure Domain Core function; the shell projects it onto both series reads; the engine applies it and computes nothing.**

- `core/axis.py` — `y_axis_range(values) -> AxisRange | None`, total, clock-free, order-invariant. Constants live here and nowhere else: `FLOOR_KG = 2.0`, `GRID_KG = 0.5`, `AUTO_PAD_FRACTION = 0.1`.
- Arithmetic, pinned: no values ⇒ none. Otherwise `span = max − min`. **Below the floor** (`span < 2.0`): `lo₀ = mid − 1.0`, `hi₀ = mid + 1.0`, no extra pad. **At or above the floor** (`span ≥ 2.0`): `lo₀ = min − 0.1·span`, `hi₀ = max + 0.1·span`. Then snap outward: `lo = ⌊2·lo₀ + ε⌋/2`, `hi = ⌈2·hi₀ − ε⌉/2`, `ε = 1e-9`. Every multiple of 0.5 is an exact binary float, so bounds are exact on the wire by construction; ε keeps a value within float noise of a grid line on that line.
- `GET /entries` and `GET /trend` each gain one **additive, optional** field `y_range: [lo, hi] | null` (key always present; `null` iff nothing is plotted), computed from the exact windowed series the route already returns. `WeightHistory` and `TrendProjection` gain **no methods** — this is route-level enrichment on the `confirmation` / `glance` / `recent` precedent, and `ports.py` is untouched.
- `graph.js` supplies `scales: { y: { range: () => [lo, hi] } }` **only when** `y_range` is an array of exactly two finite numbers with `lo < hi`; on absent, null or garbled input it omits the override and uPlot's default range renders. The engine holds no numeric literal for the rule. Degrade-to-absent means an imperfect axis, never a blank chart.

The auto-range branch is an **explicit formula, not a uPlot replay**. For every span in [2.0, 10.0) kg the formula followed by the 0.5 kg snap is identical to uPlot's default followed by the same snap (a 0.5 floor of a 0.1 floor is the 0.5 floor); for spans ≥ 10 kg uPlot's whole-kg pre-rounding can differ by at most 0.5 kg on a bound. The formula is what the acceptance tests state and the property test oracles; importing a magnitude-dependent engine detail into the domain would buy nothing the user can see. This refines DISCUSS assumption A28 ("the pre-feature auto-range") and is recorded as a Changed Assumption in the feature delta.

Falsifiable at the HTTP boundary: a 1M trend window of 77.1…77.3 kg must answer `y_range: [76.0, 78.5]` on `/trend`; a 6M window of 82.1 → 77.2 kg must answer `[76.5, 83.0]`; an empty record must answer `null`.

## Alternatives Considered

- **Client-side `scales.y.range` function in `graph.js`**: Rejected. The smallest diff and no wire change, but the arithmetic is unassertable in this suite (source-regex only), both constants sit outside the mutation gate, and the degenerate-span case must be reimplemented in JS regardless because uPlot's default is wrong there. Parity would hold (one engine), but honesty would rest on convention — the house precedent (ADR-006, ADR-009, ADR-011) is against rules that cannot be falsified.
- **Hybrid — server computes, client re-checks or re-pads**: Rejected outright. Two definitions of one rule violate A29 and the journey's `y_axis_floor_kg` integration rule ("ONE rule with two constants … never per-surface, per-lens, or per-scale"); any drift between them is invisible until a morning glance.
- **Relative floor (a percentage of the plotted level, e.g. 2.6 % ≈ 2.0 kg at 77 kg)**: Rejected. It re-scales the honesty constant with the person's weight — 3.1 kg at 120 kg, 1.3 kg at 50 kg — so the same 0.2 kg wobble would read differently across the life of one record. D6 chose absolute kg because honesty across scales matters more than adaptivity in a single-user, metric-only product; a relative floor also loses the one-line retune OQ-12 promises.
- **Replaying uPlot's `rangeNum` rounding exactly (pad, then round to `10^⌊log10 span⌋/10`, then snap)**: Rejected. Byte-fidelity to a vendored library's internal rounding is not a user-visible property; it makes the pinned rule harder to state, harder to oracle, and couples the domain to a uPlot version. Divergence is bounded (≤ 0.5 kg per bound, only at spans ≥ 10 kg).
- **Placing the function in `core/types.py` or `core/trend.py` instead of a new module**: Rejected. `types.py` is the noun module and `trend.py` is ADR-004's determinism contract ("constants changed only by a superseding ADR"); a tunable presentation constant must not share a file with either, and per-feature mutation scoping is cleaner on a one-ADR-one-module basis (the `core/glance.py` / ADR-006 precedent).

## Consequences

- Positive: the @property honesty scenario becomes a real Hypothesis test over a pure function; the two product constants are single, named, mutation-gated and retunable in one line after dogfood; the series is untouched and the read ports gain nothing; parity is structural (one core definition, one engine consumer, both surfaces fetch the same URLs); the wire cost is two floats per response; uPlot's unsafe degenerate case is bypassed rather than patched; enforcement is free (import-linter already forbids `core → shell/web` by package, so `core/axis.py` cannot regress into I/O).
- Negative / disclosed: a presentation number now rides on data endpoints — a curl reader of `/entries` sees an axis hint it did not ask for (mitigated: additive, optional, ignorable); the engine trusts one more server field, contained by a shape guard whose failure mode is uPlot's own range; the auto branch is a formula rather than the engine's literal default, differing by ≤ 0.5 kg on a bound for spans ≥ 10 kg (A28 refined, not broken — no shipped AT asserts bounds); `graph.js` is pre-cached by the service worker, so the change forces a `SHELL_CACHE` bump (`-v4 → -v5`); the engine-side guard itself remains assertable only by source inspection until the project has a JS runner, which this feature does not justify adding.
