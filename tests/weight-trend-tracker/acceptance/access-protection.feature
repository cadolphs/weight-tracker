Feature: The record is protected
  A public address holds one person's weight record. The passphrase keeps it
  private without ever slowing down a half-awake morning, and the tracker
  refuses to run at all rather than risk losing a confirmed entry.

  Background:
    Given the tracker is running with an empty record
    And today is Tuesday 21 July 2026

  @driving_port @US-001 @contract-shape:bounded-change
  Scenario: The right passphrase opens his record
    When he unlocks the tracker with his passphrase
    Then his record is open to him

  @driving_port @error @US-001 @contract-shape:unbounded-preservation
  Scenario: A wrong passphrase keeps the record closed
    When he tries the wrong passphrase
    Then his record stays hidden

  @driving_port @error @US-001 @contract-shape:unbounded-preservation
  Scenario: Without the passphrase the record stays hidden
    When he opens his record
    Then his record stays hidden

  @driving_port @error @US-001 @contract-shape:unbounded-preservation
  Scenario: Without the passphrase nothing can be added to the record
    When he logs "82.4" for today
    Then the save is turned away without the passphrase
    And nothing is stored

  # -- The human doorway (AT_GAP-5): US-001's elevator pitch is "taps the
  # -- tracker icon -> entry screen opens". A half-awake browser visit must be
  # -- met by a door he can walk through, never a bare machine refusal.

  @driving_port @error @US-001 @contract-shape:pure-function
  Scenario: A locked visit is met by the passphrase door
    When he visits the tracker in his browser
    Then the passphrase door is shown rather than a bare refusal

  @driving_port @US-001 @contract-shape:bounded-change
  Scenario: The passphrase door opens onto the entry screen
    Given he has visited the tracker in his browser
    When he enters his passphrase at the door
    Then the browser lands on the entry screen
    And his record is open to him

  @driving_port @error @US-001 @contract-shape:unbounded-preservation
  Scenario: A wrong passphrase keeps the door shut but polite
    Given he has visited the tracker in his browser
    When he enters a wrong passphrase at the door
    Then the passphrase door is shown again with a visible rejection
    And his record stays hidden

  @driving_port @error @US-001 @contract-shape:unbounded-preservation
  Scenario: Repeated wrong guesses are throttled
    When he tries the wrong passphrase 10 times in a row
    Then further attempts are turned away for a while

  @driving_port @US-001 @contract-shape:pure-function
  Scenario: An unlock lasts across seasons
    Given Clemens has unlocked the tracker with his passphrase
    And 89 days have passed
    When he opens his record
    Then his record is open to him

  @driving_port @error @US-001 @contract-shape:pure-function
  Scenario: After three months the passphrase is asked again
    Given Clemens has unlocked the tracker with his passphrase
    And 91 days have passed
    When he opens his record
    Then he is asked for the passphrase again

  @driving_port @contract-shape:pure-function
  Scenario: The tracker's health can be checked without the passphrase
    When he checks the tracker's health
    Then the tracker reports itself healthy without the passphrase

  @driving_port @error @real-io @US-001 @contract-shape:unbounded-preservation
  Scenario: A record that cannot be stored safely refuses to open
    Given the record's home cannot be written to
    When the tracker starts
    Then the tracker refuses to open rather than risk his record
