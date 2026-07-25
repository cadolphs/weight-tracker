Feature: The record repairs itself where the habit lives
  US-013 + US-014 (entry-date-picker, Slice 01): a date row rests above the
  weight field, so a forgotten Sunday or a fat-fingered Tuesday is repaired on
  the entry screen in seconds -- picking a past day offers its stored weight
  back for correction, or admits the gap -- while the five-second morning keeps
  costing exactly what it always did. Maintenance is never mistaken for a
  morning: a backdated save contributes 0 samples to the morning-speed record
  and is counted as a repair instead (KPI-1 purity + KPI-8, ADR-011), and the
  correction of a timed morning never erases what that morning already cost.
  What the phone renders -- the picker's own default and upper bound, the hint
  wording -- is client-structural (one node, one pure function; the client-paint
  precedent D-15) and verified at dogfood. These scenarios pin what the tracker
  itself SERVES and STORES: the date row above the field, the whole-record
  day-to-weight map that answers ANY stored day (ADR-010), the single hint line,
  the server-authoritative no-future rule, and the write-time classification --
  falsifiable at the HTTP boundary, never a client convention.

  Background:
    Given the tracker is running with an empty record
    And today is Friday 24 July 2026
    And Clemens has unlocked the tracker with his passphrase

  @driving_port @US-013 @contract-shape:bounded-change
  Scenario: A forgotten day is backfilled from the entry screen
    Given his record holds an entry for every day from 20 July 2026 to 23 July 2026
    And his record has no entry for 19 July 2026
    When he backfills "82.6" for 19 July 2026
    Then he sees the confirmation "Saved: 82.6 kg — Sun 19 Jul"
    And 19 July 2026 holds exactly one entry of 82.6 kg
    And the refreshed picture the save hands back holds "Sun 19 Jul — 82.6 kg"
    And the trend recomputes over the repaired record including 19 July 2026

  @driving_port @property @kpi @US-013 @contract-shape:pure-function
  Scenario: The morning flow never pays for the picker
    Given his record holds an entry for every day from 17 July 2026 to 23 July 2026
    When he opens the entry screen, watch in hand
    Then the entry screen is ready within two seconds
    And the date row rests above the weight field
    And the entry screen is ready for immediate typing
    And nothing about the date row steals the morning focus

  @driving_port @US-013 @contract-shape:pure-function
  Scenario: The picker cannot wander off before the record began
    Given he logged 84.9 kg on 3 March 2026
    And he logged 82.4 kg on 23 July 2026
    When he opens the entry screen
    Then the date row reaches back no further than 3 March 2025

  @driving_port @error @kpi @US-013 @contract-shape:unbounded-preservation
  Scenario: The future stays closed however the phone frames its day
    Given he logged 82.4 kg on 23 July 2026
    When a save of "82.0" for 30 July 2026 arrives from his phone
    Then the save is rejected because future dates cannot be logged
    And nothing is stored
    And neither the morning-speed record nor the repair count moves

  @driving_port @property @kpi @real-io @adapter-integration @US-013 @contract-shape:bounded-change
  Scenario: A slow repair never slows the morning record
    Given he has logged timed entries every morning for the last week
    And his record has no entry for 10 July 2026
    When he takes 22000 ms to backfill "82.6" for 10 July 2026
    Then the week's morning-speed record still holds the same mornings
    And the repair is counted on the stats page

  @driving_port @kpi @US-013 @contract-shape:bounded-change
  Scenario: A morning still counts as a morning
    Given he has logged timed entries every morning for the last week
    When he takes 4200 ms to log "82.2" for today
    Then the week's morning-speed record gains that morning
    And no repair is counted for it

  @driving_port @error @US-013 @contract-shape:bounded-change
  Scenario Outline: A phone that will not say which day it is on is still served
    When a save of "82.6" for 19 July 2026 arrives <claim>
    Then he sees the confirmation "Saved: 82.6 kg — Sun 19 Jul"
    And 19 July 2026 holds exactly one entry of 82.6 kg

    Examples:
      | claim                                   |
      | with no word about the phone's day      |
      | with a garbled word for the phone's day |

  @driving_port @US-014 @contract-shape:pure-function
  Scenario: Any day of the record answers the picker
    Given he logged 84.9 kg on 3 March 2026
    And his record holds an entry for every day from 17 July 2026 to 23 July 2026
    When he opens the entry screen
    Then 3 March 2026 offers its stored 84.9 kg back for correction
    And every day of the record offers its stored weight back

  @driving_port @error @US-014 @contract-shape:pure-function
  Scenario: A gap is offered as a gap, never as a value
    Given he logged 82.5 kg on 20 July 2026
    And he logged 82.4 kg on 21 July 2026
    And his record has no entry for 19 July 2026
    When he opens the entry screen
    Then 21 July 2026 offers its stored 82.4 kg back for correction
    And 19 July 2026 offers nothing to correct

  @driving_port @US-014 @contract-shape:bounded-change
  Scenario: A mistyped past day is corrected in place
    Given he logged 88.4 kg on 21 July 2026
    And his record holds an entry for every day from 22 July 2026 to 23 July 2026
    When he corrects 21 July 2026 to 82.4 kg from the date row
    Then he sees the confirmation "Saved: 82.4 kg — Tue 21 Jul"
    And 21 July 2026 holds exactly one entry of 82.4 kg
    And the refreshed picture the save hands back holds "Tue 21 Jul — 82.4 kg"
    And the trend recomputes over the repaired record including 21 July 2026

  @driving_port @error @kpi @US-014 @contract-shape:bounded-change
  Scenario: Correcting a timed morning leaves the week's mornings intact
    Given he has logged timed entries every morning for the last week
    When he corrects 22 July 2026 to 82.1 kg from the date row
    Then 22 July 2026 holds exactly one entry of 82.1 kg
    And the week's morning-speed record still holds the same mornings
    And the repair is counted on the stats page

  @driving_port @US-014 @contract-shape:pure-function
  Scenario: One hint line serves the anchor and the repair alike
    Given yesterday he logged 82.4 kg
    When he opens the entry screen
    Then the screen carries exactly one hint line
    And yesterday's 82.4 kg is shown beside the input
    And the hint names its day in the record's own grammar

  @driving_port @error @US-013 @US-014 @contract-shape:pure-function
  Scenario: An empty record still opens straight into typing
    When he opens the entry screen
    Then the date row rests above the weight field
    And the entry screen is ready for immediate typing
    And nothing of the record is offered to correct
