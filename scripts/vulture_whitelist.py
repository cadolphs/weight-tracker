"""Names vulture cannot see being used (consumed outside `src/` or by a framework).

Each entry says WHO uses the name. A name that no longer has a consumer leaves this
file and, when nothing else holds it, the code. Vulture treats any name mentioned
here as used; the lines are never executed.
"""

# Jinja templates read EntryRow's cells by attribute (index.html, graph.html).
day_text
raw_text
trend_text

# ViewMode members are built from the query string via ViewMode(value) in the
# shell and named directly only by the acceptance suite.
TREND
RAW

# Published core constant consumed by the acceptance suite's domain_types oracle.
PRECISION_KG
