"""Step vocabulary: the graph-first front page -- ambient curve, recent-7 list,
intent telemetry (US-010, US-011, ADR-008/ADR-009).

Front-page state machine (C2a), an ambient surface over the entry record:
    SIMPLE (0 entries: no graph area, no recent list)
        --first save--> PICTURED (mount + curve data + list)
    PICTURED --save--> PICTURED' [repaint in place: `recent` on the save
                                  response; series refetched at the current
                                  lens/scale -- both ambient, A15/D-19]
    PICTURED --series failure--> AREA_ABSENT [entry + save untouched, D-15]
    any ambient render/refetch --> deliberate study +0, home delivery +1 (A19)
    explicit lens/scale tap --beacon--> deliberate study +1 (closed vocabulary)
    garbled/stranger beacon --> refused (400 / door), trail untouched

Degenerate events covered: series failure mid-morning (render and save), empty
record, garbled beacon vocabulary, beacon without a session, focus theft (Q4).

Mandate-12: bodies are <=2 statements delegating to composition services.
"""

from __future__ import annotations

from domain_types import parse_day, parse_scale
from pytest_bdd import given, parsers, then, when

# ---------------------------------------------------------------- Given


@given("he has opened the entry screen")
def step_has_opened_entry(composition, ctx):
    ctx.response = composition.screen.open_entry()


@given("he has seen the morning picture end at yesterday")
def step_seen_series_end(composition, ctx):
    composition.home_graph.note_series_end(ctx)


@given("the trend series cannot be computed")
def step_series_broken(composition, monkeypatch):
    composition.home_graph.break_series(monkeypatch)


@given(parsers.parse('the entry screen\'s recent list begins with "{text}"'))
def step_recent_begins_given(composition, ctx, text):
    composition.recent_list.screen_begins_with(ctx, text)


# ---------------------------------------------------------------- When


MORNING_PHRASE = 'he opens on the morning picture, logs "{raw}" for today and pockets the phone'


@when(parsers.parse(MORNING_PHRASE))
def step_log_only_morning(composition, ctx, raw):
    composition.study.log_only_morning(ctx, raw)


@when(parsers.parse('he chooses the "{window}" window and then the Raw lens on the front page'))
def step_choose_window_then_raw(composition, ctx, window):
    composition.study.choose_scale_then_raw(ctx, window)


@when("a study signal arrives speaking words the tracker does not know")
def step_garbled_signal(composition, ctx):
    composition.study.send_garbled(ctx)


@when("a stranger sends a study signal without the passphrase")
def step_stranger_signal(composition, ctx):
    composition.study.stranger_taps(ctx)


# ---------------------------------------------------------------- Then


@then("the trend curve greets him above the entry form")
def step_curve_above_form(composition, ctx):
    composition.home_graph.assert_curve_above_form(ctx)


@then("the front-page graph offers both lenses and every time scale")
@then("the graph page offers both lenses and every time scale")
def step_full_controls(composition, ctx):
    composition.home_graph.assert_full_controls(ctx)


@then(parsers.parse('the front-page graph opens on the Trend lens at "{scale}"'))
def step_opens_at_defaults(composition, ctx, scale):
    composition.home_graph.assert_opens_at_defaults(ctx, parse_scale(scale))


@then("the front page drives the same graph engine as the History page")
def step_shared_engine(composition, ctx):
    composition.home_graph.assert_shared_engine(ctx)


@then(parsers.parse("the deliberate trend-study count for this week is {expected:d}"))
def step_deliberate_count(composition, expected):
    composition.study.assert_deliberate(expected)


@then("the morning graph delivery is on the record")
@then("the morning graph delivery is still on the record")
def step_ambient_delivery(composition):
    composition.study.assert_ambient_delivery()


@then("both taps are counted as deliberate study")
def step_taps_counted(composition, ctx):
    composition.study.assert_taps_counted(ctx, 2)


@then("the save hands back the refreshed recent list with today on top")
def step_save_recent_top(composition, ctx):
    composition.recent_list.assert_save_response_top(ctx)


@then("the refreshed morning picture includes today")
def step_series_includes_today(composition, ctx):
    composition.home_graph.assert_series_includes_today(ctx)


@then("the repaint added nothing to the deliberate trend-study count")
def step_repaint_stays_ambient(composition):
    composition.study.assert_deliberate(0)


@then("the morning picture admits its trouble without marking the record")
def step_series_trouble_harmless(composition, ctx):
    composition.home_graph.series_read_admits_trouble(ctx)


@then("no graph area is offered")
def step_no_graph_area(composition, ctx):
    composition.home_graph.assert_absent(ctx)


@then("nothing about the graph steals the morning focus")
def step_no_focus_theft(composition, ctx):
    composition.home_graph.assert_no_focus_theft(ctx)


@then("no recent list is offered")
def step_no_recent_list(composition, ctx):
    composition.recent_list.assert_none(ctx)


@then("the recent list shows his last 7 entries newest first")
def step_recent_last_seven(composition, ctx):
    composition.recent_list.assert_last_seven(ctx)


@then(parsers.parse('the recent list begins with "{text}"'))
def step_recent_begins(composition, ctx, text):
    composition.recent_list.assert_begins_with(ctx, text)


@then(parsers.parse("{day} appears nowhere in the recent list"))
def step_recent_day_absent(composition, ctx, day):
    composition.recent_list.assert_day_absent(ctx, parse_day(day))


@then(parsers.parse("the recent list shows exactly those {count:d} entries"))
def step_recent_exactly(composition, ctx, count):
    composition.recent_list.assert_exactly(ctx, count)


@then("the recent list offers no way to edit or delete")
def step_recent_display_only(composition, ctx):
    composition.recent_list.assert_display_only(ctx)


@then("every recent value equals the stored entry for its day")
def step_recent_matches_store(composition, ctx):
    composition.recent_list.assert_values_match_store(ctx)


@then("the signal is refused as unintelligible, never as a breakdown")
def step_signal_refused(composition, ctx):
    composition.study.assert_refused_unintelligible(ctx)


@then("no deliberate study is recorded for it")
def step_no_study_mark(composition, ctx):
    composition.study.assert_no_study_mark(ctx)


@then("the stranger is turned away at the door")
def step_stranger_turned_away(composition, ctx):
    composition.study.assert_stranger_turned_away(ctx)
