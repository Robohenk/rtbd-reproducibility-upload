# Dataset, attribution and access

Original dataset: Rob Bemthuis, Martijn Koot, Martijn R. K. Mes, Faiza A. Bukhsh, Maria-Eugenia Iacob, and Nirvana Meratnia. *Data underlying the paper: An agent-based process mining architecture for emergent behavior analysis*. 4TU.ResearchData, version 2. DOI: https://doi.org/10.4121/12708839.v2.

The public version record identifies the original files as CC BY 4.0: https://creativecommons.org/licenses/by/4.0/. That license applies to original data and the sample, independently of the software's MIT license. No source event values are changed; repairs occur in memory and are recorded separately. The fetched metadata and original citation are preserved in `source_record.json`.

## Included files and optional download

The release ZIP includes all 54 source files from the supplied repository snapshot. Each bundled file matches `checksums.json`, and this exact corpus was used for the successful full reproduction. No network connection is required for analytical reproduction. The separate `sample/` excerpt contains the original header and first two event records, including the original byte formatting.

The public version metadata was retrieved successfully. Its archive endpoints returned HTTP 504 during release preparation, so a fresh download and byte comparison against that public version could not be completed. The bundled snapshot is verified against the recorded source checksums; public archive equivalence is not asserted. The downloader below is optional for restoring missing inputs, and rejects files whose hashes differ.

From the repository root:

```console
python -B scripts/download_data.py
```

The downloader fetches pinned file IDs, locates the expected filenames, and checks every extracted file against `checksums.json` before installing the 54 files. Existing files with different hashes are not overwritten.

Manual alternative: download and extract these two archives, preserving their filenames:

- RawData.zip: https://ndownloader.figshare.com/files/28325148
- FilteredFiles.zip: https://ndownloader.figshare.com/files/28325151

The resulting layout must be `data/RawData/Experiment411.txt` through `Experiment633.txt` (27 files) and `data/FilteredFiles/411.xes` through `633.xes` (27 files). The full pipeline validates source hashes before analysis. `docs/RELEASE_VALIDATION.json` records whether remote acquisition and matching were successfully tested for this release.

Configuration digits encode fleet {4,5,6}, direction {1 Forward,2 Backward,3 Bidirectional}, and dispatch {1 Random,2 Longest-Waiting-Time,3 Nearest-Vehicle}. Filtered logs contain completed cases; raw logs contain 1,450 cases per run. Timestamp precision is preserved. Join case IDs with run IDs because product labels repeat across experiments.

`sample/Experiment411_first3lines.txt` is an exact excerpt: header plus two event records. It is a format illustration, not a complete reproduction dataset.
