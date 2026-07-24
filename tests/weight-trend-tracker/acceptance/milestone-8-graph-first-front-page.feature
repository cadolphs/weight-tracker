Feature: The morning opens on the whole picture
  US-010 + US-011 (graph-first-home, Slice 01): the front page becomes the
  ambient picture -- the trend curve with its full lens and scale controls
  ABOVE the entry form, the glance line kept, and the last seven entries
  resting below -- without costing the five-second entry a single tap or
  second, and without ever polluting the deliberate trend-study counter
  (KPI-3, A19): ambient renders (page open at defaults, post-save repaint)
  add 0; only explicit lens/scale taps and History-page visits count.
  The ambient graph's presence is its own record (KPI-7, `home.graph.shown`,
  a server-side data-available-at-render proxy -- Q3, glance precedent).
  Client paint is one shared engine with the History page (ADR-008), so
  lens/scale behavior parity holds by construction; these scenarios pin the
  served contract: mount + controls + defaults, the telemetry-free data
  reads, the save response's `recent` hand-back, and the beacon's closed
  vocabulary (ADR-009). The keypad covering the graph on open is ACCEPTED
  (locked D6) and asserted nowhere.

  Background:
    Given the tracker is running with an empty record
    And today is Friday 24 July 2026
    And Clemens has unlocked the tracker with his passphrase

  @driving_port @US-010 @contract-shape:pure-function
  Scenario: The morning opens on the whole picture
    Given his weight has been falling for the last two weeks
    When he opens the entry screen
    Then the trend curve greets him above the entry form
    And the front-page graph offers both lenses and every time scale
    And the front-page graph opens on the Trend lens at "3M"
    And the front page drives the same graph engine as the History page
    And the entry screen is ready for immediate typing

  @pending @driving_port @kpi @real-io @adapter-integration @US-010 @contract-shape:bounded-change
  Scenario: An ambient morning never counts as deliberate study
    Given his weight has been falling for the last two weeks
    When he opens on the morning picture, logs "82.2" for today and pockets the phone
    Then the deliberate trend-study count for this week is 0
    And the morning graph delivery is on the record

  @pending @driving_port @driving_adapter @kpi @real-io @US-010 @contract-shape:bounded-change
  Scenario: Choosing a lens or scale is deliberate study
    Given his weight has been falling for the last two weeks
    And he has opened the entry screen
    When he chooses the "1Y" window and then the Raw lens on the front page
    Then both taps are counted as deliberate study

  @pending @driving_port @US-010 @contract-shape:bounded-change
  Scenario: Saving repaints the morning picture in place
    Given his weight has been falling for the last two weeks
    And he has seen the morning picture end at yesterday
    When he logs "82.2" for today
    Then he sees the confirmation "Saved: 82.2 kg — Fri 24 Jul"
    And the save hands back the refreshed recent list with today on top
    And the refreshed morning picture includes today
    And the repaint added nothing to the deliberate trend-study count

  @pending @driving_port @error @US-010 @contract-shape:bounded-change
  Scenario: A graph hiccup never blocks the log
    Given his weight has been falling for the last two weeks
    And the trend series cannot be computed
    When he opens the entry screen
    Then the entry screen is ready for immediate typing
    When he logs "82.2" for today
    Then he sees the confirmation "Saved: 82.2 kg — Fri 24 Jul"
    And today holds exactly one entry of 82.2 kg
    And the morning picture admits its trouble without marking the record
    And the morning graph delivery is still on the record

  @driving_port @error @US-010 @US-011 @contract-shape:pure-function
  Scenario: An empty record keeps the front page simple
    When he opens the entry screen
    Then no graph area is offered
    And no recent list is offered
    And the entry screen is ready for immediate typing

  @driving_port @property @kpi @US-010 @contract-shape:pure-function
  Scenario: The graph never taxes the entry
    Given his weight has been falling for the last two weeks
    When he opens the entry screen, watch in hand
    Then the entry screen is ready within two seconds
    And the entry screen is ready for immediate typing
    And the trend curve greets him above the entry form
    And nothing about the graph steals the morning focus

  @pending @driving_port @US-011 @contract-shape:bounded-change
  Scenario: The last week of numbers is one look away
    Given he logged 82.3 kg on 17 July 2026
    And he logged 82.5 kg on 18 July 2026
    And he logged 82.7 kg on 20 July 2026
    And he logged 82.4 kg on 21 July 2026
    And he logged 82.6 kg on 22 July 2026
    And he logged 82.4 kg on 23 July 2026
    When he logs "82.2" for today
    And he opens the entry screen
    Then the recent list shows his last 7 entries newest first
    And the recent list begins with "Fri 24 Jul — 82.2 kg"
    And Sunday 19 July 2026 appears nowhere in the recent list

  @pending @driving_port @US-011 @contract-shape:bounded-change
  Scenario: Today's save goes straight to the top
    Given he logged 82.4 kg on 23 July 2026
    And the entry screen's recent list begins with "Thu 23 Jul — 82.4 kg"
    When he logs "82.2" for today
    Then the save hands back the refreshed recent list with today on top

  @pending @driving_port @US-011 @contract-shape:pure-function
  Scenario: A young record shows what it has
    Given he logged 82.5 kg on 21 July 2026
    And he logged 82.4 kg on 22 July 2026
    And he logged 82.3 kg on 23 July 2026
    When he opens the entry screen
    Then the recent list shows exactly those 3 entries

  @pending @driving_port @US-011 @contract-shape:pure-function
  Scenario: Looking is not touching
    Given his record holds an entry for every day from 14 July 2026 to 23 July 2026
    When he opens the entry screen
    Then the recent list offers no way to edit or delete
    And every recent value equals the stored entry for its day

  @pending @driving_port @driving_adapter @error @real-io @US-010 @contract-shape:unbounded-preservation
  Scenario: A garbled study signal is turned away without a mark
    Given his weight has been falling for the last two weeks
    When a study signal arrives speaking words the tracker does not know
    Then the signal is refused as unintelligible, never as a breakdown
    And no deliberate study is recorded for it

  @pending @driving_port @driving_adapter @error @US-010 @contract-shape:unbounded-preservation
  Scenario: A stranger's study signal leaves no mark
    When a stranger sends a study signal without the passphrase
    Then the stranger is turned away at the door
    And no deliberate study is recorded for it
