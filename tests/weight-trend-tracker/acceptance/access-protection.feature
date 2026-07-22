Feature: The record is protected
  A public address holds one person's weight record. The passphrase keeps it
  private without ever slowing down a half-awake morning, and the tracker
  refuses to run at all rather than risk losing a confirmed entry.

  Background:
    Given the tracker is running with an empty record
    And today is Tuesday 21 July 2026

  @pending @driving_port @US-001 @contract-shape:bounded-change
  Scenario: The right passphrase opens his record
    When he unlocks the tracker with his passphrase
    Then his record is open to him

  @pending @driving_port @error @US-001 @contract-shape:unbounded-preservation
  Scenario: A wrong passphrase keeps the record closed
    When he tries the wrong passphrase
    Then his record stays hidden

  @pending @driving_port @error @US-001 @contract-shape:unbounded-preservation
  Scenario: Without the passphrase the record stays hidden
    When he opens his record
    Then his record stays hidden

  @pending @driving_port @error @US-001 @contract-shape:unbounded-preservation
  Scenario: Without the passphrase nothing can be added to the record
    When he logs "82.4" for today
    Then the save is turned away without the passphrase
    And nothing is stored

  @pending @driving_port @error @US-001 @contract-shape:unbounded-preservation
  Scenario: Repeated wrong guesses are throttled
    When he tries the wrong passphrase 10 times in a row
    Then further attempts are turned away for a while

  @pending @driving_port @US-001 @contract-shape:pure-function
  Scenario: An unlock lasts across seasons
    Given Clemens has unlocked the tracker with his passphrase
    And 89 days have passed
    When he opens his record
    Then his record is open to him

  @pending @driving_port @error @US-001 @contract-shape:pure-function
  Scenario: After three months the passphrase is asked again
    Given Clemens has unlocked the tracker with his passphrase
    And 91 days have passed
    When he opens his record
    Then he is asked for the passphrase again

  @pending @driving_port @contract-shape:pure-function
  Scenario: The tracker's health can be checked without the passphrase
    When he checks the tracker's health
    Then the tracker reports itself healthy without the passphrase

  @pending @driving_port @error @real-io @US-001 @contract-shape:unbounded-preservation
  Scenario: A record that cannot be stored safely refuses to open
    Given the record's home cannot be written to
    When the tracker starts
    Then the tracker refuses to open rather than risk his record
