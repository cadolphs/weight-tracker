# Mutation Report — home-trend-display (per-feature strategy, scoped to modified files)

## Steps 01-01..01-03 — glance core + render/save-refresh + render semantics (2026-07-23)

- **Tool**: cosmic-ray 8.4.3 (project venv, local distributor); config/session in session scratchpad (`cr-0103.toml` / `cr-0103.sqlite`)
- **Scope**: feature delta via `git-filter` (branch = pre-feature HEAD `a3382b6`) over
  `src/weight_tracker/core/glance.py`, `src/weight_tracker/web/routes.py`,
  `src/weight_tracker/composition.py` at HEAD `fb7dbcd`
  (template/JS assets are outside cosmic-ray's mutable surface)
- **Killers**: milestone-6 acceptance steps + glance property suite —
  `pytest -x tests/weight-trend-tracker/acceptance/steps/test_milestone_6.py tests/weight-trend-tracker/acceptance/properties/test_glance_properties.py`
  (21 tests, ~2.1 s/mutant)
- **Post-run safety**: `git checkout -- src/ tests/` → `git status` clean on `src/`;
  full suite re-verified GREEN (107 passed, 5 skipped)

### Results

| Metric | Value |
|---|---|
| Jobs | 293 (151 skipped by git filter — outside the feature delta) |
| Executed | 142 |
| Killed | 107 |
| Surviving | 35 |
| Equivalent mutants | 35 |
| Raw kill rate | 107/142 = 75.4% |
| **Effective kill rate (excluding equivalents)** | **107/107 = 100% — PASS (>= 80%)** |

Every behavior-changing mutant in the feature delta was killed. Notably pinned by the
01-03 scenarios: `RATE_SPAN_MIN_DAYS` 7→6/7→8 and every comparison flip on the span
guard (the entry-based boundary rows of the young-record outline did exactly their job),
`series[-8]`→`-7`/`-9`/positive-index lookback slips, the `RATE_STEP_KG_PER_WEEK`
quantize literals and operator swaps, both `rate_glyph` sign guards (direction outline +
steady 0.00 scenario), the `glance` empty-record guard, the `deliver_glance`
None-short-circuit + event emission, and the composition-root wiring.

### Equivalent mutants — 35

| Mutation | Count | Why equivalent |
|---|---|---|
| `X \| None` return-annotation `BitOr` swaps (`glance.py:35` glance, `:57` `_trailing_week_rate`, `routes.py:199` `deliver_glance`) | 33 | `from __future__ import annotations` — annotations never evaluated at runtime |
| `glance.py:27` `@dataclass(frozen=True)` → `False` on `GlanceSummary` | 1 | Immutability is a design constraint, not observable port-to-port; no production code mutates domain values (same disposition as types.py frozen mutants, 03-01) |
| `glance.py:79` `rate_glyph` `> 0` → `!= 0` | 1 | Reached only after the `< 0` guard returned, so the operand is non-negative: `!= 0` ≡ `> 0` there (−0.0 compares equal to 0 under both) |

### Genuine survivors — 0

No AT gaps to route. The DISTILL oracle design (pinned ADR-006 expressions encoded
verbatim in `GlanceService`, boundary rows logging ON the boundary day, the resting-record
D-12 discriminator) left no unpinned behavior in the glance surface.

### Verdict

**PASS — effective kill rate 100% (>= 80% gate).** No mutation-test response required;
no back-pressure to `nw-acceptance-designer` from this run.

## Step 01-04 — degrade-to-null containment, entry primacy, KPI separation (2026-07-23)

- **Tool**: cosmic-ray 8.4.3 (project venv, local distributor); config/session in session scratchpad (`cr-0104.toml` / `cr-0104.sqlite`)
- **Scope**: step delta via `git-filter` (branch = pre-step HEAD `fb7dbcd`) over
  `src/weight_tracker/web/routes.py` at HEAD `8181842` (post-refactor;
  `index.html` JS is outside cosmic-ray's mutable surface)
- **Killers**: milestone-6 acceptance steps + glance property suite —
  `pytest -x tests/weight-trend-tracker/acceptance/steps/test_milestone_6.py tests/weight-trend-tracker/acceptance/properties/test_glance_properties.py`
  (26 tests)
- **Post-run safety**: `git checkout -- src/ tests/` → `git status` clean on `src/`;
  killer suite re-verified GREEN (26 passed)

### Results

| Metric | Value |
|---|---|
| Jobs | 182 (170 skipped by git filter — outside the step delta) |
| Executed | 12 |
| Killed | 1 |
| Surviving | 11 |
| Equivalent mutants | 11 |
| Raw kill rate | 1/12 = 8.3% |
| **Effective kill rate (excluding equivalents)** | **1/1 = 100% — PASS (>= 80%)** |

The single behavior-changing mutant in the delta was killed by the milestone-6
degradation/KPI scenarios (containment guard + windowed glance count). The
containment `try/except -> None` and the `/stats` rolling-week read are pinned by
"A trend hiccup hides the glance, not the morning", "A trend hiccup never blocks
the save", and "The stats page still tells deliberate study from ambient glances".

### Equivalent mutants — 11

| Mutation | Count | Why equivalent |
|---|---|---|
| `X \| None` return-annotation `BitOr` swaps (`routes.py` `glance_or_degrade` delta annotation, occurrence 2) | 11 | `from __future__ import annotations` — annotations never evaluated at runtime (same class as the 01-01..01-03 run's 33 equivalents) |
