Feature: Log today's weight in seconds
  US-001 (Slice 01): one honest number per morning. Implausible input never
  pollutes the record, a day never holds two entries, and a confirmed save
  survives anything.

  Background:
    Given the tracker is running with an empty record
    And today is Tuesday 21 July 2026
    And Clemens has unlocked the tracker with his passphrase

  @driving_port @error @US-001 @contract-shape:unbounded-preservation
  Scenario: An implausible typo is caught before it pollutes the record
    When he logs "824" for today
    Then the save is rejected because the value must be between 30.0 and 250.0 kg
    And nothing is stored
    And his typed value is kept for correction

  @driving_port @error @US-001 @contract-shape:unbounded-preservation
  Scenario Outline: Values outside the plausible range are rejected
    When he logs "<raw>" for today
    Then the save is rejected because the value must be between 30.0 and 250.0 kg
    And nothing is stored

    Examples:
      | raw   |
      | 29.9  |
      | 250.1 |
      | 824   |
      | 8.2   |

  @driving_port @US-001 @contract-shape:bounded-change
  Scenario Outline: Values at the edge of plausibility are accepted
    When he logs "<raw>" for today
    Then he sees the confirmation "Saved: <raw> kg — Tue 21 Jul"
    And today holds exactly one entry of <raw> kg

    Examples:
      | raw   |
      | 30.0  |
      | 250.0 |

  @driving_port @error @US-001 @contract-shape:unbounded-preservation
  Scenario: A finer-than-scale value is rejected rather than silently rounded
    When he logs "81.234" for today
    Then the save is rejected because the value is finer than the 0.1 kg scale
    And nothing is stored

  @driving_port @error @US-001 @contract-shape:unbounded-preservation
  Scenario: Something that is not a weight is rejected safely
    When he logs "eighty two" for today
    Then the save is rejected because that is not a weight
    And nothing is stored

  @driving_port @error @US-001 @contract-shape:unbounded-preservation
  Scenario: Empty submit does nothing destructive
    When he submits an empty weight for today
    Then the save is rejected because a weight is required
    And nothing is stored

  @driving_port @US-001 @contract-shape:bounded-change
  Scenario: Re-saving today replaces rather than duplicates
    Given he has already logged 82.4 kg for today
    When he logs "82.1" for today
    Then today holds exactly one entry of 82.1 kg

  @driving_port @real-io @adapter-integration @US-001 @contract-shape:unbounded-preservation
  Scenario: A confirmed save survives a restart
    Given he has already logged 82.4 kg for today
    When the tracker is restarted
    Then today holds exactly one entry of 82.4 kg

  @driving_port @US-001 @contract-shape:bounded-change
  Scenario: A log just after midnight belongs to the phone's new day
    Given his phone is already in 22 July 2026
    When he logs "82.4" for today
    Then 22 July 2026 holds exactly one entry of 82.4 kg
