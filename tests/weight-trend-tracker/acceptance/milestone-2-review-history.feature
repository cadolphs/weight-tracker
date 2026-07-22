Feature: Review weight history at selectable time scales
  US-002 (Slice 02): the raw record as a phone-legible graph. Exactly the stored
  entries appear — missing days stay honest gaps — and every time scale shows
  exactly its window.

  Background:
    Given the tracker is running with an empty record
    And today is Tuesday 21 July 2026
    And Clemens has unlocked the tracker with his passphrase

  @driving_port @US-002 @contract-shape:pure-function
  Scenario: History is readable at the chosen time scale
    Given his record holds an entry for every day from 3 March 2026 to 21 July 2026
    When he opens his history at "3M"
    Then only entries from 22 April 2026 to 21 July 2026 are shown

  @driving_port @US-002 @contract-shape:pure-function
  Scenario: The full record is one tap away
    Given his record holds an entry for every day from 3 March 2026 to 21 July 2026
    When he opens his history at "All"
    Then his history spans 3 March 2026 to 21 July 2026

  @driving_port @error @US-002 @contract-shape:pure-function
  Scenario: Missing days stay honest gaps
    Given his record holds a steady 82.3 kg from 18 March 2026 to 9 April 2026
    And he logged 82.9 kg on 18 April 2026
    When he opens his history at "All"
    Then the days from 10 April 2026 to 17 April 2026 show no entries

  @driving_port @US-002 @contract-shape:pure-function
  Scenario Outline: Each time scale reaches back exactly its window
    Given his record holds an entry for every day from 1 July 2025 to 21 July 2026
    When he opens his history at "<scale>"
    Then only entries from <start> to 21 July 2026 are shown

    Examples:
      | scale | start           |
      | 1W    | 15 July 2026    |
      | 1M    | 22 June 2026    |
      | 3M    | 22 April 2026   |
      | 6M    | 21 January 2026 |
      | 1Y    | 22 July 2025    |

  @driving_port @error @US-002 @contract-shape:pure-function
  Scenario: An empty record invites the first log
    When he opens his history at "All"
    Then he is invited to log his first weight

  @driving_port @error @US-002 @contract-shape:pure-function
  Scenario: A single entry is still a readable record
    Given he logged 82.4 kg on 21 July 2026
    When he opens his history at "1W"
    Then exactly one entry is shown

  @driving_port @property @kpi @US-002 @contract-shape:pure-function
  Scenario: The history is ready without a wait
    Given his record holds an entry for every day from 1 May 2026 to 21 July 2026
    When he opens his history at "3M"
    Then the history is ready within two seconds
