"""Step vocabulary: device-day frame on READ surfaces (fix-device-day-reads).

The phone's calendar day is canonical (A5) for reads too: at 02:00 UTC with
the phone still living the previous day, the yesterday anchor and the 1W
windows must keep the device frame. The oracle is NON-TAUTOLOGICAL: expected
days derive from the phone's declared day, never from the server clock.

Mandate-12: bodies are <=2 statements delegating to composition services.
"""

from __future__ import annotations

from domain_types import parse_day, parse_scale
from pytest_bdd import given, parsers, then, when

# ---------------------------------------------------------------- Given


@given(
    parsers.parse(
        "the UTC day has rolled over to {utc_day} while his phone is still in {device_day}"
    )
)
def step_evening_skew(composition, utc_day, device_day):
    composition.day_frame.evening_skew(parse_day(utc_day), parse_day(device_day))


# ---------------------------------------------------------------- When


@when(parsers.parse('he opens his history at "{scale}" as his phone frames the day'))
def step_history_device_framed(composition, ctx, scale):
    ctx.response = composition.day_frame.open_history(parse_scale(scale))


@when(parsers.parse('he opens the trend at "{scale}" as his phone frames the day'))
def step_trend_device_framed(composition, ctx, scale):
    composition.day_frame.open_trend(parse_scale(scale), ctx)


@when(parsers.parse('his phone asks for the {lens} week claiming the day is "{claimed_day}"'))
def step_claimed_day(composition, ctx, lens, claimed_day):
    ctx.response = composition.day_frame.ask_with_claimed_day(lens, claimed_day)


# ---------------------------------------------------------------- Then


@then(parsers.parse("the yesterday anchor names {day}'s {kg:g} kg"))
def step_anchor_names(composition, ctx, day, kg):
    composition.day_frame.assert_anchor_names(ctx, parse_day(day), kg)


@then(parsers.parse("the trend line spans exactly {start} to {end}"))
def step_trend_spans_exactly(composition, ctx, start, end):
    composition.day_frame.assert_trend_spans_exactly(ctx, parse_day(start), parse_day(end))


@then("the garbled day claim is politely turned away")
def step_garbled_day_refused(composition, ctx):
    composition.day_frame.assert_garbled_day_refused(ctx)
