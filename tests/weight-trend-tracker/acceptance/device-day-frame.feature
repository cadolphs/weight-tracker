Feature: The day frame belongs to the phone
  Regression (fix-device-day-reads): after 6 p.m. at home the UTC day has
  already rolled over, and every read surface framed "today" from the server
  clock -- the yesterday anchor slipped onto this morning's entry and the 1W
  windows dropped their oldest day. A5 (the device-local calendar day is
  canonical) extends from writes to reads: the phone declares its day, the
  server validates and bounds the claim. Oracle discipline: every expected
  day below derives from the phone's day, never from the server clock.

  Background:
    Given the tracker is running with an empty record
    And today is Tuesday 21 July 2026
    And Clemens has unlocked the tracker with his passphrase

  @regression @driving_port @US-006 @contract-shape:pure-function
  Scenario: An evening at home is still today
    Given he logged 82.6 kg on 20 July 2026
    And he has already logged 81.9 kg for today
    And the UTC day has rolled over to 22 July 2026 while his phone is still in 21 July 2026
    When he opens the entry screen
    Then the yesterday anchor names 20 July 2026's 82.6 kg

  @regression @driving_port @US-002 @contract-shape:pure-function
  Scenario: The raw week does not lose a day at dusk
    Given his record holds an entry for every day from 15 July 2026 to 21 July 2026
    And the UTC day has rolled over to 22 July 2026 while his phone is still in 21 July 2026
    When he opens his history at "1W" as his phone frames the day
    Then his history spans 15 July 2026 to 21 July 2026

  @regression @driving_port @US-004 @contract-shape:pure-function
  Scenario: The trend week does not lose a day at dusk
    Given his record holds an entry for every day from 8 July 2026 to 21 July 2026
    And the UTC day has rolled over to 22 July 2026 while his phone is still in 21 July 2026
    When he opens the trend at "1W" as his phone frames the day
    Then the trend line spans exactly 15 July 2026 to 21 July 2026

  @regression @driving_port @error @contract-shape:unbounded-preservation
  Scenario Outline: A garbled day is turned away politely
    Given he logged 82.4 kg on 20 July 2026
    When his phone asks for the <lens> week claiming the day is "<claimed day>"
    Then the garbled day claim is politely turned away

    Examples:
      | lens  | claimed day               |
      | raw   | someday-soon              |
      | raw   | 2026-13-45                |
      | raw   | <script>alert(1)</script> |
      | trend | not-a-day                 |
      | trend | 9999-99-99                |

  # A parseable claim beyond server UTC +/- MAX_DEVICE_SKEW_DAYS is clamped to
  # the nearest bound (reads stay forgiving where saves stay strict): the year
  # 2030 clamps to 22 July (server day + 1), framing the raw week as 16..22 July.
  @regression @driving_port @error @US-002 @contract-shape:pure-function
  Scenario: A phone claiming a far-future day is reined in to the skew bound
    Given his record holds an entry for every day from 15 July 2026 to 21 July 2026
    When his phone asks for the raw week claiming the day is "2030-01-01"
    Then his history spans 16 July 2026 to 21 July 2026

  # ...and 1970 clamps to 20 July (server day - 1), framing the week as 14..20 July.
  @regression @driving_port @error @US-002 @contract-shape:pure-function
  Scenario: A phone claiming a long-gone day is reined in to the skew bound
    Given his record holds an entry for every day from 15 July 2026 to 21 July 2026
    When his phone asks for the raw week claiming the day is "1970-01-01"
    Then his history spans 15 July 2026 to 20 July 2026
