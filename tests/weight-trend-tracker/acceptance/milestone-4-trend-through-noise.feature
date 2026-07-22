Feature: See the true trend through daily noise
  US-004 + US-005 (Slice 04): a single smooth trend line that absorbs
  restaurant-night spikes, survives vacation gaps, tracks real change within a
  week, and renders identically on every load — with a one-tap Trend/Raw toggle
  that never loses the chosen window. The trend revises its recent past as
  entries arrive (by design); these scenarios assert the CURRENT line's shape
  for a fixed entry set, never the immutability of previously rendered values.

  Background:
    Given the tracker is running with an empty record
    And today is Tuesday 21 July 2026
    And Clemens has unlocked the tracker with his passphrase

  @pending @driving_port @US-004 @contract-shape:pure-function
  Scenario: A restaurant-night spike is revealed as noise
    Given his record holds a steady 82.3 kg from 7 July 2026 to 21 July 2026
    And he has noted the current trend at "1M"
    When the next morning he logs "83.6"
    Then the trend moves by no more than 0.3 kg

  @pending @driving_port @error @US-004 @contract-shape:pure-function
  Scenario: The trend survives a vacation gap
    Given his record holds a steady 82.3 kg from 18 March 2026 to 9 April 2026
    And he logged 82.9 kg on 18 April 2026
    When he opens the trend at "All"
    Then the trend has a value for every day from 18 March 2026 to 18 April 2026
    And the trend line steps by no more than 0.3 kg between consecutive days

  @pending @driving_port @US-004 @contract-shape:pure-function
  Scenario: Real change shows up within a week
    Given his record holds a steady 82.3 kg from 1 June 2026 to 14 June 2026
    And his entries fall by half a kilogram each week from 15 June 2026 to 5 July 2026
    When he opens the trend at "3M"
    Then the trend shows the decline within 7 days of 15 June 2026

  @pending @driving_port @US-004 @contract-shape:bounded-change
  Scenario: Corrections flow into the trend
    Given his record holds a steady 82.3 kg from 8 July 2026 to 21 July 2026
    And he logged 79.1 kg on 15 July 2026
    And he has noted the current trend at "1M"
    When he corrects 15 July 2026 to 82.1 kg
    Then the trend no longer dips at 15 July 2026

  @pending @driving_port @property @kpi @US-004 @contract-shape:pure-function
  Scenario: The trend is deterministic
    Given his record holds an entry for every day from 1 May 2026 to 21 July 2026
    When he opens the trend at "3M"
    Then every load shows the identical trend line at "3M"

  @pending @driving_port @error @US-004 @contract-shape:pure-function
  Scenario: The trend begins with the very first entry
    Given he logged 82.4 kg on 21 July 2026
    When he opens the trend at "1W"
    Then the trend begins at 21 July 2026

  @pending @driving_port @US-005 @contract-shape:pure-function
  Scenario: Toggling preserves the time window
    Given his record holds an entry for every day from 1 May 2026 to 21 July 2026
    And he is viewing the trend at "3M"
    When he switches the graph to Raw
    Then the Raw view is shown at "3M"

  @pending @driving_port @US-005 @contract-shape:pure-function
  Scenario: Round trip is lossless
    Given his record holds an entry for every day from 1 May 2026 to 21 July 2026
    And he toggled to the Raw view at "3M"
    When he switches the graph to Trend
    Then the Trend view is shown at "3M"

  @pending @driving_port @US-005 @contract-shape:pure-function
  Scenario: The trend is the default lens
    Given his record holds an entry for every day from 1 May 2026 to 21 July 2026
    When he opens the graph
    Then the trend view is shown first

  @pending @driving_port @kpi @real-io @adapter-integration @US-004 @contract-shape:bounded-change
  Scenario: Opening the trend counts toward engagement
    Given his record holds an entry for every day from 1 July 2026 to 21 July 2026
    When he opens the trend at "1M"
    Then his trend views this week number 1
