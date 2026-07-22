"""Step vocabulary: history, trend, graph toggle, entry screen, speed report
(US-002, US-004, US-005, US-006).

Trend oracles are the DISTILL framings of ADR-004 (see also the pure-core
property suite in ../properties/): shift/step bounds, daily-grid coverage,
decline visibility, reload determinism. Gap oracle asserts smoothed continuity
of the CURRENT line -- never immutability of previously rendered values.
"""

from __future__ import annotations

from pytest_bdd import given, parsers, then, when

from domain_types import ViewMode, parse_day, parse_scale, parse_view

# ---------------------------------------------------------------- Given

@given(parsers.parse('he has noted the current trend at "{scale}"'))
def step_noted_trend(composition, ctx, scale):
    composition.trend.note(parse_scale(scale), ctx)


@given(parsers.parse('he is viewing the trend at "{scale}"'))
def step_viewing_trend(composition, ctx, scale):
    ctx.graph_scale = parse_scale(scale)
    ctx.response = composition.graph.open(ViewMode.TREND, ctx.graph_scale)


@given(parsers.parse('he toggled to the Raw view at "{scale}"'))
def step_toggled_raw(composition, ctx, scale):
    ctx.graph_scale = parse_scale(scale)
    ctx.response = composition.graph.open(ViewMode.RAW, ctx.graph_scale)


# ---------------------------------------------------------------- When

@when(parsers.parse('he opens his history at "{scale}"'))
def step_opens_history(composition, ctx, scale):
    ctx.response = composition.history.open_timed(parse_scale(scale), ctx)


@when(parsers.parse('he opens the trend at "{scale}"'))
def step_opens_trend(composition, ctx, scale):
    composition.trend.open(parse_scale(scale), ctx)


@when("he opens the graph")
def step_opens_graph(composition, ctx):
    ctx.response = composition.graph.open()


@when(parsers.parse("he switches the graph to {view}"))
def step_switches_graph(composition, ctx, view):
    ctx.response = composition.graph.switch(ctx, parse_view(view))


@when("he opens the entry screen")
def step_opens_entry_screen(composition, ctx):
    ctx.response = composition.screen.open_entry()


@when("he looks for the home-screen install option")
def step_looks_for_install(composition, ctx):
    ctx.response = composition.screen.open_manifest()


@when("he opens the speed report")
def step_opens_speed_report(composition, ctx):
    ctx.response = composition.stats.open_speed()


# ---------------------------------------------------------------- Then

@then(parsers.parse("only entries from {start} to {end} are shown"))
def step_only_between(composition, ctx, start, end):
    composition.history.assert_only_between(ctx, parse_day(start), parse_day(end))


@then(parsers.parse("his history spans {start} to {end}"))
def step_spans(composition, ctx, start, end):
    composition.history.assert_spans(ctx, parse_day(start), parse_day(end))


@then(parsers.parse("the days from {start} to {end} show no entries"))
def step_gap(composition, ctx, start, end):
    composition.history.assert_gap(ctx, parse_day(start), parse_day(end))


@then("he is invited to log his first weight")
def step_invited(composition, ctx):
    composition.history.assert_invite(ctx)


@then("exactly one entry is shown")
def step_exactly_one(composition, ctx):
    composition.history.assert_exactly_one(ctx)


@then("the history is ready within two seconds")
def step_ready_within(composition, ctx):
    composition.history.assert_ready_within(ctx, 2000)


@then(parsers.parse("the trend moves by no more than {kg:g} kg"))
def step_trend_max_shift(composition, ctx, kg):
    composition.trend.assert_max_shift(ctx, kg)


@then(parsers.parse("the trend line steps by no more than {kg:g} kg between consecutive days"))
def step_trend_max_step(composition, ctx, kg):
    composition.trend.assert_max_daily_step(ctx, kg)


@then(parsers.parse("the trend has a value for every day from {start} to {end}"))
def step_trend_covers(composition, ctx, start, end):
    composition.trend.assert_covers_every_day(ctx, parse_day(start), parse_day(end))


@then(parsers.parse("the trend shows the decline within {n:d} days of {day}"))
def step_trend_decline(composition, ctx, n, day):
    composition.trend.assert_decline_within(ctx, parse_day(day), n)


@then(parsers.parse("the trend no longer dips at {day}"))
def step_trend_no_dip(composition, ctx, day):
    composition.trend.assert_no_dip_at(ctx, parse_day(day))


@then(parsers.parse('every load shows the identical trend line at "{scale}"'))
def step_trend_deterministic(composition, ctx, scale):
    composition.trend.assert_identical_reloads(ctx)


@then(parsers.parse("the trend begins at {day}"))
def step_trend_begins(composition, ctx, day):
    composition.trend.assert_begins_at(ctx, parse_day(day))


@then(parsers.parse('the {view} view is shown at "{scale}"'))
def step_view_at(composition, ctx, view, scale):
    composition.graph.assert_view_at(ctx, parse_view(view), parse_scale(scale))


@then("the trend view is shown first")
def step_default_view(composition, ctx):
    composition.graph.assert_default_is_trend(ctx)


@then(parsers.parse("his trend views this week number {n:d}"))
def step_trend_views_count(composition, n):
    composition.stats.assert_trend_views_this_week(n)


@then("the entry screen is ready for immediate typing")
def step_ready_for_typing(composition, ctx):
    composition.screen.assert_ready_for_typing(ctx)


@then(parsers.parse("yesterday's {kg:g} kg is shown beside the input"))
def step_yesterday_reference(composition, ctx, kg):
    composition.screen.assert_yesterday(ctx, kg)


@then("no yesterday reference is shown")
def step_no_yesterday(composition, ctx):
    composition.screen.assert_no_yesterday(ctx)


@then("the tracker offers itself for the home screen")
def step_installable(composition, ctx):
    composition.screen.assert_installable(ctx)


@then("the speed report shows the week's median and worst-case entry times")
def step_speed_report(composition, ctx):
    composition.stats.assert_speed_report(ctx, ctx.timings)
