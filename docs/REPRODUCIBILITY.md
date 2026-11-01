# Reproduction and verification

Python 3.10+ is sufficient for the analytical pipeline; no third-party runtime packages are required. The local full execution used CPython 3.12.10. Optional package installation uses setuptools and is not required for the documented commands.

Quick verification checks semantic fixtures and saved results. Full reproduction reads all source logs, validates SHA256 hashes, reconstructs intervals, generates measurements and derived tables, checks regenerated results, and compares them with the immutable reference. Run `python -B scripts/verify_all.py --data-root data --output reproduced` from the root. The output directory must be empty. `outputs/` is protected against use as the reproduction destination.

`build_review.py --output DIRECTORY` and `check_outputs.py --output DIRECTORY` both act on the named directory. `compare_outputs.py --reference outputs --actual DIRECTORY` compares every scientific reference file, including derived figure data and historical claim comparisons. It excludes only verification.json (runtime metadata) and fresh_reproduction_comparison.json (historical execution evidence). Missing or differing files fail. References are never silently updated.

Tests exercise lifecycle repair, occurrence separation, blocking inclusion, censoring, boundary clipping, zero-service ratios, fixed fleet multiplicity, exact near-tie thresholds, invalid resource overlaps, timestamp precision, and deliberate missing/modified result files. Full-data checks enumerate 405 service and 659 atomic conservation checks per corpus; the service checks also use an independent endpoint sweep. These validate calculation consistency, not universal causal interpretation.

CI runs tests and stored-result checks on Python 3.10, 3.12 and 3.13. A manually triggered full-reproduction job uses the bundled source data and performs the complete comparison. The existence of a workflow is not evidence that it has executed remotely. Keep the bundled data and `.gitattributes` when uploading to GitHub: automatic newline conversion would invalidate byte-level checksums.

Large canonical interval files are optional: add --intervals PATH to reproduce.py. For each corpus/run, the compressed CSV retains source IDs, exact interval endpoints, resource/service attribution and censoring flags.

Native figure build: `latexmk -pdf -interaction=nonstopmode -halt-on-error figures/preview.tex` from the repository root. A self-contained alternative is figures/preview_standalone.tex. Compilation status and any remaining limits are recorded in RELEASE_VALIDATION.json. The full manuscript is not included and is not part of the software build.
