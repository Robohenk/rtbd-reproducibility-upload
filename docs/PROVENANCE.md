# Provenance

This implementation reconstructs the measurement definitions in *Resource–Temporal Bottleneck Diagnosis from Manufacturing Event Logs*. The reference corpus consists of 27 completion-filtered XES logs and 27 raw simulation logs. Source-file SHA256 hashes identify all inputs in `data/checksums.json`; public version metadata is preserved in `data/source_record.json`.

The original source snapshot was Process_Mining_2026-main.zip, SHA256 c3ff41833c758acd63149dbfbdd697692239c169a0bed6542b06ec4fd98c63e1. Its exploratory notebook was inspected, but is not required by or executed in the reproducibility pipeline. The native pipeline diagram originates in the manuscript. No original Git commit identity is inferred from the ZIP.

The primary analysis concerns completed cases. All-raw-case and raw-retained-case controls quantify selection and timestamp effects. Baseline-relative gains, deterministic lifecycle repairs, exact integer-microsecond conservation and both crop conventions are documented explicitly. Statistical association in these logs does not establish causal bottlenecks or generalization to other plants.

Software is MIT licensed. Original dataset terms and attribution are in data/README.md. The software is cited collectively as RTBD contributors until a named software creator list is established. Manuscript authorship is not automatically software authorship.
