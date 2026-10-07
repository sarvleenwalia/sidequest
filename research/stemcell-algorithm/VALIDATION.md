# Implementation validation

Tested on Windows with Python 3.12 in an isolated environment. Exact scientific package versions are recorded in environment-lock.txt and verified-results/run_manifest.json.

All 10 automated tests passed:

1. High mitochondrial fraction and empty cells are excluded by QC.
2. Library-size normalization matches manually computed results.
3. Pseudobulk sums raw counts before normalization.
4. Variable-gene selection learns only from its supplied training rows.
5. Benjamini-Hochberg correction matches known values.
6. Fractional normalized input is rejected.
7. Donor groups do not overlap cross-validation training and test folds.
8. Insufficient class-specific donor counts are rejected.
9. Matrix Market input loads with explicit cell/metadata/gene order.
10. H5AD counts layers are preferred over normalized X.

An end-to-end CLI run completed on 560 synthetic cells, 300 genes and 16 synthetic donors. The planted signal produced 0.9375 held-out balanced accuracy and 1.0 ROC AUC; the balanced majority baseline was 0.5. Nineteen donor-label permutations completed. These are software demonstration results only. There is no real-patient accuracy estimate here.

The verified-results directory contains the current run. The cell embedding is a visualization of invented data. All four folds have disjoint training and test donors; raw input file SHA-256 hashes and run parameters were exported.

The new release also imports actual GSE183248 counts and metadata: 4,495 aligned cells and 18,097 genes. Counts are nonnegative integers, gene IDs are unique, and per-cell total counts match published metadata. This establishes technical import of that particular matrix, not successful cross-study harmonization or biological prediction.

Not validated: cross-study harmonization, biological pathway findings, batch correction, prospective fate prediction, early disease vulnerability, clinical use, causal mechanisms or treatment implications. Future validation must use independent real donor data and a prespecified scientific design.

Three additional metadata-audit tests passed: eligible declared metadata; repeated samples correctly counted as two donors rather than eight; complete batch/label confounding rejected. Total: thirteen passing tests across the pipeline and the new audit tool. The supplied synthetic metadata audit passes only these metadata feasibility checks.

Release update: a fourteenth test verifies the donor-bootstrap uncertainty helper. All fourteen tests passed together. The current synthetic run (release-results) reports a conditional 95% balanced-accuracy interval of approximately 78.6% to 100%; it resamples fixed out-of-fold donor predictions without model refitting. Neither this interval nor the synthetic AUC is real-patient validation.
