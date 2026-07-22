Feature: A morning weigh-in becomes a lasting record
  The walking skeleton (Slice 01): Clemens captures today's weight from his phone,
  the tracker keeps it, and he sees it confirmed in his history — the full vertical
  loop through the production composition root with a real record store.

  @walking_skeleton @driving_port @driving_adapter @real-io @US-001 @contract-shape:bounded-change
  Scenario: Morning weight is captured in seconds and lands in the record
    Given the tracker is running with an empty record
    And today is Tuesday 21 July 2026
    And Clemens has unlocked the tracker with his passphrase
    When he logs "82.4" for today
    Then he sees the confirmation "Saved: 82.4 kg — Tue 21 Jul"
    And today holds exactly one entry of 82.4 kg
    And today's entry of 82.4 kg appears at the top of his history
