# Scientific verification report

The primary corpus comprises completed cases; all-raw-case results quantify selection effects. Throughput gains use the lower-fleet baseline denominator. Execution status is recorded in RELEASE_VALIDATION.json.

## Scientific evidence

| Measure | Filtered primary | All raw cases |
|---|---:|---:|
| Four-AGV mean throughput | 1288.1 | 1288.1 |
| Four-AGV mean transport queue | 55.76 | 69.70 |
| Four-AGV mean maximum production exposure/capacity | 88.6% | 95.0% |
| Four-AGV regimes: transport / mixed / production | 5 / 2 / 2 | 1 / 6 / 2 |
| Five-AGV regimes | 0 / 1 / 8 | 0 / 1 / 8 |
| Six-AGV regimes | 0 / 0 / 9 | 0 / 0 / 9 |

All raw cases include unfinished jobs, with open intervals right-censored at 24 hours. Runs 411, 413, 422, and 432 change from transport/low-production-exposure to mixed. Raw timestamps restricted to the same completed-case IDs reproduce all 27 filtered regime labels; their measurement differences are tiny. This identifies case omission, rather than timestamp precision, as the material source of the regime changes.

The filtered counts, throughput means, transport queue means, production utilization means, blocking means, example runs, factorial percentages, and selected threshold sensitivities reproduce to the manuscript's displayed precision. Whole-system claims of production unsaturation are not supported by low occupied exposure from completed cases alone. The label denotes low completed-case production exposure, not whole-system spare capacity.

## Corrected matched gains and screening

Using 100 × (P5-P4)/P4:

| Four-AGV filtered regime | n | Gain range |
|---|---:|---:|
| Persistent production pressure | 2 | 0.14–0.21% |
| Mixed pressure | 2 | 3.64–5.18% |
| Transport pressure / low production exposure | 5 | 8.94–40.38% |

Six runs exceed the 5% cutoff, including mixed-pressure run 431. For explicit reconstructed screening rules, utilization below 0.90 and the transport/low-production-exposure label make identical predictions across nine cases: five true positives, one false negative, three true negatives. Transport persistence alone gives six true positives, one false positive, and two true negatives. Each achieves 8/9 agreement; their precision/recall tradeoffs differ. These observations do not demonstrate superior binary discrimination for full RTBD.

`screening_predictions.csv` and `screening_scores.csv` therefore name the exact reconstructed rules.

## Startup/drain convention

The manuscript's general 27/27 crop-agreement claim requires an explicit convention. If only window evidence is cropped and the production-saturation discriminator remains the original full-24-hour measure, all tested crop variants preserve all 27 labels. If production utilization is also recomputed over the cropped horizon, agreement is 25/27 for hours 1–23, 24/27 for hours 2–22 and 0–22, and 27/27 for hours 2–24.

Both crop conventions are implemented and exported. The raw-log labels are stable for all four crop variants. All per-run outcomes and configurations are included, so an author can choose a different convention without reverse-engineering prose.

