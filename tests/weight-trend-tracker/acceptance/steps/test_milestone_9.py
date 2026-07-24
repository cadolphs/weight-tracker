"""Scenario bindings for milestone-9-whole-record-history.feature (shared step suite)."""

from pytest_bdd import scenarios
from steps_access import *  # noqa: F401,F403
from steps_glance import *  # noqa: F401,F403
from steps_history_record import *  # noqa: F401,F403
from steps_home_graph import *  # noqa: F401,F403
from steps_record import *  # noqa: F401,F403
from steps_views import *  # noqa: F401,F403

scenarios("../milestone-9-whole-record-history.feature")
