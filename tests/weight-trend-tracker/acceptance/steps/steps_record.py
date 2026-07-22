"""Step vocabulary: logging, validation, durability (US-001, US-003).

Record state machine (C2a):
    EMPTY --save(day,kg)--> DAY_HELD(day) --save(day,kg')--> DAY_HELD(day)   [replace, never duplicate]
    any state --save(rejected input)--> unchanged                            [range/precision/date guards]
    any state --save while LOCKED--> unchanged                               [AccessGate]
    any state --restart--> same state                                        [durability]
Illegal events covered per state: rejected input from EMPTY and DAY_HELD,
future/unparseable dates, save-while-locked, startup-on-broken-store.

Mandate-12: bodies are <=2 statements delegating to composition services.
"""

from __future__ import annotations

from pytest_bdd import given, parsers, then, when

from domain_types import parse_day, parse_reason

# ---------------------------------------------------------------- Given

@given("the tracker is running with an empty record")
def step_empty_record(composition):
    composition.system.ensure_fresh()


@given(parsers.parse("today is {day}"))
def step_today_is(composition, day):
    composition.clock.set_today(parse_day(day))


@given(parsers.parse("his phone is already in {day}"))
def step_device_day(composition, day):
    composition.clock.set_device_day(parse_day(day))


@given(parsers.parse("he has already logged {kg:g} kg for today"))
def step_already_logged_today(composition, kg):
    composition.logging.seed(composition.resolve_day("today"), kg)


@given(parsers.parse("he logged {kg:g} kg on {day}"))
def step_logged_on(composition, kg, day):
    composition.logging.seed(parse_day(day), kg)


@given(parsers.parse("yesterday he logged {kg:g} kg"))
def step_logged_yesterday(composition, kg):
    composition.logging.seed(composition.resolve_day("yesterday"), kg)


@given(parsers.parse("his record has no entry for {day}"))
def step_no_entry_for(composition, day):
    composition.logging.assert_absent(parse_day(day))


@given(parsers.parse("his record holds a steady {kg:g} kg from {start} to {end}"))
def step_steady_range(composition, kg, start, end):
    composition.logging.seed_steady(kg, parse_day(start), parse_day(end))


@given(parsers.parse("his record holds an entry for every day from {start} to {end}"))
def step_daily_range(composition, start, end):
    composition.logging.seed_daily(parse_day(start), parse_day(end))


@given(parsers.parse("his entries fall by half a kilogram each week from {start} to {end}"))
def step_weekly_decline(composition, start, end):
    composition.logging.seed_weekly_decline(82.3, 0.5, parse_day(start), parse_day(end))


@given("he has logged timed entries every morning for the last week")
def step_timed_week(composition, ctx):
    ctx.timings = composition.logging.seed_timed_week(composition.resolve_day("today"))


@given("the record's home cannot be written to")
def step_home_unwritable(composition):
    composition.system.make_home_unwritable()


# ---------------------------------------------------------------- When

@when(parsers.parse('he logs "{raw}" for {day_spec}'))
def step_logs_for(composition, ctx, raw, day_spec):
    ctx.before, ctx.raw_input = composition.capture_universe(), raw
    ctx.response = composition.logging.record(day_spec, raw)


@when(parsers.parse('the next morning he logs "{raw}"'))
def step_logs_next_morning(composition, ctx, raw):
    ctx.response = composition.logging.record_next_morning(ctx, raw)


@when("he submits an empty weight for today")
def step_submits_empty(composition, ctx):
    ctx.before, ctx.raw_input = composition.capture_universe(), ""
    ctx.response = composition.logging.record("today", "")


@when("he submits a weight for an unrecognisable date")
def step_submits_bad_date(composition, ctx):
    ctx.before = composition.capture_universe()
    ctx.response = composition.logging.record_raw_date("someday-soon", "82.4")


@when(parsers.parse("he corrects {day} to {kg:g} kg"))
def step_corrects(composition, ctx, day, kg):
    ctx.before = composition.capture_universe()
    ctx.response = composition.logging.record(day, f"{kg:.1f}")


@when("the tracker is restarted")
def step_restarted(composition):
    composition.system.restart()


@when("the tracker starts")
def step_starts(composition, ctx):
    composition.system.try_start(ctx)


# ---------------------------------------------------------------- Then

@then(parsers.parse('he sees the confirmation "{text}"'))
def step_sees_confirmation(composition, ctx, text):
    composition.logging.assert_confirmation(ctx, text)


@then(parsers.parse("{day_spec} holds exactly one entry of {kg:g} kg"))
def step_day_holds(composition, ctx, day_spec, kg):
    composition.logging.assert_day_holds(ctx, day_spec, kg)


@then(parsers.parse("today's entry of {kg:g} kg appears at the top of his history"))
def step_top_of_history(composition, kg):
    composition.logging.assert_top_of_history("today", kg)


@then(parsers.parse("the save is rejected because {phrase}"))
def step_rejected_because(composition, ctx, phrase):
    composition.logging.assert_rejected(ctx, parse_reason(phrase))


@then("nothing is stored")
@then("his record is unchanged")
def step_nothing_stored(composition, ctx):
    composition.logging.assert_nothing_stored(ctx)


@then("the record is exactly as before")
def step_record_preserved(composition, ctx):
    composition.logging.assert_record_preserved(ctx)


@then("his typed value is kept for correction")
def step_input_kept(composition, ctx):
    composition.logging.assert_input_kept(ctx)
