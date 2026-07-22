Feature: From pocket to logged in five seconds
  US-006 (Slice 05): the entry screen drops Clemens straight into typing with
  yesterday's value as an anchor, the tracker installs on his phone's home
  screen, and every save records how long the morning ritual took so the
  five-second budget is measured, not guessed.

  Background:
    Given the tracker is running with an empty record
    And today is Tuesday 21 July 2026
    And Clemens has unlocked the tracker with his passphrase

  @driving_port @US-006 @contract-shape:pure-function
  Scenario: Launch drops him straight into typing
    Given yesterday he logged 82.6 kg
    When he opens the entry screen
    Then the entry screen is ready for immediate typing

  @driving_port @US-006 @contract-shape:pure-function
  Scenario: Yesterday anchors today
    Given yesterday he logged 82.6 kg
    When he opens the entry screen
    Then yesterday's 82.6 kg is shown beside the input

  @driving_port @US-006 @contract-shape:pure-function
  Scenario: Yesterday still anchors today in a well-kept record
    # All three neighbouring days hold DISTINCT values so the anchor is pinned
    # to yesterday specifically: a latest-entry slip would show today's 81.9,
    # an off-by-one-older slip would show 83.4 (mutation survivors, step 03-06).
    Given he logged 83.4 kg on 19 July 2026
    And yesterday he logged 82.6 kg
    And he has already logged 81.9 kg for today
    When he opens the entry screen
    Then yesterday's 82.6 kg is shown beside the input

  @driving_port @error @US-006 @contract-shape:pure-function
  Scenario: The first morning has no yesterday to lean on
    When he opens the entry screen
    Then no yesterday reference is shown

  @driving_port @US-006 @contract-shape:pure-function
  Scenario: The tracker can join the phone home screen
    When he looks for the home-screen install option
    Then the tracker offers itself for the home screen

  @driving_port @property @kpi @real-io @adapter-integration @US-006 @contract-shape:bounded-change
  Scenario: A week of timed mornings yields the speed report
    Given he has logged timed entries every morning for the last week
    When he opens the speed report
    Then the speed report shows the week's median and worst-case entry times

  @driving_port @error @kpi @US-006 @contract-shape:pure-function
  Scenario: An untimed record makes no speed claims
    When he opens the speed report
    Then the speed report honestly shows no timed mornings yet
