# StemScope research evidence studio

This is an executable research prototype implementing the supplied abstract by Sarvleen Kaur Walia. It analyzes raw single-cell RNA-seq counts, creates donor-level expression profiles, and evaluates a model on held-out donors. It does not establish early Parkinson's vulnerability, predict future clinical outcomes, or recommend therapies.

Open [the live evidence studio](https://sarvleenwalia.github.io/sidequest/research/stemcell-algorithm/) to inspect the real-study review, clearly labeled synthetic benchmark and product pitch. [PITCH.md](PITCH.md) contains the short introduction, product hypothesis, milestones and reviewer questions. StemScope is a working product name, not an affiliation or endorsement.

The current release includes a real descriptive analysis of GSE183248: 4,495 cells and 18,097 genes from two cell-line groups. Raw-count totals match published metadata. Disease prediction is withheld because the experiment does not independently replicate donors within each condition. Fourteen software tests passed; no independent real-cohort prediction score has been established.

## What it does

1. Validates raw counts and matching metadata. Rejects normalized input, negative values, duplicate genes, missing donor IDs, and inconsistent donor disease labels.
2. Filters cells by detected genes and mitochondrial count fraction, then filters rarely expressed genes. Thresholds are configurable; inspect the exported QC before choosing them.
3. Normalizes each cell to 10,000 counts and applies log1p. Produces an SVD embedding and K-means clusters for descriptive exploration. Clusters are not biological cell-type annotations.
4. Optionally restricts analysis to an independently annotated cell type, such as dopaminergic neurons.
5. Sums raw counts by donor and label into pseudobulk profiles, then normalizes those profiles. Each donor has equal prediction weight. Cells are not independent biological replicates.
6. Runs stratified cross-validation with disjoint donors. Variance filtering, supervised gene selection, scaling and regularized logistic regression are fitted inside each training fold. Whole-dataset embeddings and differential results are never fed into the model.
7. Reports held-out predictions, balanced accuracy, majority baseline, binary ROC AUC, fold donor assignments and averaged coefficient magnitudes. Optional donor-level label permutations provide a null comparison for disease classification. Coefficients are predictive associations, not causes.
8. For binary disease labels with at least three donors per group, runs exploratory Welch tests on log-normalized donor pseudobulk, with Benjamini-Hochberg correction. This is a lightweight screening method, not a replacement for a covariate-adjusted negative-binomial differential-expression model.
9. Scores supplied gene panels descriptively and reports gene coverage. Included panels are small examples, not complete or validated pathway definitions. Replace them with versioned curated gene sets and record the source.

## Run

On GitHub, the source files are browsable directly. Download and extract `stemcell-algorithm.zip` in this folder for the complete package including synthetic demo-data and verified-results. See [DATASET_REVIEW.md](DATASET_REVIEW.md) for the first real-study eligibility review and the metadata audit command.

Requires Python 3.11 or newer. In a terminal in this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python stemcell.py demo --out demo-data
.\.venv\Scripts\python stemcell.py run --counts demo-data/counts.csv --metadata demo-data/metadata.csv --cell-type dopaminergic --min-genes 100 --pathways pathways.example.json --permutations 19 --synthetic --out demo-results
.\.venv\Scripts\python -m unittest -v
```

On macOS/Linux, replace `.\.venv\Scripts\python` with `.venv/bin/python`. `environment-lock.txt` records the exact package versions used for the delivered test run; use it instead of requirements.txt to recreate that environment on a compatible Python version.

The demo contains 560 invented cells, 300 invented/illustrative genes and 16 invented donors. The PD class has an intentionally planted expression shift. Its metrics test code behavior only and are not evidence about Parkinson's disease.

## Real inputs

CSV counts: one cell per row, one unique gene symbol per column, first column cell ID. Values must be raw integer counts, not TPM, log expression or scaled residuals. Metadata CSV must have the same cell IDs and these columns:

```csv
cell_id,donor_id,batch_id,status,cell_type
cell_001,donor_01,batch_01,control,dopaminergic
cell_002,donor_02,batch_01,PD,dopaminergic
```

`donor_id` identifies the original biological donor, not a cell, clone, sequencing library or technical replicate. `batch_id` must reflect real experimental batches. Additional metadata is retained in cell exports but is not modeled automatically. Confirm diagnosis, genotype, sex, age, time point, differentiation protocol, clone and batch from the source study before analysis.

```powershell
python stemcell.py run --counts counts.csv --metadata metadata.csv --task pd --label status --cell-type dopaminergic --folds 4 --pathways curated-pathways.json --out results
```

Minimum four distinct donors per class for the default four folds; this is a software feasibility threshold, not adequate statistical power. Every fold must have every class. Complete batch/label confounding causes an explicit failure. Partial confounding, differentiation time, genotype and donor characteristics still require study design review and external validation. The algorithm does not claim to remove batch effects.

Also accepts `.h5ad` with raw counts in `layers['counts']` (or `X` if raw) and required columns in `obs`. Gene symbols must be `var_names`. `.mtx` input requires cells-by-genes orientation, metadata rows in exactly matrix order, and `--genes genes.csv` with one symbol per row and no header. Transpose standard 10x genes-by-cells matrices upstream; do not guess orientation. Counts are read into memory, so large studies may require subsetting or more RAM.

## Cell fate versus Parkinson's status

The document title says cell-fate prediction but its abstract describes PD/control signatures. These are separate tasks.

`--task fate --label cell_type` evaluates retrospective classification of supplied cell-type labels across held-out donors. A donor can have multiple labeled pseudobulk profiles; these stay together in one fold. This is not future differentiation-fate prediction from an earlier state. That requires matched lineage/time-course outcome labels, a specified prediction time, and a longitudinal design that prevents future measurements entering training features. Unsupervised clusters cannot supply ground truth for that claim.

## Outputs

- `cell_qc.csv`: per-cell metrics and inclusion status.
- `cells_embedding.csv`, `clusters.png`: descriptive retained-cell embedding and clusters.
- `batch_label_counts.csv`: inspect batch/label overlap.
- `held_out_predictions.csv`: only out-of-fold predictions.
- `model_features.csv`: mean absolute standardized model coefficients across folds.
- `exploratory_differential_genes.csv`: binary PD donor comparisons when eligible.
- `pathway_scores.csv`, `pathway_coverage.json`: optional panel expression and coverage.
- `metrics.json`, `run_manifest.json`: results, limitations, settings and package versions.

The downloadable archive also includes `release-results/` (synthetic predictions with conditional donor-bootstrap uncertainty) and `real-data-review/` (actual public-study QC, descriptive embedding, sample summary and hashed provenance). `verified-results/` retains the earlier synthetic run for history. The viewer uses release-results and real-data-review, never silently combines their metrics.

To reproduce the real-study review and rebuild the viewer:

```powershell
python explore_geo.py --download --source geo-data --out new-real-review
python build_dashboard.py
```

The dashboard builder expects the included release-results and real-data-review directories. It creates a static HTML viewer of precomputed reports. It does not run remote analyses or collect uploaded datasets.

Outputs should go to a new directory for each run to avoid confusing old artifacts with current outputs. No model is presented as a deployable clinical predictor; this pipeline is for evaluating a research hypothesis.

## Scientific next steps

Obtain raw counts and trustworthy donor metadata; inspect QC, doublets, ambient RNA and cell-type annotations with a domain expert. This prototype does not automate doublet detection or ambient-RNA correction. Analyze like-for-like cell types and time points. Use donor-aware count-based differential expression with prespecified covariates, curated pathway enrichment and an independent cohort. Freeze model choices before external evaluation; don't tune on these reported folds. Use larger donor cohorts and confidence intervals before treating performance as stable. An early vulnerability claim additionally needs longitudinal or independently validated outcomes.

## References

- [Scanpy preprocessing and clustering](https://scanpy.readthedocs.io/en/latest/tutorials/basics/clustering.html): reference workflow for QC and normalization. This implementation uses SciPy/scikit-learn, not Scanpy itself; SVD/K-means are deliberately lightweight alternatives.
- [Scanpy total-count normalization](https://scanpy.readthedocs.io/en/stable/generated/scanpy.pp.normalize_total.html).
- [scikit-learn grouped cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html): donors must not overlap training and testing.
- [GEO GSE183248](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE183248): real descriptive import completed; cross-donor disease classifier evaluation rejected. Twelve experimental samples do not automatically mean twelve independent donors. See DATASET_REVIEW.md for the measured import and design limitations.

The abstract's claims of novelty, precise early signatures and direct therapy impact have not been established by this implementation.
