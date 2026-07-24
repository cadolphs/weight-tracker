"""Step vocabulary: the dated entry row -- backfill, correct, and the purity of
the morning record (US-013, US-014, ADR-010 + ADR-011).

Entry-screen state machine (C2a), a repair surface over the same one-per-day record:

    TODAY (date row on the phone's own day, anchor hint)
        --pick a stored day--> EDITING(day)   [stored value offered back + editing hint]
        --pick an empty day--> BACKFILLING(day) [nothing offered + no-entry hint]
    EDITING/BACKFILLING --save--> TODAY'  [one entry for that day; date resets to today;
                                           picture (glance + recent + curve) refreshed in place]
    any state --save dated != claimed day--> REPAIR   [entry_ms withheld: 0 speed samples,
                                                       +1 repair count]
    any state --save dated == claimed day--> MORNING  [+1 speed sample, +0 repairs]
    any state --save dated in the future--> unchanged [server no-future rule, trail untouched]
    absent/garbled day claim --> server's UTC day frames the judgement, save NEVER refused

Degenerate events covered: a gap offered as a gap (no blind overwrite), a March
day read in July (whole-record map), an empty record (nothing to correct, entry
still ready), a forged future date, a phone that will not name its day, and a
correction landing on a day whose morning was already timed (the trail keeps it).

Mandate-12: bodies are <=2 statements delegating to composition services.
"""

from __future__ import annotations

from domain_types import parse_claim, parse_day
from pytest_bdd import parsers, then, when

# ---------------------------------------------------------------- When


@when(parsers.parse('he backfills "{raw}" for {day}'))
def step_backfills(composition, ctx, raw, day):
    composition.dated_entry.remember(ctx)
    ctx.response = composition.logging.backfill(parse_day(day), raw)


@when(parsers.parse('he takes {entry_ms:d} ms to backfill "{raw}" for {day}'))
def step_backfills_slowly(composition, ctx, entry_ms, raw, day):
    composition.dated_entry.remember(ctx)
    ctx.response = composition.logging.backfill(parse_day(day), raw, entry_ms=entry_ms)


@when(parsers.parse('he takes {entry_ms:d} ms to log "{raw}" for today'))
def step_logs_today_timed(composition, ctx, entry_ms, raw):
    composition.dated_entry.remember(ctx)
    ctx.response = composition.logging.log_today(raw, entry_ms=entry_ms)


@when(parsers.parse("he corrects {day} to {kg:g} kg from the date row"))
def step_corrects_from_date_row(composition, ctx, day, kg):
    composition.dated_entry.remember(ctx)
    ctx.response = composition.logging.correct(parse_day(day), kg)


@when(parsers.parse('a save of "{raw}" for {day} arrives {claim}'))
def step_save_arrives_with_claim(composition, ctx, raw, day, claim):
    composition.dated_entry.remember(ctx)
    ctx.response = composition.logging.save_with_claim(parse_day(day), raw, parse_claim(claim))


# ---------------------------------------------------------------- Then (the served row)


@then("the date row rests above the weight field")
def step_date_row_above_field(composition, ctx):
    composition.dated_entry.assert_row_above_field(ctx)


@then("nothing about the date row steals the morning focus")
def step_date_row_no_focus_theft(composition, ctx):
    composition.dated_entry.assert_no_focus_theft(ctx)


@then(parsers.parse("the date row reaches back no further than {day}"))
def step_date_row_earliest(composition, ctx, day):
    composition.dated_entry.assert_reaches_back_to(ctx, parse_day(day))


# ---------------------------------------------------------------- Then (what a day offers)


@then(parsers.parse("{day} offers its stored {kg:g} kg back for correction"))
def step_day_offers_value(composition, ctx, day, kg):
    composition.dated_entry.assert_offers(ctx, parse_day(day), kg)


@then("every day of the record offers its stored weight back")
def step_whole_record_offered(composition, ctx):
    composition.dated_entry.assert_offers_whole_record(ctx)


@then(parsers.parse("{day} offers nothing to correct"))
def step_day_offers_nothing(composition, ctx, day):
    composition.dated_entry.assert_offers_nothing_for(ctx, parse_day(day))


@then("nothing of the record is offered to correct")
def step_nothing_offered(composition, ctx):
    composition.dated_entry.assert_nothing_to_correct(ctx)


# ---------------------------------------------------------------- Then (the one hint line)


@then("the screen carries exactly one hint line")
def step_single_hint_line(composition, ctx):
    composition.dated_entry.assert_single_hint_line(ctx)


@then("the hint names its day in the record's own grammar")
def step_hint_grammar(composition, ctx):
    composition.dated_entry.assert_hint_speaks_record_grammar(ctx)


# ---------------------------------------------------------------- Then (the repaired picture)


@then(parsers.parse('the refreshed picture the save hands back holds "{row_text}"'))
def step_handed_back_row(composition, ctx, row_text):
    composition.dated_entry.assert_handed_back(ctx, row_text)


@then(parsers.parse("the trend recomputes over the repaired record including {day}"))
def step_trend_reflects(composition, ctx, day):
    composition.dated_entry.assert_trend_reflects(parse_day(day))


# ---------------------------------------------------------------- Then (KPI-1 purity, KPI-8)


@then("the week's morning-speed record still holds the same mornings")
def step_mornings_unchanged(composition, ctx):
    composition.dated_entry.assert_mornings_unchanged(ctx)


@then("the week's morning-speed record gains that morning")
def step_morning_counted(composition, ctx):
    composition.dated_entry.assert_morning_counted(ctx)


@then("the repair is counted on the stats page")
def step_repair_counted(composition, ctx):
    composition.dated_entry.assert_repair_counted(ctx)


@then("no repair is counted for it")
def step_no_repair_counted(composition, ctx):
    composition.dated_entry.assert_no_repair_counted(ctx)


@then("neither the morning-speed record nor the repair count moves")
def step_trail_untouched(composition, ctx):
    composition.dated_entry.assert_trail_untouched(ctx)
