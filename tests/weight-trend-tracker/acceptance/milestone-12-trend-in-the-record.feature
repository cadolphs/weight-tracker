Feature: The trend has a readable history
  US-016 (numeric-trend-history, Slice 01): the smoothed trend stops being a
  number for exactly one day and a shape everywhere else. Both entries lists --
  the front page's last seven and the History page's complete record -- become
  aligned Date | Raw | Trend tables, so "how far has the trend moved" is a
  subtraction of two printed numbers rather than an estimate off a curve
  (js-2-judge, sharpened by the deliberately calm axis of US-015). The trend
  value is the SAME smoothed series the chart plots and the glance line
  reports, read at each entry's own day (ADR-004/ADR-013: derived, never
  stored, revised retrospectively when a past day is backfilled). One row
  definition serves both surfaces and the in-place repaint; a failing trend
  empties the trend cells and nothing else.

  Background:
    Given the tracker is running with an empty record
    And today is Friday 24 July 2026
    And Clemens has unlocked the tracker with his passphrase

  @driving_port @US-016 @contract-shape:pure-function
  Scenario: A noisy week reads as a steady trend, in numbers
    Given his record holds an entry for every day from 1 June 2026 to 24 July 2026
    When he opens the entry screen
    Then every recent row carries a date, a raw weight and a trend weight
    And every recent trend value is the smoothed series value for that row's day

  @driving_port @US-016 @contract-shape:pure-function
  Scenario: The newest row and the glance line agree
    Given his weight has been falling for the last two weeks
    When he opens the entry screen
    Then the newest recent row's trend value equals the glance line's trend value
    And the same day reads the same trend value on the History page

  @driving_port @property @US-016 @contract-shape:pure-function
  Scenario: The whole record carries the column at every scale
    Given his record holds an entry for every day from 3 March 2026 to 24 July 2026
    When he opens the graph
    Then every complete-record row carries a date, a raw weight and a trend weight
    And every complete-record trend value is the smoothed series value for that row's day
    And the complete record reads identically at every time scale

  @driving_port @error @US-016 @contract-shape:pure-function
  Scenario: Missing days are absent, not empty rows
    Given his record holds an entry for every day from 1 June 2026 to 9 July 2026
    And his record holds an entry for every day from 14 July 2026 to 24 July 2026
    When he opens the graph
    Then every day from 10 July 2026 to 13 July 2026 appears nowhere in the complete list
    And no rendered row is missing either of its two weights

  @driving_port @US-016 @contract-shape:bounded-change
  Scenario: A backfilled day revises the rows above it, in place
    Given his record holds an entry for every day from 1 July 2026 to 24 July 2026
    And his record has no entry for 26 June 2026
    When he logs "76.8" for 26 June 2026
    Then the handed-back recent list carries a trend value for every entry
    And every handed-back trend value is the smoothed series value for its day

  @driving_port @error @US-016 @contract-shape:pure-function
  Scenario: A failing trend leaves the raw record standing
    Given his record holds an entry for every day from 1 July 2026 to 24 July 2026
    And the trend column cannot be computed
    When he opens the entry screen
    Then every recent row still carries its date and raw weight
    And every recent trend value is blank
    And the entry screen is ready for immediate typing

  @driving_port @error @US-016 @contract-shape:pure-function
  Scenario: A first morning stands on its own trend
    Given he logged 77.2 kg on 24 July 2026
    When he opens the entry screen
    Then every recent row carries a date, a raw weight and a trend weight
    And every recent trend value is the smoothed series value for that row's day

  @driving_port @error @US-016 @contract-shape:pure-function
  Scenario: An empty record shows no table at all
    When he opens the entry screen
    Then no recent list is offered
    When he opens the graph
    Then no complete list is rendered

  @driving_port @property @US-016 @contract-shape:pure-function
  Scenario: Both lists speak one grammar
    Given his record holds an entry for every day from 1 June 2026 to 24 July 2026
    When he opens the entry screen
    Then the recent rows are exactly the newest rows of the complete record

  @driving_port @US-016 @contract-shape:pure-function
  Scenario: The columns are announced, not merely aligned
    Given his record holds an entry for every day from 1 July 2026 to 24 July 2026
    When he opens the entry screen
    Then the recent list names its three columns as table headers
    When he opens the graph
    Then the complete list names its three columns as table headers

  @driving_port @US-016 @contract-shape:pure-function
  Scenario: Looking is still not touching
    Given his record holds an entry for every day from 1 July 2026 to 24 July 2026
    When he opens the entry screen
    Then the recent list offers no way to edit or delete

  @driving_port @kpi @US-016 @contract-shape:unbounded-preservation
  Scenario: The second column costs nothing at the door
    Given his record holds an entry for every day from 1 January 2026 to 24 July 2026
    When he opens the entry screen, watch in hand
    Then the entry screen is ready within two seconds
    And the entry screen is ready for immediate typing
