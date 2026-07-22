# RED Classification — weight-trend-tracker (DISTILL fail-for-right-reason gate)

Date: 2026-07-22 · Command: `RED_GATE_ALL=1 uv run pytest` (RED_GATE_ALL runs @pending
scenarios too; the committed default runs only the walking skeleton, rest skipped
one-at-a-time). Result: **71 failed, 0 errors, 0 skipped**.

## Verdict: ALL 71 tests are RED for the right reason — `MISSING_FUNCTIONALITY`

Every failure is `AssertionError: Not yet implemented -- RED scaffold`, raised inside a
production scaffold (Mandate 7), never in test infrastructure:

| Raising production scaffold | Failing tests | Classification |
|---|---|---|
| `src/weight_tracker/composition.py::build_app` | 57 (all Gherkin scenario instances — every HTTP scenario reaches the production composition root and stops at the unimplemented app) | MISSING_FUNCTIONALITY |
| `src/weight_tracker/core/trend.py::trend_series` | 7 (pure-core trend PBT properties) | MISSING_FUNCTIONALITY |
| `src/weight_tracker/core/validation.py` (`validate_weight` / `validate_entry_date` / `apply_entry`) | 7 (pure-core validation PBT properties) | MISSING_FUNCTIONALITY |

- `IMPORT_ERROR` / `FIXTURE_BROKEN` / `SETUP_FAILURE`: **0** — collection is clean
  (71 collected), all imports succeed against the scaffolds.
- `WRONG_ASSERTION` / `OBSERVABLE_NOT_AT_PORT`: **0** — universes are port-exposed only
  (`record.entries`, `telemetry.entry_logged_count`, `telemetry.trend_view_opened_count`
  via WeightHistory + the KPI query surface; no internal fields).

## Notes for DELIVER (RED phase entry)

1. Default suite state: walking skeleton enabled (RED), all other scenarios `@pending`
   (skipped). Unskip = remove the `@pending` tag from the one scenario the step owns.
2. Greenfield: no green walking skeleton exists (SPIKE skipped) — the WS scenario is the
   first RED to drive to GREEN.
3. The startup-refusal scenario ("A record that cannot be stored safely refuses to open")
   asserts specifically `StartupRefused` — a scaffold `AssertionError` propagates as RED;
   a generic-exception catch would be a false GREEN. Do not widen the except clause.
4. `@pending` → pytest marker via `conftest.pytest_collection_modifyitems`; the
   `RED_GATE_ALL=1` escape hatch exists only for this gate and re-classification runs.
