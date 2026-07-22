"""Scenario bindings for milestone-3-backfill-and-correct.feature (shared step vocabulary)."""

from pytest_bdd import scenarios
from steps_access import *  # noqa: F401,F403
from steps_record import *  # noqa: F401,F403
from steps_views import *  # noqa: F401,F403

scenarios("../milestone-3-backfill-and-correct.feature")
