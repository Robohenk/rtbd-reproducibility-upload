# Resource–Temporal Bottleneck Diagnosis

This repository provides the implementation, verification tests, reference results, and native figure sources for *Resource–Temporal Bottleneck Diagnosis from Manufacturing Event Logs*. The primary analysis uses completion-filtered logs. Analyses of all raw cases and raw events restricted to completed-case IDs quantify sensitivity to case selection.

Version 0.1.0 is a reproducibility artifact for this specific flexible job-shop dataset. Its adapter assumes the source lifecycle grammar and a 24-hour simulation horizon. The scientific definitions and parameters are documented in `docs/METHOD_PARAMETERS.md`.

## Requirements

Python 3.10 or later. Analytical commands use only the standard library: no installation or notebook execution is required. The tested Python version and full-run report are in `docs/RELEASE_VALIDATION.json`. Run commands from this directory.

## Quick verification (no dataset required)

```console
python -B scripts/verify_manifest.py
python -B -m unittest discover -s tests -v
python -B scripts/check_outputs.py --output outputs
```

This validates the distributed files, semantic tests, and stored reference results. It does not recalculate results from event logs.

## Full reproduction

This ZIP includes all 54 source files under `data/FilteredFiles/` and `data/RawData/`. After extraction, full analytical reproduction works offline. Run:

```console
python -B scripts/verify_all.py --data-root data --output reproduced
```

This regenerates all 27 configurations for three corpus variants, derives tables and figure data, checks the new results, and compares them against every scientific reference file. Missing or differing results produce a failing exit code. The destination must be empty. The frozen `outputs/` directory is preserved. On the verification machine the original complete pipeline took about two minutes; runtime varies by computer.

For separate steps:

```console
python -B scripts/reproduce.py --data-root data --output reproduced
python -B scripts/build_review.py --output reproduced
python -B scripts/check_outputs.py --output reproduced
python -B scripts/compare_outputs.py --reference outputs --actual reproduced
```

Optional canonical intervals: add `--intervals intervals` to `reproduce.py`. The two-row sample in `data/sample/` illustrates format and is not sufficient for full reproduction. Throughput gain is calculated as `(P5-P4)/P4`.

## Figures

TikZ/PGFPlots sources read the exact CSV tables in `outputs/figure_data/`. Compile from the repository root:

```console
latexmk -pdf -interaction=nonstopmode -halt-on-error figures/preview.tex
```

Alternatively use the self-contained `figures/preview_standalone.tex`; regenerate it with `python scripts/make_standalone_preview.py`. See `docs/RELEASE_VALIDATION.json` for actual build status. The primary plots use filtered data; the raw landscape is a sensitivity comparison. Blocking is supplementary.

## Results and documentation

- `src/rtbd/`: reconstruction, adapter, evidence and regime logic.
- `config/`: baseline values; all executed variants are exported with results.
- `outputs/`: frozen reference outputs, event-level repair audit and exact conservation records.
- `tests/`: hand-calculated semantic fixtures and comparison failure tests.
- `docs/DATA_DICTIONARY.md`: columns, units and interpretation.
- `docs/VERIFICATION_REPORT.md`: scientific findings and scope limitations.
- `docs/REPRODUCIBILITY.md`: commands and verification details.

The legacy `outputs/historical_claim_ledger.csv` compares against an earlier manuscript snapshot. It is not a pass/fail checklist for a final published paper; see `docs/CLAIM_TARGETS.md`.

## Paper, license and citation

Related manuscript: Arda Akyazi, Rob H. Bemthuis, and Faiza A. Bukhsh, *Resource–Temporal Bottleneck Diagnosis from Manufacturing Event Logs*. A final public manuscript identifier was not available when this artifact was prepared. This package does not contain the manuscript or assert correspondence to an unspecified final paper version.

Software is distributed under the MIT license (`LICENSE`). Original data and the sample have separate CC BY 4.0 terms and attribution (`data/README.md`). `CITATION.cff` identifies the software collectively as RTBD contributors; named software creators were not separately confirmed. No repository URL or archival DOI has been fabricated. Add the final URL/DOI to citation metadata when publishing.

## Declaration of AI assistance

OpenAI Codex was used to assist with examining the supplied manuscript
and repository, developing and revising the reproducibility code,
implementing verification checks, drafting documentation, and preparing
the release package. This assistance included substantive code generation
and analysis, rather than language editing alone.

Verification performed during preparation is recorded in
docs/RELEASE_VALIDATION.json. The human authors remain responsible for
reviewing the artifact, interpreting the results, and approving its
release. AI tools are not listed as authors.
