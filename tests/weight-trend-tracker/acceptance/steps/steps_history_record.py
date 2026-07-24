"""Step vocabulary: the combined History page -- full-control graph + complete
record (US-012, D-17/D-18, ADR-009).

History-page state machine (C2a), the deliberate surface over the same record:
    EMPTY (0 entries) --open--> INVITE (empty-invite, no list; study counted)
    RECORDED --open--> AUDITABLE [graph on top, COMPLETE list beneath, newest
                                  first; one trend.study.opened per open]
    AUDITABLE --lens/scale toggle--> AUDITABLE [scale preserved (US-005 rule);
                                                the list never windows (D-17)]
    deep link ?view=/?scale= --> AUDITABLE at that lens/scale (A16)

Degenerate events covered: empty record, gap days (absent from list AND plot),
old bookmarks, >=300-entry load (G-2 extended).

Mandate-12: bodies are <=2 statements delegating to composition services.
"""

from __future__ import annotations

from domain_types import ViewMode, parse_day, parse_scale
from pytest_bdd import given, parsers, then, when

# ---------------------------------------------------------------- Given


@given("he has studied the History page once this week")
def step_studied_once(composition):
    composition.graph.open()


# ---------------------------------------------------------------- When


@when(parsers.parse('he studies the Raw record at "{scale}"'))
def step_raw_record_at(composition, ctx, scale):
    ctx.graph_scale = parse_scale(scale)
    ctx.response = composition.graph.open(ViewMode.RAW, ctx.graph_scale)


@when("he follows his old bookmark to the Raw year view")
def step_old_bookmark(composition, ctx):
    ctx.graph_scale = parse_scale("1Y")
    ctx.response = composition.graph.open(ViewMode.RAW, ctx.graph_scale)


@when("he opens the History page, watch in hand")
def step_open_history_timed(composition, ctx):
    ctx.response = composition.history_record.open_timed(ctx)


# ---------------------------------------------------------------- Then


@then("the complete record is listed beneath the graph, newest first")
def step_complete_list(composition, ctx):
    composition.history_record.assert_complete_newest_first(ctx)


@then(parsers.parse("every day from {start} to {end} appears nowhere in the complete list"))
def step_complete_gap_absent(composition, ctx, start, end):
    composition.history_record.assert_days_absent(ctx, parse_day(start), parse_day(end))


@then("the complete list carries exactly the entries the raw plot draws")
def step_list_matches_plot(composition, ctx):
    composition.history_record.assert_matches_raw_plot(ctx)


@then("the way back to today's entry is one tap away")
def step_back_link(composition, ctx):
    composition.history_record.assert_back_link(ctx)


@then("no complete list is rendered")
def step_no_complete_list(composition, ctx):
    composition.history_record.assert_none(ctx)


@then("the first-log invite is still offered")
def step_invite_offered(composition, ctx):
    composition.history_record.assert_invite_offered(ctx)


@then("the empty visit still counts as one deliberate study")
def step_empty_visit_counted(composition):
    composition.study.assert_deliberate(1)


@then("the History page is ready within two seconds")
def step_history_ready_within(composition, ctx):
    composition.history_record.assert_ready_within(ctx, 2000)
