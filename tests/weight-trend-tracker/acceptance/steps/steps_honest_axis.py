"""Step vocabulary: the honest y-axis (US-015, ADR-012).

Not a state machine (C2a): the axis is a PURE PROJECTION of the values a lens
plots for a window -- two branches on one number, the plotted span:

    span < 2.0 kg  -->  [mid - 1.0, mid + 1.0]            (floor: widen, never clip)
    span >= 2.0 kg -->  [min - 0.1*span, max + 0.1*span]  (ordinary range, explicit)
    then both bounds snap OUTWARD to the 0.5 kg grid; nothing plotted --> no axis.

Degenerate windows covered: a single entry, an all-equal week, a missing day
under the band, an empty window on a non-empty record, an empty record, an
awkward midpoint, and the branch boundary at exactly 2.0 kg of movement.
Reads stay pure (KPI-3, ADR-009) and the series never moves (G-3).

Layer 3 (real HTTP + real SQLite): every @property scenario here is
EXAMPLE-PINNED (Mandates 9/11); the generative property over the pure rule is
DELIVER's paired PBT against `core/axis.py` (ADR-025).

Mandate-12: bodies are <=2 statements delegating to composition services.
"""

from __future__ import annotations

from domain_types import parse_day, parse_kg_list, parse_scale, parse_view
from pytest_bdd import given, parsers, then, when

# ---------------------------------------------------------------- Given


@given(parsers.parse("his weight has hovered around {kg:g} kg from {start} to {end}"))
def step_plateau(composition, kg, start, end):
    composition.logging.seed_plateau(kg, parse_day(start), parse_day(end))


@given(
    parsers.parse(
        "his entries fall by {rate:g} kg each week from {kg:g} kg between {start} and {end}"
    )
)
def step_decline_at_rate(composition, rate, kg, start, end):
    composition.logging.seed_weekly_decline(kg, rate, parse_day(start), parse_day(end))


@given(parsers.parse("his last seven mornings read {values} kg"))
def step_last_seven_mornings(composition, values):
    composition.logging.seed_mornings(parse_kg_list(values), composition.resolve_day("today"))


# ---------------------------------------------------------------- When


@when(parsers.parse('he views the {lens} lens at "{scale}"'))
def step_views_lens(composition, ctx, lens, scale):
    composition.axis.view(parse_view(lens), parse_scale(scale), ctx)


@when("he taps through every lens at every scale")
def step_tour(composition, ctx):
    composition.axis.tour(ctx)


# ---------------------------------------------------------------- Then


@then(parsers.parse("the axis runs from {lo:g} to {hi:g}"))
def step_axis_runs(composition, ctx, lo, hi):
    composition.axis.assert_band(ctx, lo, hi)


@then("the axis is at least two kilograms tall with every plotted point inside")
def step_floor_and_containment(composition, ctx):
    composition.axis.assert_floor_and_containment(ctx)


@then("the axis is the honest range for what is plotted")
def step_honest(composition, ctx):
    composition.axis.assert_honest(ctx)


@then(parsers.parse("the plotted line fills at most {percent:d} % of the axis"))
def step_line_at_most(composition, ctx, percent):
    composition.axis.assert_line_share_at_most(ctx, percent)


@then(parsers.parse("the plotted line covers at least {percent:d} % of the axis"))
def step_line_at_least(composition, ctx, percent):
    composition.axis.assert_line_share_at_least(ctx, percent)


@then(parsers.parse("the axis is between {lo_w:g} and {hi_w:g} kg tall"))
def step_width_between(composition, ctx, lo_w, hi_w):
    composition.axis.assert_width_between(ctx, lo_w, hi_w)


@then(parsers.parse("the axis is centred within {tolerance:g} kg of the data midpoint"))
def step_centred_within(composition, ctx, tolerance):
    composition.axis.assert_centre_within(ctx, tolerance)


@then(
    "the axis is the plotted range padded by a tenth each side, "
    "snapped outward to the half-kilogram grid"
)
def step_auto_branch(composition, ctx):
    composition.axis.assert_auto_branch(ctx)


@then("every bound is a clean multiple of half a kilogram")
def step_clean_bounds(composition, ctx):
    composition.axis.assert_clean_bounds(ctx)


@then(parsers.parse("the axis is exactly {width:g} kg tall, centred on {centre:g}"))
def step_exact_width_centred(composition, ctx, width, centre):
    composition.axis.assert_exact_width_centred(ctx, width, centre)


@then(parsers.parse('no axis is offered in either lens at "{scale}"'))
def step_none_either_lens(composition, scale):
    composition.axis.assert_none_either_lens(parse_scale(scale))


@then("every axis on the tour obeys the one honest rule")
def step_tour_honest(composition, ctx):
    composition.axis.assert_tour_honest(ctx)


@then("every tap keeps its chosen lens and scale")
def step_tour_keeps_selection(composition, ctx):
    composition.axis.assert_tour_keeps_selection(ctx)


@then("the plotted line is exactly the line the record has always told")
def step_series_untouched(composition, ctx):
    composition.axis.assert_series_untouched(ctx)
