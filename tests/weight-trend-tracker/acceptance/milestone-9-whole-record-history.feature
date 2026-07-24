Feature: One place holds the whole record
  US-012 (graph-first-home, Slice 02): "History" keeps its promise -- one
  deliberate tap opens the combined page: the full-control graph on top and
  the COMPLETE numeric record beneath it, newest first, date + kg at 0.1
  precision. The list is server-rendered from the same single entry store the
  raw plot draws (D-17/D-18) and always shows the whole record regardless of
  the chart's selected window; days without an entry are absent from both.
  Existing /graph behaviors are preserved by construction (A16): deep links,
  lens-preserves-scale, empty-invite, back-link. Opening this page is where
  deliberate trend study now lives (KPI-3, A19 -- `trend.study.opened`,
  ADR-009). G-2 extends to the combined page: interactive within the budget
  with a >=300-entry record.

  Background:
    Given the tracker is running with an empty record
    And today is Friday 24 July 2026
    And Clemens has unlocked the tracker with his passphrase

  @driving_port @US-012 @contract-shape:pure-function
  Scenario: History leads to the whole record
    Given his record holds an entry for every day from 3 March 2026 to 9 April 2026
    And his record holds an entry for every day from 18 April 2026 to 24 July 2026
    When he opens the graph
    Then the graph page offers both lenses and every time scale
    And the complete record is listed beneath the graph, newest first
    And every day from 10 April 2026 to 17 April 2026 appears nowhere in the complete list

  @driving_port @US-012 @contract-shape:pure-function
  Scenario: The list and the plot tell the same story
    Given his record holds an entry for every day from 1 June 2026 to 9 July 2026
    And his record holds an entry for every day from 14 July 2026 to 24 July 2026
    When he studies the Raw record at "All"
    Then the complete list carries exactly the entries the raw plot draws
    And every day from 10 July 2026 to 13 July 2026 appears nowhere in the complete list

  @pending @driving_port @kpi @real-io @adapter-integration @US-012 @contract-shape:bounded-change
  Scenario: Deliberate study is counted where it happens
    Given his weight has been falling for the last two weeks
    And he has studied the History page once this week
    When he opens the graph
    Then the deliberate trend-study count for this week is 2

  @driving_port @US-012 @contract-shape:pure-function
  Scenario: Old bookmarks still work
    Given his weight has been falling for the last two weeks
    When he follows his old bookmark to the Raw year view
    Then the Raw view is shown at "1Y"
    And the complete record is listed beneath the graph, newest first
    And the way back to today's entry is one tap away
    When he switches the graph to Trend
    Then the Trend view is shown at "1Y"

  @driving_port @error @US-012 @contract-shape:pure-function
  Scenario: An empty record still invites
    When he opens the graph
    Then the first-log invite is still offered
    And no complete list is rendered
    And the empty visit still counts as one deliberate study

  @pending @driving_port @property @kpi @US-012 @contract-shape:pure-function
  Scenario: The full record arrives without a wait
    Given his record holds an entry for every day from 1 September 2025 to 24 July 2026
    When he opens the History page, watch in hand
    Then the History page is ready within two seconds
    And the complete record is listed beneath the graph, newest first
