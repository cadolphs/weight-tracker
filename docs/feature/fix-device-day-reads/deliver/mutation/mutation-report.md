# Mutation report — fix-device-day-reads (2026-07-24)

- **Tool**: cosmic-ray 8.4.3 (uvx, local distributor); config/session in session scratchpad (`cr-dayframe.toml` / `cr-dayframe.sqlite`)
- **Scope**: `src/weight_tracker/web/routes.py`, git-filtered to the fix diff (`cr-filter-git --branch ae3aab2`): 213 mutants total, 149 skipped (pre-existing lines), **64 executed**
- **Test command (killers)**: `uv run pytest tests/weight-trend-tracker/acceptance/steps/test_day_frame.py -x -q`
- **Raw**: 13 survived / 64 executed = 79.7%
- **Survivor triage**:
  - 11 × `ReplaceBinaryOperator_BitOr_*` at line 99 — the `|` in the `claimed_today: str | None` annotation. `from __future__ import annotations` makes annotations lazy strings; the mutation is runtime-inert. **Equivalent mutants, excluded.**
  - 2 × `NumberReplacer` at line 167 — `RECENT_ANCHOR_ENTRIES = 4` (deliberate skew headroom; behavior identical at 3/5 for any legitimate skew). **Tolerated: killing requires pinning the constant, i.e. testing implementation detail.**
- **Effective kill rate: 51/53 = 96.2% — gate (>= 80%) PASS**
