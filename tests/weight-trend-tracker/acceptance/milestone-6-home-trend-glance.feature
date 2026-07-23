Feature: Where you stand, at a glance
  US-007 (home-trend-display, Slice 01): the entry screen answers "where am I,
  and which way am I moving?" at the moment of logging -- a glance line
  `Trend: 82.3 kg · ↓0.25 kg/week` beside the form, refreshed in place by the
  save, honest on young records (no rate below a 7-day ENTRY span, ADR-006),
  degrading to an absent line rather than ever taxing the five-second entry,
  and counted apart from deliberate trend-view study (KPI-3 stays clean).
  The rate revises together with the line under RTS revision (by design):
  oracles assert the CURRENT pair's coherence -- the displayed rate is the
  displayed line's own trailing-week net change -- never the immutability of
  previously rendered values.

  Background:
    Given the tracker is running with an empty record
    And today is Thursday 23 July 2026
    And Clemens has unlocked the tracker with his passphrase

  @walking_skeleton @driving_port @driving_adapter @real-io @US-007 @contract-shape:bounded-change
  Scenario: The morning verdict arrives with the log and survives the save
    Given his weight has been falling for the last two weeks
    And the entry screen shows the trend at a glance
    When he logs "82.1" for today
    Then he sees the confirmation "Saved: 82.1 kg — Thu 23 Jul"
    And the glance refreshes in place with the save

  @driving_port @US-007 @contract-shape:pure-function
  Scenario: Where-am-I and which-way are answered in one glance
    Given his weight has been falling for the last two weeks
    When he opens the entry screen
    Then the entry screen shows the trend at a glance
    And the glanced trend is where the graph's trend line ends
    And the weekly rate is the line's own change over the last week
    And the direction glyph reads "↓"

  @driving_port @US-007 @contract-shape:bounded-change
  Scenario: A sushi-morning spike is defused at the moment of logging
    Given his record holds a steady 82.3 kg from 8 July 2026 to 22 July 2026
    And the entry screen shows the trend at a glance
    When he logs "83.6" for today
    Then he sees the confirmation "Saved: 83.6 kg — Thu 23 Jul"
    And the glance refreshes in place with the save
    And the weekly rate is the line's own change over the last week

  @driving_port @US-007 @contract-shape:pure-function
  Scenario Outline: Every direction is information, never judgment
    Given his weight has been <direction> for the last two weeks
    When he opens the entry screen
    Then the direction glyph reads "<glyph>"
    And the glance wears the same quiet styling in every direction

    Examples:
      | direction | glyph |
      | falling   | ↓     |
      | rising    | ↑     |
      | steady    | →     |

  @driving_port @US-007 @contract-shape:pure-function
  Scenario: Standing still is reported plainly
    Given his record holds a steady 82.0 kg from 8 July 2026 to 22 July 2026
    When he opens the entry screen
    Then the glance line reads a trend of "82.0 kg"
    And the glance line reads a weekly rate of "0.00 kg/week"
    And the direction glyph reads "→"

  @driving_port @error @US-007 @contract-shape:pure-function
  Scenario Outline: A young record holds its tongue about the rate
    # Span is ENTRY-based (latest - earliest ENTRY date, D-12/ADR-006), so the
    # boundary rows log an entry ON the boundary day itself.
    Given his record holds an entry for every day from <first entry> to <last entry>
    When he opens the entry screen
    Then the trend value is shown at a glance
    And the weekly rate is <rate disposition>

    Examples:
      | first entry  | last entry   | rate disposition |
      | 20 July 2026 | 23 July 2026 | held back        |
      | 17 July 2026 | 23 July 2026 | held back        |
      | 16 July 2026 | 23 July 2026 | shown            |

  @driving_port @error @US-007 @contract-shape:pure-function
  Scenario: A resting record still reports where its line ends
    # Entry-based span (15 days) though the last entry is a week old: the rate
    # stays, and the glanced value is the line's END (16 July), same as the graph.
    Given his record holds an entry for every day from 1 July 2026 to 16 July 2026
    When he opens the entry screen
    Then the trend and weekly rate are both shown at a glance
    And the glanced trend is where the graph's trend line ends

  @driving_port @error @US-007 @contract-shape:bounded-change
  Scenario: An empty record shows no trend line until the first save brings one
    Given he has seen the entry screen without a trend line
    When he logs "82.5" for today
    Then the glance appears with his first entry at 82.5 kg and no weekly rate
    And the glance delivery is on the record

  @driving_port @property @kpi @US-007 @contract-shape:pure-function
  Scenario: The glance never taxes the entry
    Given his weight has been falling for the last two weeks
    When he opens the entry screen, watch in hand
    Then the entry screen is ready within two seconds
    And the entry screen is ready for immediate typing
    And the entry screen shows the trend at a glance

  @driving_port @error @US-007 @contract-shape:pure-function
  Scenario: A trend hiccup hides the glance, not the morning
    Given his weight has been falling for the last two weeks
    And the entry screen shows the trend at a glance
    And the trend computation is failing
    When he opens the entry screen
    Then no trend line is shown
    And the entry screen is ready for immediate typing

  @driving_port @error @US-007 @contract-shape:bounded-change
  Scenario: A trend hiccup never blocks the save
    Given his weight has been falling for the last two weeks
    And the entry screen shows the trend at a glance
    And the trend computation is failing
    When he logs "82.4" for today
    Then he sees the confirmation "Saved: 82.4 kg — Thu 23 Jul"
    And today holds exactly one entry of 82.4 kg
    And the save carries no glance to show

  @driving_port @error @US-007 @contract-shape:unbounded-preservation
  Scenario: A rejected save leaves not even a glance behind
    Given his weight has been falling for the last two weeks
    And the entry screen shows the trend at a glance
    When he logs "824" for today
    Then the save is rejected because the value must be between 30.0 and 250.0 kg
    And nothing is stored
    And no glance delivery is recorded for it

  @driving_port @kpi @real-io @adapter-integration @US-007 @contract-shape:bounded-change
  Scenario: The stats page still tells deliberate study from ambient glances
    Given his record holds an entry for every day from 1 July 2026 to 16 July 2026
    And he starts each of the next 7 mornings at the entry screen
    When he studies the graph's trend view 2 times
    Then his trend views this week number 2
    And the glance was delivered 7 times
