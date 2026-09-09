# Mutation report — numeric-trend-history (per-feature strategy, scoped to modified files)

- **Tool**: cosmic-ray 8.4.3 via `uvx cosmic-ray` (local distributor); config/session in the
  session scratchpad (`cr-nth.toml` / `cr-nth.sqlite`)
- **Scope**: feature delta via `git-filter` (branch = `95794e0`, the DISCUSS/DESIGN/DISTILL
  commit) over the production tree at `a38e8fa`. The filter reduced 1,663 candidate jobs to
  **31 executed**, all on `web/routes.py`'s changed lines.
- **Why the two new core functions contribute zero jobs** — and why that is a fact about
  them, not a gap in the run: `core/trend.py: trend_by_day` is a single dict comprehension
  over the shipped series, and `core/types.py: day_label` is a single f-string. Between
  them they contain no numeric literal, no comparison, no boolean, no branch and no
  decorator — nothing in cosmic-ray's operator set has a site to mutate. The projection's
  behaviour is instead pinned by `test_trend_by_day_properties.py` (7 properties: series
  identity, totality over the record, grid span including gaps, order-invariance,
  determinism, the empty record, the diffuse-prior single entry), and the label's by the
  cell-grammar properties plus the byte-identical confirmation guard.
- **Killers**: milestone-12 + the feature's row/projection/hand-back property suites —
  `uv run pytest -x -q -p no:cacheprovider tests/weight-trend-tracker/acceptance/steps/test_milestone_12.py tests/weight-trend-tracker/acceptance/properties/test_recent_list_properties.py tests/weight-trend-tracker/acceptance/properties/test_trend_by_day_properties.py tests/weight-trend-tracker/acceptance/properties/test_save_recent_properties.py`
- **Post-run safety**: tree committed clean before the run; `git status --porcelain src/`
  empty afterwards; full suite re-run green.

## Results

| Metric | Value |
|---|---|
| Jobs | 1,663 (1,632 skipped by git filter — outside the feature delta) |
| Executed | 31 (all `web/routes.py`) |
| Killed | 20 |
| Surviving | 11 |
| Equivalent mutants | 11 |
| Raw kill rate | 20/31 = **64.5%** |
| **Effective kill rate (excluding equivalents)** | **20/20 = 100% — PASS (>= 80%)** |

The raw rate sits below the gate only because the delta is small and annotation-dense: a
single `float | None` annotation generates eleven binary-operator mutants on its own, which
is 35% of the executed jobs. Every mutant with a runtime site died.

## Survivors, all equivalent

All 11 are `ReplaceBinaryOperator_BitOr_*` on occurrence 5 in `routes.py` — the `|` in
`entry_row(day, weight_kg, trend_kg: float | None)`. `routes.py` carries
`from __future__ import annotations`, so every annotation is stored as a string and never
evaluated; replacing `|` with `+`, `-`, `*`, `/`, `//`, `%`, `**`, `>>`, `<<`, `&` or `^`
inside one cannot change behaviour at any input. Provably equivalent, not untested — the
same class the y-axis-floor run recorded as "lazy annotations".

## Survivor closed during the run

`ReplaceTrueWithFalse 0` — `@dataclass(frozen=True)` on `EntryRow` — survived the first
pass. Not equivalent: unfreezing the row is a real loss of the project's stated paradigm
guarantee (CLAUDE.md, ADR-005: pure functions over frozen dataclasses), and it matters
here specifically because three renderers share one row definition and two of them hand
their rows straight to a template — a row that could be rewritten between building and
rendering is how the front page and the History page would begin telling different stories
about the same day. Closed by `test_a_rendered_row_cannot_be_edited_after_the_fact`
(`test_recent_list_properties.py`), which asserts `FrozenInstanceError` on assignment; the
mutant died on the re-run.

## What the killers pin, among others

The two rendered precisions (`RAW_DECIMALS = 1`, `TREND_DECIMALS = 2`) and every digit they
produce; the row's three cells and their order; the empty trend cell under a degraded
projection, and the fact that degrading costs the row nothing else; the seven-entry slice
and its boundary; the per-day lookup rather than a positional zip; the `trend_kg` key on the
save's hand-back and its absence from `GET /entries`; and the column headings, including
that `kg` is stated in the header and never in a cell.
