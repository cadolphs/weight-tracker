Feature: From pocket to logged in five seconds
  US-006 (Slice 05): the entry screen drops Clemens straight into typing with
  yesterday's value as an anchor, the tracker installs on his phone's home
  screen, and every save records how long the morning ritual took so the
  five-second budget is measured, not guessed.

  Background:
    Given the tracker is running with an empty record
    And today is Tuesday 21 July 2026
    And Clemens has unlocked the tracker with his passphrase

  @pending @driving_port @US-006 @contract-shape:pure-function
  Scenario: Launch drops him straight into typing
    Given yesterday he logged 82.6 kg
    When he opens the entry screen
    Then the entry screen is ready for immediate typing

  @pending @driving_port @US-006 @contract-shape:pure-function
  Scenario: Yesterday anchors today
    Given yesterday he logged 82.6 kg
    When he opens the entry screen
    Then yesterday's 82.6 kg is shown beside the input

  @pending @driving_port @error @US-006 @contract-shape:pure-function
  Scenario: The first morning has no yesterday to lean on
    When he opens the entry screen
    Then no yesterday reference is shown

  @pending @driving_port @US-006 @contract-shape:pure-function
  Scenario: The tracker can join the phone home screen
    When he looks for the home-screen install option
    Then the tracker offers itself for the home screen

  @pending @driving_port @property @kpi @real-io @adapter-integration @US-006 @contract-shape:bounded-change
  Scenario: A week of timed mornings yields the speed report
    Given he has logged timed entries every morning for the last week
    When he opens the speed report
    Then the speed report shows the week's median and worst-case entry times
