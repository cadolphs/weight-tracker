# Weight Tracker

A single-user tracker: one weight per day, a smoothed trend over the whole record, and a quick read on which way it is going.

## Language

**Entry**:
One weight for one calendar day. Re-saving a day replaces its entry.
_Avoid_: reading, measurement, log

**Record**:
Every entry the tracker holds, oldest to newest. Never windowed.
_Avoid_: history, dataset

**Trend**:
The smoothed series over the record, one value per calendar day from the first entry day to the last. Derived on every read, never stored.
_Avoid_: smoothed weight, filtered series

**Glance**:
The trend's end value and its weekly rate, as of the last entry day.
_Avoid_: summary

**Picture**:
Everything the pages know about the record, derived from one smoothing of all entries: the trend, the glance, the trend by day, the recent head, the whole-record weights, and the earliest pickable day.
_Avoid_: projection, view, snapshot

**Trail**:
The append-only record of events the tracker keeps beside the record, read only as the KPI report. Lives in the `events` table; one module (`core/trail.py` + `shell/trail.py`) owns its vocabulary, its one write entry point and its one read.
_Avoid_: telemetry store, log, audit log

**Event**:
One row on the trail: when it was stamped, which name it carries, and the payload its emitter gave it. Names come from a closed vocabulary; routes decide when an event is marked (ADR-009).
_Avoid_: telemetry, metric, signal (the beacon's body is a signal until it passes the vocabulary gate and becomes an event)

**KPI report**:
What `GET /stats` serves: the trail's counters, framed as all-time or as the rolling week ending today, plus the speed summary. A pure derivation of the events and the day it is read on (ADR-015).
_Avoid_: stats, metrics, dashboard
