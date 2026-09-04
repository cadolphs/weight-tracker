"""Scenario bindings for milestone-11-honest-axis.feature (shared step suite)."""

from pytest_bdd import scenarios
from steps_access import *  # noqa: F401,F403
from steps_honest_axis import *  # noqa: F401,F403
from steps_record import *  # noqa: F401,F403
from steps_views import *  # noqa: F401,F403

scenarios("../milestone-11-honest-axis.feature")
