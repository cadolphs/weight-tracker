"""Step vocabulary: the home glance -- trend + weekly rate at the moment of logging (US-007).

Glance state machine (C2a), driven by the entry record (entry-based span, ADR-006):
    NO_LINE (0 entries) --first save--> VALUE_ONLY        [trend from the first entry]
    VALUE_ONLY (span < 7 days) --save reaching span >= 7--> VALUE_AND_RATE
    VALUE_AND_RATE --save--> VALUE_AND_RATE               [pair co-revises with the line]
    any state --rejected save--> unchanged                [no glance field, no event]
    any state --glance computation fails--> LINE_ABSENT   [degrade; logging never blocked]
    VALUE_AND_RATE --days pass, no entries--> VALUE_AND_RATE  [span is ENTRY-based, not
                                                               today-based; line ends at
                                                               the last entry day]
Illegal/degenerate events covered per state: rejected input with a glance showing,
failure mid-morning (render and save), rate demanded of a young record, KPI-3
pollution by ambient renders.

Mandate-12: bodies are <=2 statements delegating to composition services.
"""

from __future__ import annotations

from domain_types import parse_direction, parse_rate_disposition
from pytest_bdd import given, parsers, then, when

# ---------------------------------------------------------------- Given


@given(parsers.parse("his weight has been {direction} for the last two weeks"))
def step_recent_direction(composition, direction):
    composition.glance.seed_recent(parse_direction(direction))


@given("the entry screen shows the trend at a glance")
def step_glance_showing(composition, ctx):
    composition.glance.shows_now(ctx)


@given("he has seen the entry screen without a trend line")
def step_saw_no_glance(composition, ctx):
    composition.glance.saw_no_line(ctx)


@given("the trend computation is failing")
def step_trend_computation_failing(composition, monkeypatch):
    composition.glance.break_computation(monkeypatch)


@given(parsers.parse("he starts each of the next {mornings:d} mornings at the entry screen"))
def step_seven_mornings(composition, mornings):
    composition.glance.deliver_mornings(mornings)


# ---------------------------------------------------------------- When


@when("he opens the entry screen, watch in hand")
def step_opens_entry_screen_timed(composition, ctx):
    ctx.response = composition.screen.open_entry_timed(ctx)


@when(parsers.parse("he studies the graph's trend view {times:d} times"))
def step_studies_trend(composition, times):
    composition.glance.study_trend(times)


# ---------------------------------------------------------------- Then


@then("the entry screen shows the trend at a glance")
def step_glance_shown(composition, ctx):
    composition.glance.assert_line_matches(ctx)


@then("no trend line is shown")
def step_no_glance_line(composition, ctx):
    composition.glance.assert_no_line(ctx)


@then("the trend value is shown at a glance")
def step_glance_value_shown(composition, ctx):
    composition.glance.assert_value_shown(ctx)


@then(parsers.parse('the glance line reads a trend of "{text}"'))
def step_glance_value_reads(composition, ctx, text):
    composition.glance.assert_value_fragment(ctx, text)


@then(parsers.parse('the glance line reads a weekly rate of "{text}"'))
def step_glance_rate_reads(composition, ctx, text):
    composition.glance.assert_rate_fragment(ctx, text)


@then(parsers.parse('the direction glyph reads "{glyph}"'))
def step_glyph_reads(composition, ctx, glyph):
    composition.glance.assert_glyph(ctx, glyph)


@then("the glance wears the same quiet styling in every direction")
def step_neutral_styling(composition, ctx):
    composition.glance.assert_neutral_styling(ctx)


# Closed vocabulary (RateDisposition values only), so this parser never shadows the
# exact-sentence step "the weekly rate is the line's own change over the last week".
@then(parsers.re(r"the weekly rate is (?P<disposition>held back|shown)$"))
def step_rate_disposition(composition, ctx, disposition):
    composition.glance.assert_rate_disposition(ctx, parse_rate_disposition(disposition))


@then("the trend and weekly rate are both shown at a glance")
def step_value_and_rate_shown(composition, ctx):
    composition.glance.assert_value_and_rate_shown(ctx)


@then("the glanced trend is where the graph's trend line ends")
def step_matches_graph_line_end(composition, ctx):
    composition.glance.assert_matches_graph_line_end(ctx)


@then("the weekly rate is the line's own change over the last week")
def step_rate_coheres_with_line(composition, ctx):
    composition.glance.assert_rate_is_trailing_week_change(ctx)


@then("the glance refreshes in place with the save")
def step_glance_refreshed(composition, ctx):
    composition.glance.assert_refreshed_by_save(ctx)


@then(parsers.parse("the glance appears with his first entry at {kg:g} kg and no weekly rate"))
def step_first_glance(composition, ctx, kg):
    composition.glance.assert_first_glance(ctx, kg)


@then("the glance delivery is on the record")
def step_delivery_recorded(composition, ctx):
    composition.glance.assert_delivery_recorded(ctx)


@then("the save carries no glance to show")
def step_no_glance_on_save(composition, ctx):
    composition.glance.assert_no_glance_on_save(ctx)


@then("no glance delivery is recorded for it")
def step_no_delivery_for_rejection(composition, ctx):
    composition.glance.assert_no_glance_for_rejection(ctx)


@then(parsers.parse("the glance was delivered {times:d} times"))
def step_delivered_times(composition, times):
    composition.glance.assert_delivered_times(times)


@then("the entry screen is ready within two seconds")
def step_screen_ready_within(composition, ctx):
    composition.screen.assert_ready_within(ctx, 2000)
