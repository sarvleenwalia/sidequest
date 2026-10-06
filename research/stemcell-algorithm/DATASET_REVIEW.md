# First real data eligibility review

## Decision

Do not use GSE183248 to report a cross-donor Parkinson's prediction score. It can support descriptive exploration of differentiation and the two specific cell lines. The implemented four-fold classifier needs at least four independent donors in each class; time points, cells and clones cannot replace independent donors.

This review uses the published study and GEO sample listing. No real expression matrix has been downloaded, imported or analyzed, and no biological finding is claimed.

## Evidence

[GEO GSE183248](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE183248) lists twelve sequencing samples. Sample titles repeat two line identifiers, 17608/6 and ND40066-8, at different differentiation time points. These twelve samples should not be encoded as twelve donors.

The [original study](https://doi.org/10.1038/s42003-021-02973-7), also [available from the authors' institutional repository](https://escholarship.org/uc/item/0t01p433), describes sequencing a PINK1-ILE368ASN line and a control line. Disease/genotype and line identity are inseparable in this comparison. A classifier could recognize differences between these lines without demonstrating generalization to unrelated people.

The study is therefore unsuitable for the current cross-donor classifier evaluation. This conclusion concerns the proposed prediction experiment, not the value of the original mechanistic study.

## What the next eligible study must supply

- Raw cell-by-gene counts with documented cell IDs and gene identifiers.
- Original donor identity and disease status independent of sample/clone/library IDs.
- Multiple independent donors per group and overlapping experimental batches.
- Comparable differentiation time points and protocols across disease groups.
- Cell-type annotations or sufficient metadata to establish a comparable population.
- A stated reuse policy and a record of sample exclusions.

For the default four-fold experiment, at least four donors per class are required by the software. A larger cohort and independent validation remain necessary for a reliable scientific claim. If the eventual study instead contains adult postmortem brain tissue, label it as a different validation setting; do not call it an early iPSC-derived neuronal model.

## New metadata audit tool

Before importing an expression matrix:

```powershell
python audit_metadata.py --metadata your-metadata.csv --label status --folds 4 --out eligibility.json
```

This checks declared donor labels, class-specific donor counts and batch overlap. Passing means only that these metadata checks pass, not that donor labels or the experiment are biologically valid. You must establish that donor_id truly identifies the original donor from the source publication.

The audit on the included synthetic metadata passes with eight invented donors per class. The synthetic dataset does not satisfy the real-data stage.
