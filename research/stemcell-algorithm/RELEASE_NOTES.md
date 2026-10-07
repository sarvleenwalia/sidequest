# Research demo release

Prototype 03 fixes single-label donor splitting: stratify unique donors directly, then map those donors back to profiles. The approximate grouped splitter could omit a class in a small test fold under the browser's scikit-learn version. Multi-label donor tasks retain grouped splitting and explicit class checks. Fifteen tests pass, including minimum-cohort class balance and donor separation. The regenerated desktop synthetic run in `release-results-v3` yields 100% balanced accuracy on planted data (558 cells retained from 560); this is software demonstration data, not disease validation. Earlier report folders are historical runs.

StemScope is a working name for the evidence viewer around this research prototype.

This release adds an actual GSE183248 import and descriptive data audit, an interactive evidence dashboard, a concise pitch and question preparation, and conditional donor-bootstrap uncertainty for the synthetic benchmark. It retains the explicit rejection of real disease classifier evaluation on the two-line study.

The uncertainty interval resamples whole donors from fixed out-of-fold predictions. It does not refit models and must not be described as external-validation uncertainty. It is illustrative because the included classifier benchmark is synthetic.

The study and benchmark tabs embed precomputed evidence. The Run analysis tab now executes the same Python CSV pipeline in a browser worker using Pyodide. Selected files stay in browser memory; scientific libraries download from jsDelivr. The runner includes input errors, progress, cancellation and a results ZIP. It is limited to 20 MB count CSVs and 5 MB metadata CSVs; use the command-line package for larger studies or MTX/H5AD. Browser package versions are recorded separately in the run manifest; numerical results can differ from the locked desktop environment.

Navigation now preserves the selected tab in the URL, supports browser Back and keyboard arrow keys, and provides a manual pitch-copy fallback when clipboard access is blocked.
