# Output dictionary

All tables are UTF-8 CSV with an explicit header. `corpus` is `filtered` (selected primary XES corpus), `raw` (all raw cases), or `raw_retained` (raw events restricted to filtered case IDs). `run` is the three-digit experiment identifier; join on corpus plus run, and on case/occurrence where appropriate. Resource names preserve source spelling. Floating-point outputs are not rounded before figure export.

| File | Granularity and principal fields |
|---|---|
| input_manifest.csv | One corpus/run: source filename, SHA256, case/event/throughput counts, repairs, duplicates, censored intervals. |
| repair_audit.csv | One adapter action: source event ID, case, original and corrected activity, time_us, related IDs, action. |
| conservation_checks.csv | One service/channel or observed resource/channel: total_us, difference_us, independent sweep_difference_us for service rows. |
| window_evidence.csv | One corpus/run/window/service group: start_hour; queue, occupied, blocked and active seconds; normalized utilization and blocking; mean_queue in jobs; delay_ratio; binary capacity/delay/joint membership; transport-pressure flag for AGV rows. |
| resource_evidence.csv | One corpus/run/service group: full-horizon exposures in seconds, utilization, mean_queue, joint_persistence. |
| run_summary.csv | One corpus/run: throughput, case count, factorial digits, transport_persistence, wp_persistence, production_utilization, fleet_utilization, transport_queue, fleet_blocking, regime, independent congestion flag. |
| regime_counts.csv | One corpus/fleet: counts for transport, mixed, production, indeterminate. |
| fleet_summary.csv | Means over all nine configurations at a fleet size; utilization values are proportions. |
| blocking_summary.csv | Mean blocked fleet-capacity fraction over the three dispatch policies, by corpus/fleet/direction. |
| matched_contrasts.csv | One matched 4→5 or 5→6 comparison: absolute products, difference, baseline-relative gain_percent, legacy destination-relative percent, and >=5% high_response flag. Regime refers to the lower-fleet run. |
| factorial_decomposition.csv | Exact observed design sums of squares and percentage shares; no inferential residual/error variance or p-values. |
| sensitivity_runs.csv | One corpus/run/configuration variant: same derived regime measures as run_summary. |
| robustness_summary.csv | Count and IDs of primary-regime changes against each corpus's own baseline. Congestion changes are not included in this agreement count. |
| corpus_comparison.csv | Raw or raw-retained minus filtered values and regime-change flag. Utilization deltas are proportions (multiply by 100 for percentage points). |
| screening_predictions.csv | Nine four-AGV comparisons per corpus: approved gain target and three explicitly reconstructed binary rules. |
| screening_scores.csv | TP/FP/FN/TN and accuracy for those rules; no confidence intervals or held-out performance claim. |
| historical_claim_ledger.csv | Earlier manuscript snapshot numerical target (see CLAIM_TARGETS.md), computed value, display-rounding tolerance, status and interpretation note. Crop rows distinguish two reconstructed conventions. |
| figure_data/ | Exact primary figure coordinates; raw/ supplies the sensitivity alternative. Throughput means average direction, blocking means average dispatch. Landscape has one row for each run; subset files are exact partitions by regime and fleet. |

`production_utilization` is maximum normalized production occupied exposure, not mean utilization across machines. In the filtered corpus its numerator excludes unfinished cases; it must not be equated with total machine use. `transport_queue` is job-seconds of transport demand divided by observation duration, including demand physically waiting at production outputs. `wp_persistence` is joint simultaneous Welding–Painting persistence, not the average of their individual persistence scores. All persistence and intensity fields are proportions between zero and one. `delay_ratio` may contain `inf`, representing demand with zero occupied service, never a missing value.

Canonical interval exports contain `case`, `occurrence`, `activity`, `kind`, physical `resource`, demanded/service `group`, exact microsecond `start` and `end`, source `open_id`/`close_id`, and `censored`. Time intervals are half-open. The corpus/run identifiers are in the filename. A censored interval has an empty closing event ID; it ends at the observation horizon, not at an invented completion.
