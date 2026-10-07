# Research demo release

StemScope is a working name for the evidence viewer around this research prototype.

This release adds an actual GSE183248 import and descriptive data audit, an interactive evidence dashboard, a concise pitch and question preparation, and conditional donor-bootstrap uncertainty for the synthetic benchmark. It retains the explicit rejection of real disease classifier evaluation on the two-line study.

The uncertainty interval resamples whole donors from fixed out-of-fold predictions. It does not refit models and must not be described as external-validation uncertainty. It is illustrative because the included classifier benchmark is synthetic.

The dashboard is static and embeds only precomputed evidence. It performs no remote analysis, handles no clinical records and claims no live AI generation. Use the command-line scripts to reproduce the underlying analyses.
