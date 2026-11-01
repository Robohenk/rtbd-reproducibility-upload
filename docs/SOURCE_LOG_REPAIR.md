# Auditable source-log repair

An In progress event with an AGV resource and a production activity is a candidate. Repair is allowed only when it immediately follows a Complete event for that production activity at the same timestamp, and immediately precedes Transport Start and Waiting on the same AGV and timestamp.

The adapter changes the candidate activity to Transport and emits the three same-time transitions as Start, Waiting, In progress. Event IDs and timestamps remain unchanged. The source-order adjustment is necessary because the mislabeled In progress precedes the transport occurrence's Start in the original data. It is recorded explicitly and never implemented as a global lifecycle sort.

After that repair, only immediately consecutive In progress records with identical activity, resource, and timestamp are ignored. Their event IDs remain in the audit. Intervening Blocked/resume cycles remain intact, even when timestamps repeat. Every other unexplained lifecycle transition raises an error.

`outputs/repair_audit.csv` records corpus, run, case, event ID, action, original/repaired activity, timestamp in microseconds, and related event IDs. `outputs/input_manifest.csv` records per-log repair and duplicate counts. Originals are read-only inputs. The full filtered corpus is expected to contain the manuscript's 6,557 repair candidates and 402 consecutive duplicates; the raw corpus is audited independently and need not have identical counts.
