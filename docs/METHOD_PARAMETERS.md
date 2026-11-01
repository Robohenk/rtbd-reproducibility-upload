# Measurement specification

All interval boundaries use integer microseconds, preserving source precision. The observation horizon is the local simulation day [00:00,24:00). Input must contain a single date and monotonically ordered events within each case. Equal-time source order is preserved except for the explicitly audited same-time repair. No event timestamp or duration is rescaled.

Each Start opens an activity occurrence. Waiting → first In progress defines queue exposure. First In progress → Complete defines occupied service, including blocked time. Blocked → resume/Complete defines non-overlapping blocked subintervals. Unknown activities, orphan transitions, unexplained repeated starts, resource changes, and overlapping use of a unit resource cause a failure rather than silent data loss. Arrival/Drain are structural events; Drain/Complete counts finished products.

For unfinished raw cases, open queue, occupied, and blocked intervals are right-censored at 24 hours and tagged `censored`. A closed queue followed by unfinished service remains a closed queue. The reconstruction does not infer events after the observation horizon.

Queue intervals retain the Waiting event's physical resource. Their demanded service group is the occurrence activity: all Transport queues map to the AGV fleet, including waits at production outputs. Sawing, Drilling, Welding, and Painting queues map to their own production services. Occupied/blocked intervals retain the service-start AGV or production machine.

Capacity uses occupied/(multiplicity × window duration). Production multiplicity is one; fleet multiplicity is the first experiment digit, including idle vehicles. Mean queue occupancy is queue exposure/window duration. Delay is queue/occupied; zero/zero is zero and positive/zero is infinity. Blocking intensity is blocked/(multiplicity × duration). Active duration is occupied minus blocked, never occupied plus blocked.

Production co-dominance compares only the four production services. Both the utilization floor and near-tie tolerance must hold. Delay dominance requires the configured queue/occupied threshold. Joint dominance is their intersection; Welding–Painting persistence counts windows in which both are joint-dominant. Transport persistence counts windows above the transport queue/occupied threshold. Regime rules preserve an indeterminate outcome. Congestion is an independent modifier.

Baseline values are in `config/baseline.json`. `capacity_threshold` controls window-level co-dominance; `production_saturation` controls full-horizon regime interpretation. They are separate variables even though both default to 0.90. Co-dominance comparisons use exact rational thresholds applied to integer exposures to avoid near-tie floating-point artifacts.

Sensitivity runs change one parameter at a time. Cropped variants cover hours 1–23, 2–22, 0–22, and 2–24. Plain `hours=` variants clip intervals and recalculate all denominators on the retained horizon. Variants suffixed `full_horizon_saturation` instead retain the baseline 24-hour production-utilization discriminator while cropping the persistence evidence. Both conventions are exported, and both results are reported. These are the explicitly implemented variants. All executed configurations are exported in `outputs/analysis_configs.json`.

Matched percentage gain is 100 × (P5-P4)/P4. The legacy P5 denominator is exported separately solely to explain the manuscript discrepancy. Exact descriptive factorial variation includes all main effects, two-way interactions, and the three-way interaction; no inferential p-values are produced.
