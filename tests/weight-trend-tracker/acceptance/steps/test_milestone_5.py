"""Scenario bindings for milestone-5-five-second-entry.feature (steps shared across the suite)."""

from pytest_bdd import scenarios

from steps_access import *  # noqa: F401,F403
from steps_record import *  # noqa: F401,F403
from steps_views import *  # noqa: F401,F403

scenarios("../milestone-5-five-second-entry.feature")
