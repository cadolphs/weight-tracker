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
