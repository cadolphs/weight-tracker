"""Step vocabulary: the trend column on both entries lists (US-016, ADR-013).

Row state machine (C2a) -- one row definition, three renderers:
    EMPTY (0 entries)            --render--> no table at all, either surface
    RECORDED                     --render--> TABLE [header row + one row per ENTRY,
                                             newest first, Date | Raw | Trend]
    TABLE --backfill/correct-->  TABLE [the saved day appears; the rows above it
                                        carry RTS-revised trend values, in place]
    TABLE --trend projection fails--> RAW-ONLY [same rows, blank trend cells;
                                        entry and save untouched]
    TABLE --lens/scale tap-->    TABLE [the History table never windows, D-17]

Degenerate events covered: empty record, a single entry (diffuse-prior start),
gap days (absent rows, never half-filled), a failing projection, a >200-entry
record at the door.

Oracle independence: every expected trend value is re-derived from `GET /trend`
at "ALL" -- the chart's own series over the HTTP boundary -- never from the
server's row formatter. That is what makes A36 ("one value per day across the
glance, both lists and the chart") falsifiable rather than tautological.

Mandate-12: bodies are <=2 statements delegating to composition services.
"""

from __future__ import annotations

from pytest_bdd import given, then

# ---------------------------------------------------------------- Given


@given("the trend column cannot be computed")
def step_trend_column_broken(composition, monkeypatch):
    composition.trend_rows.break_projection(monkeypatch)


# ---------------------------------------------------------------- Then


@then("every recent row carries a date, a raw weight and a trend weight")
def step_recent_rows_complete(composition, ctx):
    composition.trend_rows.assert_recent_rows_complete(ctx)


@then("every recent trend value is the smoothed series value for that row's day")
def step_recent_trend_matches_series(composition, ctx):
    composition.trend_rows.assert_recent_matches_series(ctx)


@then("the newest recent row's trend value equals the glance line's trend value")
def step_newest_row_matches_glance(composition, ctx):
    composition.trend_rows.assert_newest_row_matches_glance(ctx)


@then("the same day reads the same trend value on the History page")
def step_same_day_both_surfaces(composition, ctx):
    composition.trend_rows.assert_surfaces_agree(ctx)


@then("every complete-record row carries a date, a raw weight and a trend weight")
def step_complete_rows_complete(composition, ctx):
    composition.trend_rows.assert_complete_rows_complete(ctx)


@then("every complete-record trend value is the smoothed series value for that row's day")
def step_complete_trend_matches_series(composition, ctx):
    composition.trend_rows.assert_complete_matches_series(ctx)


@then("the complete record reads identically at every time scale")
def step_complete_unwindowed(composition, ctx):
    composition.trend_rows.assert_unwindowed(ctx)


@then("no rendered row is missing either of its two weights")
def step_no_half_rows(composition, ctx):
    composition.trend_rows.assert_no_half_rows(ctx)


@then("the handed-back recent list carries a trend value for every entry")
def step_handback_carries_trend(composition, ctx):
    composition.trend_rows.assert_handback_complete(ctx)


@then("every handed-back trend value is the smoothed series value for its day")
def step_handback_matches_series(composition, ctx):
    composition.trend_rows.assert_handback_matches_series(ctx)


@then("every recent row still carries its date and raw weight")
def step_recent_raw_survives(composition, ctx):
    composition.trend_rows.assert_raw_survives(ctx)


@then("every recent trend value is blank")
def step_recent_trend_blank(composition, ctx):
    composition.trend_rows.assert_trend_blank(ctx)


@then("the recent rows are exactly the newest rows of the complete record")
def step_one_grammar(composition, ctx):
    composition.trend_rows.assert_one_grammar(ctx)


@then("the recent list names its three columns as table headers")
def step_recent_headers(composition, ctx):
    composition.trend_rows.assert_recent_headers(ctx)


@then("the complete list names its three columns as table headers")
def step_complete_headers(composition, ctx):
    composition.trend_rows.assert_complete_headers(ctx)
