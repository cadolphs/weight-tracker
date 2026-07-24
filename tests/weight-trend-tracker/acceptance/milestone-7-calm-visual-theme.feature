Feature: The tracker looks finished, calm in daylight and dark in the dark
  US-008 + US-009 (calm-visual-theme): every morning of the year the tracker
  greets Clemens with a calm, deliberately designed screen instead of default
  browser HTML -- dark when the 06:45 bathroom is dark, light in the daylight,
  the same on the entry screen, the passphrase door and the graph. The look is
  a single self-contained theme delivered by the tracker itself: every ink
  keeps its contrast promise in both lights (G-4), the whole look costs almost
  nothing (G-5: no outside requests, no new morning-screen scripts), and NO
  behavior changes -- saves, rejections, the glance and the door all work
  byte-for-byte as before, with or without the theme (progressive enhancement).
  A mid-session light/dark flip on the open graph is covered structurally
  (single palette, one theme source) and verified live at DELIVER dogfood.

  Background:
    Given the tracker is running with an empty record
    And today is Thursday 23 July 2026

  @walking_skeleton @driving_port @driving_adapter @real-io @US-008 @contract-shape:pure-function
  Scenario: The calm look arrives with the morning screen
    Given Clemens has unlocked the tracker with his passphrase
    When he opens the entry screen
    Then the entry screen wears the calm theme
    And the calm look is delivered by the tracker itself
    And it is dressed for daylight and for dim light alike
    And the entry screen is ready for immediate typing

  @driving_port @property @US-008 @contract-shape:pure-function
  Scenario: The new clothes never slow the morning down
    Given Clemens has unlocked the tracker with his passphrase
    And his weight has been falling for the last two weeks
    And the entry screen wears the calm theme
    When he opens the entry screen, watch in hand
    Then the entry screen is ready within two seconds
    And the entry screen is ready for immediate typing
    And the entry screen shows the trend at a glance

  @driving_port @US-008 @contract-shape:bounded-change
  Scenario: A save lands exactly as it always has
    Given Clemens has unlocked the tracker with his passphrase
    And his weight has been falling for the last two weeks
    And the entry screen wears the calm theme
    And the entry screen shows the trend at a glance
    When he logs "82.1" for today
    Then he sees the confirmation "Saved: 82.1 kg — Thu 23 Jul"
    And the glance refreshes in place with the save
    And today holds exactly one entry of 82.1 kg

  @driving_port @error @US-008 @contract-shape:unbounded-preservation
  Scenario: A rejected save is turned away exactly as before
    Given Clemens has unlocked the tracker with his passphrase
    And his weight has been falling for the last two weeks
    And the entry screen wears the calm theme
    When he logs "824" for today
    Then the save is rejected because the value must be between 30.0 and 250.0 kg
    And nothing is stored
    And his typed value is kept for correction

  @driving_port @US-008 @contract-shape:pure-function
  Scenario: The door wears the same clothes
    When he visits the tracker in his browser
    Then the passphrase door is shown rather than a bare refusal
    And the door wears the calm theme
    And every control promises a comfortable touch target

  @driving_port @error @US-008 @contract-shape:unbounded-preservation
  Scenario: A wrong passphrase is refused as plainly as ever at the themed door
    Given the door wears the calm theme
    When he enters a wrong passphrase at the door
    Then the passphrase door is shown again with a visible rejection
    And his record stays hidden

  @driving_port @US-009 @contract-shape:pure-function
  Scenario: The graph dresses from the same palette
    Given Clemens has unlocked the tracker with his passphrase
    And his record holds an entry for every day from 1 July 2026 to 22 July 2026
    When he opens the graph
    Then the graph page wears the calm theme
    And the pressed control is marked by more than color alone
    And the chart draws every line from the tracker's single palette

  @driving_port @kpi @US-008 @US-009 @contract-shape:pure-function
  Scenario: Ink and surface keep their contrast promise in any light
    Given the tracker wears the calm theme
    When its daylight and dim-light appearances are examined
    Then every piece of text stands clearly against its surface
    And every edge, line and stroke stands apart from its surface

  @driving_port @kpi @error @US-008 @contract-shape:pure-function
  Scenario: Dim light is never served the daylight palette by accident
    Given the tracker wears the calm theme
    When its daylight and dim-light appearances are examined
    Then the dim-light appearance answers for every color the daylight one names

  @driving_port @kpi @US-008 @US-009 @contract-shape:pure-function
  Scenario: The finished look costs almost nothing
    Given the tracker wears the calm theme
    When the cost of the new look is tallied
    Then the whole look weighs no more than 10 kilobytes
    And no screen reaches beyond the tracker's own walls
    And the morning screen carries no new moving parts

  @driving_port @error @US-008 @contract-shape:bounded-change
  Scenario: A missing theme never blocks the morning weigh-in
    Given Clemens has unlocked the tracker with his passphrase
    And the entry screen wears the calm theme
    But the theme has gone missing
    When he logs "82.5" for today
    Then he sees the confirmation "Saved: 82.5 kg — Thu 23 Jul"
    And today holds exactly one entry of 82.5 kg
    And the morning screen still opens ready for typing
