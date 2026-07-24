"""Step vocabulary: the calm visual theme -- one look for every screen, in any
light (US-008, US-009, ADR-007).

Theme state machine (C2a): the theme itself is stateless presentation -- its
mutation universe is EMPTY by design (DESIGN: no new ports, no I/O). What the
scenarios model instead is DELIVERY and DEGRADATION:

    DRESSED (asset served, pages linked) --asset goes missing--> BARE
    BARE: every flow still works end-to-end (progressive enhancement; the
          morning is never blocked by its clothes)
    DRESSED in daylight <--system scheme--> DRESSED in dim light
          (appearance changes; behavior byte-for-byte identical, D7)

The record/access/glance state machines are INHERITED UNCHANGED from
milestones 1-6 (zero behavior change is this feature's headline requirement);
their steps are reused verbatim in the flow-untouched scenarios.

Degenerate events covered: rejected input on the themed screen, wrong
passphrase at the themed door, asset missing mid-morning, dim-light palette
silently falling back to daylight (the 06:45 flashbang, DISCUSS failure mode).

Scheme-flip MID-SESSION (US-009 third scenario) cannot be exercised through
the HTTP driving port (no browser): covered structurally here (single-source
palette + pressed/scheme rules in the one asset) and verified as a DELIVER
dogfood check -- see feature-delta § Wave: DISTILL.

Mandate-12: bodies are <=2 statements delegating to composition services.
"""

from __future__ import annotations

from domain_types import ContrastClass, parse_screen
from pytest_bdd import given, parsers, then, when

# ---------------------------------------------------------------- Given

SCREEN_PHRASE = r"the (?P<screen>entry screen|door|graph page) wears the calm theme"


@given(parsers.re(SCREEN_PHRASE))
@then(parsers.re(SCREEN_PHRASE))
def step_screen_wears_theme(composition, ctx, screen):
    composition.theme.assert_screen_wears_theme(ctx, parse_screen(screen))


@given("the tracker wears the calm theme")
def step_tracker_wears_theme(composition, ctx):
    composition.theme.fetch_delivered(ctx)


@given("the theme has gone missing")
def step_theme_gone_missing(composition, monkeypatch):
    composition.theme.break_delivery(monkeypatch)


# ---------------------------------------------------------------- When


@when("its daylight and dim-light appearances are examined")
def step_examine_appearances(composition, ctx):
    composition.theme.examine_appearances(ctx)


@when("the cost of the new look is tallied")
def step_tally_cost(composition, ctx):
    composition.theme.tally_cost(ctx)


# ---------------------------------------------------------------- Then


@then("the calm look is delivered by the tracker itself")
def step_theme_delivered(composition, ctx):
    composition.theme.fetch_delivered(ctx)


@then("it is dressed for daylight and for dim light alike")
def step_dressed_for_both(composition, ctx):
    composition.theme.assert_dressed_for_both_lights(ctx)


@then("every piece of text stands clearly against its surface")
def step_text_contrast(composition, ctx):
    composition.theme.assert_contrast_class_holds(ctx, ContrastClass.TEXT)


@then("every edge, line and stroke stands apart from its surface")
def step_non_text_contrast(composition, ctx):
    composition.theme.assert_contrast_class_holds(ctx, ContrastClass.NON_TEXT)


@then("the dim-light appearance answers for every color the daylight one names")
def step_dim_light_parity(composition, ctx):
    composition.theme.assert_dim_light_answers_daylight(ctx)


@then(parsers.parse("the whole look weighs no more than {kilobytes:d} kilobytes"))
def step_budget_kept(composition, ctx, kilobytes):
    composition.theme.assert_budget_kept(ctx, kilobytes)


@then("no screen reaches beyond the tracker's own walls")
def step_self_contained(composition, ctx):
    composition.theme.assert_self_contained(ctx)


@then("the morning screen carries no new moving parts")
def step_no_new_moving_parts(composition, ctx):
    composition.theme.assert_no_new_entry_moving_parts(ctx)


@then("every control promises a comfortable touch target")
def step_touch_comfort(composition, ctx):
    composition.theme.assert_touch_comfort_promised(ctx)


@then("the pressed control is marked by more than color alone")
def step_pressed_beyond_color(composition, ctx):
    composition.theme.assert_pressed_beyond_color(ctx)


@then("the chart draws every line from the tracker's single palette")
def step_chart_single_palette(composition, ctx):
    composition.theme.assert_chart_single_palette(ctx)


@then("the morning screen still opens ready for typing")
def step_morning_still_ready(composition, ctx):
    composition.theme.assert_morning_still_ready(ctx)
