"""The one hint line, the submitted payload and the post-save reset, as they
SHIP inside the entry screen's single inline script (US-014, D-24/A21/A22).

WHY-NEW-FILE: acceptance/properties/test_entry_hint_wiring.py
  CLOSEST-EXISTING: acceptance/properties/test_date_row_bound_properties.py
  EXTENSION-COST: that module's whole contract -- docstring, strategies, and every
    property but one -- is the pure `date_row_earliest_day` calendar bound over a
    newest-first record; its single client pin exists only because the bound it
    proves is rendered as an attribute of the same row. Folding an eight-pin
    hint/payload/reset suite in would leave a Hypothesis module whose majority is
    markup assertions and whose name names none of them.
  PARALLEL-RATIONALE: these pins have a different subject (the inline script's own
    wiring), a different oracle (the served template text, read once), and a
    different obligation (they are the honest stand-in for a browser and are owed
    a dogfood pass), so they belong in a file whose docstring can say exactly that
    rather than being appended to a module that promises calendar properties.

WHAT THESE PINS PROVE, AND WHAT THEY DO NOT
-------------------------------------------
They prove the WIRING SHIPS: that the served entry screen contains one hint node,
one pure `hintFor` answering three mutually exclusive states in the pinned
wordings, one shared `dayLabel` grammar, a submit body carrying both the picked
date and the phone's own `today`, a post-save reset back to today, and a merge of
the save's answer into the client's map.

They do NOT prove a browser EXECUTES it. This repository ships no JS test harness
-- no package.json, no browser driver -- and gains none for this step (G-5: at
most one inline script, zero new origins, no new dependency). A behavioural pin
here is owed to a browser, not to pytest, and is discharged at dogfood, exactly as
for the date row's own `value`/`max` framing (client-paint precedent D-15,
DELIVER pre-requisite 2).

The PURE logic the hint and the payload consume is property-tested elsewhere and
is not restated here: `bounded_day_frame` / `is_backdated` (test_day_frame_
properties.py) decide what a `today` claim means once it arrives, and the
whole-record `{iso_day: kg}` projection (test_prefill_map_properties.py) is the
map `hintFor` reads. What is left over is genuinely golden text and event order.

Contract shape: pure-function (return-only reads of one template file); universe
empty -- no state-delta matcher applies (documented bypass: pure-function /
no-side-effect code).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import weight_tracker.web.routes as routes

pytestmark = [pytest.mark.us_014]

ENTRY_TEMPLATE = Path(routes.__file__).parent / "templates" / "index.html"
MARKUP = ENTRY_TEMPLATE.read_text(encoding="utf-8")

HINT_NODE = re.compile(r'<[a-z]+[^>]*id="entry-hint"[^>]*>')
#: The submit body, from `body: JSON.stringify({` to its closing brace.
SUBMIT_BODY = re.compile(r"body:\s*JSON\.stringify\(\{(.*?)\n\s*\}\)", re.DOTALL)
#: The success branch of the save flow: everything the screen does once a save
#: has been accepted, in the order it does it.
SAVED_BRANCH = re.compile(
    r'if \(outcome\.outcome === "saved"\) \{(.*?)\n      \} else \{', re.DOTALL
)


def saved_branch() -> str:
    branch = SAVED_BRANCH.search(MARKUP)
    assert branch, "the inline script must still branch on an accepted save"
    return branch.group(1)


# ---------------------------------------------------------------- one node, never removed


def test_the_screen_carries_exactly_one_hint_node_and_no_retired_anchor():
    assert len(HINT_NODE.findall(MARKUP)) == 1, (
        "'never two hints at once' is structural, not conventional: the template "
        "ships exactly ONE #entry-hint node (D-24)"
    )
    assert "yesterday-reference" not in MARKUP, (
        "the yesterday anchor is absorbed INTO the one hint line, never kept beside it"
    )


def test_the_hint_node_is_never_removed_from_the_page():
    """The old anchor removed itself when it had nothing to say, which is what
    made a second hint node thinkable and what let the form reflow mid-session.
    The one line stays put and falls silent instead."""
    assert "entryHint.remove()" not in MARKUP, (
        "the one hint line is never removed -- an empty line still holds its "
        "height, so the form never jumps under the thumb (D-25 no-reflow)"
    )
    assert re.search(r"entryHint\.textContent\s*=", MARKUP), (
        "the hint's text is written at ONE apply site (FC/IS in the client, ADR-005)"
    )


# ---------------------------------------------------------------- three states, pinned wordings


def test_the_hint_answers_three_mutually_exclusive_states():
    assert re.search(r"function hintFor\(selectedDay, deviceToday, weightsByDay\)", MARKUP), (
        "the hint's three states come from ONE pure function of the picked day, "
        "the device's own day and the record -- everything it needs is an argument"
    )
    assert "`yesterday: ${" in MARKUP, (
        "the anchor's wording is unchanged: the shipped scenarios read `yesterday: {v} kg` verbatim"
    )
    assert "`Editing ${dayLabel(selectedDay)} — was ${" in MARKUP, (
        "a picked day the record holds offers its value back: `Editing {day} — was {v} kg` (OQ-10)"
    )
    assert "`No entry for ${dayLabel(selectedDay)} yet`" in MARKUP, (
        "a picked day the record lacks is admitted as a gap: `No entry for {day} yet` (OQ-10)"
    )


def test_the_hint_reads_no_clock_and_no_dom_of_its_own():
    """`hintFor` is pure or it is not a hint contract: a `new Date()` or a
    `getElementById` inside it would make the three states untestable and would
    let the anchor drift from the picker it sits under."""
    body = re.search(r"function hintFor\(.*?\n    \}", MARKUP, re.DOTALL)
    assert body, "the pure hint function must be findable to be judged"
    assert "new Date(" not in body.group(0), (
        "the device's day is an ARGUMENT to the hint, never read inside it"
    )
    assert "document." not in body.group(0), "the hint reads no DOM: inputs in, a line out"


# ---------------------------------------------------------------- one calendar grammar


def test_the_hint_and_the_record_rows_share_one_day_grammar():
    assert re.search(r"function dayLabel\(isoDay\)", MARKUP), (
        "the `Fri 24 Jul` day half is ONE named function (D-24)"
    )
    assert re.search(
        r"function entryRowText\(isoDate, weightKg\) \{\s*\n\s*return `\$\{dayLabel\(", MARKUP
    ), (
        "the record's own rows are built FROM dayLabel, so the hint and the rows "
        "cannot fork into two calendar wordings -- the server speaks the same one"
    )
    assert MARKUP.count("const WEEKDAYS") == 1 and MARKUP.count("const MONTHS") == 1, (
        "one weekday table and one month table on the page: a second copy is how two wordings start"
    )


# ---------------------------------------------------------------- the submitted payload


def test_the_submitted_payload_carries_the_picked_date_and_the_devices_own_today():
    """ADR-011's purity rule is falsifiable only because BOTH days arrive on the
    wire: a rule resting on the client omitting entry_ms could never be checked
    by a browser-less suite composing its own payloads."""
    body = SUBMIT_BODY.search(MARKUP)
    assert body, "the save must still post a JSON body"
    assert re.search(r"date:\s*dateInput\.value \|\| deviceLocalDay\(\)", body.group(1)), (
        "the day SAVED is the picked one -- today unless the row was moved"
    )
    assert re.search(r"today:\s*deviceLocalDay\(\)", body.group(1)), (
        "the day the phone believes it IS travels beside it, so the server can "
        "classify morning-vs-repair at write time (ADR-011/D-22)"
    )
    assert re.search(r"entry_ms:\s*Math\.round\(performance\.now\(\)\)", body.group(1)), (
        "the morning's own cost still travels unchanged: withholding it is the "
        "SERVER's decision now, never the client's silence (KPI-1 purity)"
    )


# ---------------------------------------------------------------- post-save reset and merge


def test_a_saved_entry_returns_the_row_to_today_and_re_derives_the_hint():
    branch = saved_branch()
    assert re.search(r"dateInput\.value = deviceLocalDay\(\);", branch), (
        "after a repair the row returns to today (D8/A22): backfill yesterday, "
        "then log this morning -- without the reset the second entry would "
        "silently overwrite the first"
    )
    assert 'weightInput.value = "";' in branch, "the field clears for the next morning"
    assert "paintHint()" in branch, (
        "the one line re-derives against the day the row now shows, so it never "
        "keeps describing the day that was just repaired"
    )


def test_the_saves_own_answer_merges_into_the_map_the_hint_reads():
    branch = saved_branch()
    assert re.search(r"knownWeights = mergedRecord\(knownWeights, outcome\)", branch), (
        "the anchor and the prefill stay fresh with NO reload: the save's answer "
        "is merged into the client's map (criterion 5)"
    )
    merge = re.search(r"function mergedRecord\(.*?\n    \}", MARKUP, re.DOTALL)
    assert merge, "the merge must be a named function to be judged"
    assert "outcome.recent" in merge.group(0), "the refreshed tail of the record merges in"
    assert "outcome.date" in merge.group(0) and "outcome.weight_kg" in merge.group(0), (
        "the saved day itself merges in -- both fields are already on the wire, free"
    )
    assert re.search(r"return \{ \.\.\.weightsByDay, \.\.\.answered \}", merge.group(0)), (
        "a NEW map comes out; the handed-over record is never mutated in place (ADR-005)"
    )


# ---------------------------------------------------------------- degrade-to-absent


def test_a_page_without_a_map_still_takes_an_entry():
    """The hint is a convenience. A missing key is the no-entry presentation; a
    missing map is a script guard. Neither may ever block entry or save."""
    assert re.search(r"let knownWeights = recordWeights \|\| \{\};", MARKUP), (
        "an absent map degrades to an empty one rather than throwing on first paint"
    )


def test_the_entry_screen_still_ships_exactly_one_inline_script():
    assert MARKUP.count("<script") - len(re.findall(r"<script[^>]*\bsrc=", MARKUP)) == 1, (
        "G-5: the hint, the payload and the reset all land in the ONE inline "
        "script -- no second script, no new origin, no new asset"
    )
