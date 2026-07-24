"""Scenario bindings for device-day-frame.feature (skew regression, fix-device-day-reads)."""

from pytest_bdd import scenarios
from steps_access import *  # noqa: F401,F403
from steps_day_frame import *  # noqa: F401,F403
from steps_record import *  # noqa: F401,F403
from steps_views import *  # noqa: F401,F403

scenarios("../device-day-frame.feature")
