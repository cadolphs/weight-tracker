"""Step vocabulary: passphrase protection, sessions, health, startup trust (ADR-003).

Access state machine (C2a):
    LOCKED --right passphrase--> UNLOCKED(90 days, judged by the injected clock)
    LOCKED --wrong passphrase--> LOCKED           [illegal event, graceful]
    LOCKED --N wrong in a row--> THROTTLED        [even the right passphrase waits]
    UNLOCKED --91 days pass--> LOCKED             [expiry]
    any state --health check--> answered          [no passphrase needed]
    BROKEN STORE --start--> REFUSED               [never serve over an untrusted store]
"""

from __future__ import annotations

from composition import WRONG_PASSPHRASE
from domain_types import TEST_PASSPHRASE
from pytest_bdd import given, parsers, then, when

# ---------------------------------------------------------------- Given


@given("Clemens has unlocked the tracker with his passphrase")
def step_unlocked(composition):
    composition.access.unlock()


@given(parsers.parse("{n:d} days have passed"))
def step_days_passed(composition, n):
    composition.clock.days_pass(n)


@when(parsers.parse("{n:d} days pass"))
def step_days_pass_mid_journey(composition, n):
    # When-flavored twin of "N days have passed", for time elapsing mid-scenario.
    composition.clock.days_pass(n)


# ---------------------------------------------------------------- When


@given("he has visited the tracker in his browser")
@when("he visits the tracker in his browser")
def step_visits_in_browser(composition, ctx):
    ctx.response = composition.access.visit_in_browser()


@when("he enters his passphrase at the door")
def step_enters_passphrase_at_door(composition, ctx):
    ctx.response = composition.access.enter_passphrase_at_door(TEST_PASSPHRASE)


@when("he enters a wrong passphrase at the door")
def step_enters_wrong_passphrase_at_door(composition, ctx):
    ctx.response = composition.access.enter_passphrase_at_door(WRONG_PASSPHRASE)


@when("he unlocks the tracker with his passphrase")
def step_unlocks(composition, ctx):
    ctx.response = composition.access.unlock()


@when("he tries the wrong passphrase")
def step_wrong_once(composition, ctx):
    ctx.response = composition.access.try_passphrase(WRONG_PASSPHRASE)


@when(parsers.parse("he tries the wrong passphrase {n:d} times in a row"))
def step_wrong_many(composition, ctx, n):
    ctx.response = composition.access.try_passphrase(WRONG_PASSPHRASE, times=n)


@when("he opens his record")
def step_opens_record(composition, ctx):
    ctx.response = composition.access.open_record()


@when("he checks the tracker's health")
def step_checks_health(composition, ctx):
    ctx.response = composition.health.check_unauthenticated()


# ---------------------------------------------------------------- Then


@then("the passphrase door is shown rather than a bare refusal")
def step_door_shown(composition, ctx):
    composition.access.assert_passphrase_door(ctx)


@then("the browser lands on the entry screen")
def step_landed_on_entry_screen(composition, ctx):
    composition.access.assert_landed_on_entry_screen(ctx)


@then("the passphrase door is shown again with a visible rejection")
def step_door_rejection(composition, ctx):
    composition.access.assert_door_rejection(ctx)


@then("his record is open to him")
def step_record_open(composition):
    composition.access.assert_record_open()


@then("his record stays hidden")
def step_record_hidden(composition):
    composition.access.assert_record_hidden()


@then("the save is turned away without the passphrase")
def step_save_turned_away(composition, ctx):
    composition.access.assert_save_turned_away(ctx)


@then("further attempts are turned away for a while")
def step_throttled(composition, ctx):
    composition.access.assert_throttled(ctx)


@then("he is asked for the passphrase again")
def step_prompted_again(composition, ctx):
    composition.access.assert_prompted_again(ctx)


@then("the tracker reports itself healthy without the passphrase")
def step_healthy(composition, ctx):
    composition.health.assert_healthy(ctx)


@then("the tracker refuses to open rather than risk his record")
def step_refused(composition, ctx):
    composition.system.assert_refused(ctx)
