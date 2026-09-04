Feature: The axis tells the truth about movement
  US-015 (y-axis-floor, Slice 01): the smoothed trend removes the daily noise,
  but an axis zoomed to the data puts it straight back -- a month that moved
  200 g fills the whole chart and reads as a rollercoaster, on the morning
  glance and on the History page alike. From now on every chart is offered an
  HONEST axis: at least 2.0 kg tall, the data centred inside it, both bounds
  snapped outward to the half-kilogram grid so no edge ever reads 77.42234
  (D6-D9, ADR-012). A stalled month is a calm, near-flat stroke; a real loss
  still slopes; a long or steep window keeps its ordinary range and gains only
  clean edges. One rule, both lenses, both surfaces, every scale -- the axis
  rides the very same series read the shared engine already fetches, so parity
  is by construction and the plotted values themselves never move (G-3).
  What the phone paints -- the engine handing the pair to the chart, its
  shape guard, the cached script -- is client-structural and verified at
  dogfood (the client-paint precedent D-15). These scenarios pin what the
  tracker SERVES: the axis offered beside each windowed series, falsifiable
  at the boundary, never a convention inside a script.

  Background:
    Given the tracker is running with an empty record
    And today is Friday 4 September 2026
    And Clemens has unlocked the tracker with his passphrase

  @driving_port @US-015 @contract-shape:pure-function
  Scenario: A stalled month reads flat
    Given his weight has hovered around 77.2 kg from 1 August 2026 to 4 September 2026
    When he views the Trend lens at "1M"
    Then the axis runs from 76.0 to 78.5
    And the axis is at least two kilograms tall with every plotted point inside
    And the plotted line fills at most 10 % of the axis

  @driving_port @US-015 @contract-shape:pure-function
  Scenario: A real month of loss still slopes
    Given his entries fall by 0.4 kg each week from 80.0 kg between 1 July 2026 and 4 September 2026
    When he views the Trend lens at "1M"
    Then the axis is between 2.0 and 3.0 kg tall
    And the axis is centred within 0.25 kg of the data midpoint
    And the plotted line covers at least 40 % of the axis

  @driving_port @US-015 @contract-shape:pure-function
  Scenario: A long window keeps its ordinary range, with clean edges
    Given his entries fall by 0.2 kg each week from 82.3 kg between 6 March 2026 and 4 September 2026
    When he views the Trend lens at "6M"
    Then the axis is the plotted range padded by a tenth each side, snapped outward to the half-kilogram grid
    And every bound is a clean multiple of half a kilogram

  @driving_port @US-015 @contract-shape:pure-function
  Scenario: A raw week is noise inside a band
    Given his last seven mornings read 77.0, 77.4, 76.9, 77.3, 77.1, 76.8 and 77.2 kg
    When he views the Raw lens at "1W"
    Then the axis runs from 76.0 to 78.5
    And the axis is at least two kilograms tall with every plotted point inside

  @driving_port @error @US-015 @contract-shape:pure-function
  Scenario: A missing day stays a gap beneath the honest axis
    Given he logged 77.0 kg on 29 August 2026
    And he logged 77.4 kg on 30 August 2026
    And he logged 76.9 kg on 31 August 2026
    And his record has no entry for 1 September 2026
    And he logged 77.1 kg on 2 September 2026
    And he logged 76.8 kg on 3 September 2026
    And he logged 77.2 kg on 4 September 2026
    When he views the Raw lens at "1W"
    Then the days from 1 September 2026 to 1 September 2026 show no entries
    And the axis is the honest range for what is plotted
    And the axis runs from 76.0 to 78.5

  @driving_port @property @US-015 @contract-shape:pure-function
  Scenario: Toggling lens or scale never changes the rule
    Given his entries fall by 0.4 kg each week from 84.0 kg between 1 March 2026 and 31 May 2026
    And his weight has hovered around 77.2 kg from 1 June 2026 to 4 September 2026
    When he taps through every lens at every scale
    Then every axis on the tour obeys the one honest rule
    And every tap keeps its chosen lens and scale

  @driving_port @error @US-015 @contract-shape:pure-function
  Scenario: Axis bounds are clean numbers
    Given he logged 77.1 kg on 3 September 2026
    And he logged 77.4 kg on 4 September 2026
    When he views the Raw lens at "1W"
    Then the axis runs from 76.0 to 78.5
    And every bound is a clean multiple of half a kilogram

  @driving_port @property @error @US-015 @contract-shape:pure-function
  Scenario: A lone entry still stands on an honest axis
    Given he logged 77.2 kg on 2 September 2026
    When he views the Raw lens at "1W"
    Then the axis runs from 76.0 to 78.5
    And the axis is at least two kilograms tall with every plotted point inside

  @driving_port @property @error @US-015 @contract-shape:pure-function
  Scenario: A perfectly steady week is a flat line, never a zero-height axis
    Given his record holds a steady 77.0 kg from 29 August 2026 to 4 September 2026
    When he views the Trend lens at "1W"
    Then the axis is exactly 2.0 kg tall, centred on 77.0
    And the axis is the honest range for what is plotted

  @driving_port @error @US-015 @contract-shape:pure-function
  Scenario: An empty window offers no axis
    Given he logged 77.2 kg on 1 July 2026
    When he views the Raw lens at "1W"
    Then the days from 29 August 2026 to 4 September 2026 show no entries
    And no axis is offered in either lens at "1W"

  @driving_port @error @US-015 @contract-shape:pure-function
  Scenario: An empty record invites, and offers no axis
    When he views the Raw lens at "1W"
    Then he is invited to log his first weight
    And no axis is offered in either lens at "1W"

  @driving_port @error @US-015 @contract-shape:pure-function
  Scenario: Exactly two kilograms of movement is where the floor steps aside
    Given he logged 76.0 kg on 3 September 2026
    And he logged 78.0 kg on 4 September 2026
    When he views the Raw lens at "1W"
    Then the axis runs from 75.5 to 78.5
    And the axis is the plotted range padded by a tenth each side, snapped outward to the half-kilogram grid

  @driving_port @property @kpi @US-015 @contract-shape:unbounded-preservation
  Scenario: The axis frames the line and never moves it
    Given his entries fall by 0.4 kg each week from 80.0 kg between 1 July 2026 and 4 September 2026
    When he views the Trend lens at "1M"
    Then the plotted line is exactly the line the record has always told
    And every load shows the identical trend line at "1M"
