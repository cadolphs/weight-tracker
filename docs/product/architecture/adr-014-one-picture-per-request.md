# ADR-014: One Picture per Request — A Single Record Projection Replaces Three Injected Callables

## Status

Accepted (2026-11-23, architecture review via `/improve-codebase-architecture`; no feature). Supersedes in part ADR-006 and ADR-013 where they describe the glance and the day-keyed trend as separately injected pure callables. Relies on ADR-004 (one series, fixed parameters), ADR-005 (pure core, adapters injected at the composition root), ADR-010 (whole-record map), ADR-012 (axis rule takes values, windowing upstream).

## Context

Each feature since ADR-006 added one pure derivation over the record and injected it into `build_router` as its own callable: `trend_series_in`, `glance_summary_of`, `trend_by_day`. Each handler then hand-wired its own mix. Three costs accumulated:

- `GET /` and `POST /entries` ran the full Kalman+RTS pass **twice** per request — once inside `glance`, once inside `trend_by_day` — because each callable smooths the record itself.
- Two degrade closures (`glance_or_degrade`, `trend_by_day_or_degrade`) carried the same try/except/log shape with different fallbacks, and the invariant "the glance's end value *is* the newest row's trend value" (A36, ADR-013) was held by convention across two call sites rather than by construction.
- `build_app` exposed no seam for these callables, so every degrade scenario monkeypatched three module attributes (`core.trend.X`, `composition.X`, `web.routes.X`) with `raising=False` and restarted the app. One adapter per seam: the seam was hypothetical, and tests went around it.

## Decision

**One pure projection, the Picture, built once per request from the single `all_entries()` read; one seam for it at `build_app`; one degrade boundary.**

- `core/picture.py`: frozen `Picture` holding every entries-only derivation — `series` (the trend, Kalman run exactly once), `trend_by_day`, `glance`, `recent_head`, `record_weights`, `earliest_pickable_day` — built by one function `picture_of(entries)`. Eager, not lazy: one call, one smoothing, visible cost. `recent_head`, `RECENT_LIST_ENTRIES`, `record_weights_map` and `date_row_earliest_day` move here from `web/routes.py`.
- **Only `trend_series` sees entries.** `glance` and the day-keyed lookup take the series, so no core path can run the Kalman twice. Anything that takes `scale` or `today` (windowed series, windowed raw entries, axis range) stays outside the picture as a pure function over `picture.series`; `trend_series_in` becomes a windowing of a series it is handed.
- **Numbers in the core, strings in the shell.** The picture carries no display text. `EntryRow`, the two precisions, the row builders, `glance_display_text`, the wire shapes and `recent_entries_payload` move to `web/views.py` and take a `Picture`. `web/routes.py` keeps handlers and the degrade boundary only. (`Saved.confirmation` still formats inside `core/types.py`; noted, not changed here.)
- **One degrade boundary.** `picture_or_degrade(entries)` logs one structured event, `picture.degraded`, and returns a **trendless picture**: empty series, empty `trend_by_day`, `glance = None`, with `recent_head`, `record_weights` and `earliest_pickable_day` still computed because they do not depend on smoothing. Rows keep date and raw with blank trend cells; the glance line is absent; the save carries `glance: null` and `trend_kg: null`. A failing trend now removes the glance line *and* the trend cells together — they are one derivation, so they fail as one.
- **The seam is real.** `build_app(..., *, picture_of=picture_of)`: production passes nothing; the acceptance composition passes a raising callable to test the degrade boundary through the interface that owns it. No monkeypatch, no module-attribute guessing. `build_router` takes `picture_of` in place of the three callables. Pillar 3 ("only the Clock is injected") gains one clause: the picture override is a fault-injection door, never a fake.
- Handlers that need no trend (`GET /entries`, the raw lens) build no picture. `GET /trend` builds the picture **without** the degrade boundary: a broken series must not pretend to answer (the chart's absent-area degrade is client-side, ADR-008), so its failure surfaces as a failed read, exactly as before.

## Alternatives Considered

- **Keep three callables, add three `build_app` overrides**: Rejected. Makes the seam real but leaves the double smoothing, the duplicated degrade closures and the by-convention A36 invariant in place; and the next derivation adds a fourth kwarg.
- **Lazy picture (`cached_property`)**: Rejected. Hides when the Kalman runs and whether it ran; the cost should be legible at the one call site. The one route that needs no trend simply does not build a picture.
- **Picture carries formatted rows**: Rejected. `core/glance.py` already states that formatting belongs to the shell; putting `'82.43'` in the core would make a display precision a core constant.
- **Two degrade points kept inside the picture (glance can fail while rows keep their trend)**: Rejected. Both derive from the same series; a failure mode in which one survives and the other does not cannot occur in the real system, so the tests that assume it would be testing a fiction.
- **Picture also owns windowing and the axis**: Rejected. Those take `scale` and `today`; folding them in would give the picture parameters and turn one value into a family. ADR-012's "the rule takes values, windowing happens upstream" stands.

## Consequences

- `test_glance_properties` and `test_trend_by_day_properties` assert through `picture_of(entries)`; a new `test_picture_properties` pins `glance.trend_kg == trend_by_day[newest day]` as a property rather than an HTTP cross-check.
- `break_computation`, `break_series` and `break_projection` in the acceptance composition collapse into one `break_picture()`.
- `milestone-12.feature` prose "a failing trend empties the trend cells and nothing else" becomes "empties the trend cells and the glance line; the raw record stands". Its steps are unchanged.
- ADR-013's rejection of "a new core module for the projection" stands for a *single* derivation; the picture earns a module because it is the composite and the single place the smoothing runs.
