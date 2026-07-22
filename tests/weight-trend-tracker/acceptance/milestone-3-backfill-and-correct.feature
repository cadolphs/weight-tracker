Feature: Backfill and correct past days
  US-003 (Slice 03): a forgotten Sunday or a fat-fingered Tuesday never becomes
  permanent. Past days accept entries under exactly today's rules, the future
  stays closed, and one day never holds two entries.

  Background:
    Given the tracker is running with an empty record
    And today is Tuesday 21 July 2026
    And Clemens has unlocked the tracker with his passphrase

  @driving_port @US-003 @contract-shape:bounded-change
  Scenario: A forgotten day is backfilled
    Given he logged 82.4 kg on 19 July 2026
    And his record has no entry for 20 July 2026
    When he logs "82.6" for 20 July 2026
    Then 20 July 2026 holds exactly one entry of 82.6 kg

  @driving_port @US-003 @contract-shape:bounded-change
  Scenario: A typo from last week is corrected in place
    Given he logged 79.1 kg on 15 July 2026
    When he corrects 15 July 2026 to 82.1 kg
    Then 15 July 2026 holds exactly one entry of 82.1 kg

  @driving_port @error @US-003 @contract-shape:unbounded-preservation
  Scenario: The future stays closed
    When he logs "82.0" for 25 July 2026
    Then the save is rejected because future dates cannot be logged
    And nothing is stored

  @driving_port @error @US-003 @contract-shape:unbounded-preservation
  Scenario: Past-day validation matches today's rules
    Given he logged 82.7 kg on 18 July 2026
    When he logs "8.2" for 18 July 2026
    Then the save is rejected because the value must be between 30.0 and 250.0 kg
    And his record is unchanged

  @pending @driving_port @US-003 @contract-shape:unbounded-preservation
  Scenario: Saving the same value again changes nothing
    Given he logged 82.4 kg on 19 July 2026
    When he logs "82.4" for 19 July 2026
    Then 19 July 2026 holds exactly one entry of 82.4 kg
    And the record is exactly as before

  @pending @driving_port @US-003 @contract-shape:bounded-change
  Scenario: A phone already in tomorrow may log its new day
    Given his phone is already in 22 July 2026
    When he logs "82.4" for 22 July 2026
    Then 22 July 2026 holds exactly one entry of 82.4 kg

  @pending @driving_port @error @US-003 @contract-shape:unbounded-preservation
  Scenario: A date two days ahead is rejected even from a skewed phone
    Given his phone is already in 22 July 2026
    When he logs "82.4" for 23 July 2026
    Then the save is rejected because future dates cannot be logged
    And nothing is stored

  @pending @driving_port @error @US-003 @contract-shape:unbounded-preservation
  Scenario: An unrecognisable date is rejected safely
    When he submits a weight for an unrecognisable date
    Then the save is rejected because the date is not recognisable
    And nothing is stored
