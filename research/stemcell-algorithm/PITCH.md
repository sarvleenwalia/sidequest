# StemScope research evidence studio

Working product name. Built by Sarvleen Kaur Walia. Early research software prototype; no affiliation with a16z and no claimed endorsement.

## The pitch in one sentence

StemScope helps stem-cell research teams decide whether a single-cell dataset supports a prediction claim, then produces a reproducible analysis with the evidence and limitations visible.

## Thirty second introduction

I started with a question about Parkinson's disease in stem-cell-derived neurons. The first public dataset looked promising: thousands of cells and multiple samples. But the samples came from only two cell-line groups. That can support exploration, not a predictor that generalizes to new donors. I built StemScope to make that distinction explicit. It checks study design, keeps donors separate during evaluation, and turns the analysis into an evidence report. My next goal is to test whether labs can use it to review studies faster and avoid unsupported claims.

## The problem and initial customer

The proposed first user is a computational researcher in an iPSC disease-modeling lab who needs to review data quality and prediction validity before prioritizing follow-up work. The buyer hypothesis is a lab lead or research platform team. These are hypotheses to validate through interviews, not existing customers.

The costly decision is whether an apparent molecular pattern is strong enough to justify another experiment. Cell count alone cannot answer that: cells from the same donor are correlated, time points can be mislabeled as biological replicates, and experimental batches can track disease status.

## What exists today

- Executable count preprocessing, descriptive clustering, donor pseudobulk and regularized logistic-regression evaluation.
- Donor-disjoint cross-validation with training-only model feature selection.
- Metadata checks for repeated donor identities and complete batch/label confounding.
- A downloadable evidence report with inputs, hashes, settings, warnings and fold assignments.
- A real public-study audit and a separate synthetic-data model demonstration.
- A browser-based evidence viewer. It displays precomputed results; it is not a hosted analysis backend.

## What the demo proves

The software can ingest one actual public count matrix, check its alignment with published metadata, compute descriptive QC and surface a design that cannot validate a donor-generalized disease predictor. The synthetic run verifies execution and evaluation mechanics. It does not establish a Parkinson's biomarker, prospective fate prediction or treatment value.

Demo sequence: open the real-study audit, explain why thousands of cells do not solve the donor problem, open the synthetic benchmark, inspect donor fold assignments and conditional uncertainty, then download the reproducible report.

## Why this could become a product

The product hypothesis is a repeatable review workflow: import a study, establish the biological prediction unit, find design problems, run appropriate analyses, and hand an auditable report to a collaborator. The value would be saved researcher time and more defensible experimental decisions. Neither has been measured yet.

The initial implementation uses standard open-source methods. It has no proven algorithmic moat. A potential advantage would have to come from trustworthy metadata adapters, versioned study evidence, usability in real lab workflows and evidence of better review outcomes. More generic models or a polished dashboard alone would not establish defensibility.

## Alternatives and differentiation to test

Scanpy and Seurat provide established single-cell analysis workflows. Custom notebooks provide flexibility. Commercial analysis platforms offer hosted collaboration and data processing. StemScope's proposed focus is a narrow evidence-review workflow that makes donor independence and claim eligibility difficult to overlook. It must demonstrate an advantage in usability or review quality against an expert notebook workflow; feature overlap is not a competitive advantage.

## Business hypothesis

Start with an open research tool to earn feedback and reproducibility. Test a paid team workflow for shared study reviews, configurable validation policies, versioned reports and support. Pricing, willingness to pay and deployment needs are unknown. Do not quote revenue projections, market size or customer savings without research.

## Next validation milestones

1. Recruit three research teams for structured interviews and dataset-review exercises. Define their actual decision and time spent before writing a pricing plan.
2. Identify a study with independent donors in both conditions and comparable time points. Verify donor identity, genotype, batch and cell type from the original metadata.
3. Freeze the prediction task, exclusions, metrics, baseline and analysis plan before running it. Test a fixed model on an independent cohort if compatible data exist.
4. Compare review time, problems found and reproducibility against an expert's existing workflow. Success thresholds should be agreed with collaborators before testing.
5. Only after those results, decide whether to invest in hosted compute, access controls, collaboration and paid pilots.

## Funding conversation

The credible current ask is introductions to research collaborators and design partners. A financing ask needs a concrete budget, a verified team plan, customer evidence and a milestone schedule. No funding amount or traction is invented here.

## Questions to be ready for

**Is the model novel?** No. It is a standard baseline. The proposed product is a rigorous, usable evidence-review workflow, whose value still needs to be demonstrated.

**Does it predict Parkinson's disease?** Not on independent real donors yet. The real study reviewed so far cannot support that claim. Synthetic performance is labeled as synthetic.

**Does it predict future differentiation fate?** No. That requires longitudinal or lineage-linked outcomes. The implemented fate option classifies current supplied cell-type labels retrospectively.

**What stops Scanpy from doing this?** Nothing fundamental. The potential wedge is a simpler, repeatable study review with explicit eligibility decisions and evidence traceability. That must be tested against existing workflows.

**Where is the moat?** There is no demonstrated moat today. A defensibility hypothesis is better curated study metadata and validated workflow adoption, subject to data rights and customer evidence.

**Why should I care about rejecting a dataset?** A model score is useful only if the experiment supports its interpretation. This prototype makes an otherwise easy-to-miss failure visible before a prediction claim is made.

## Sources informing the pitch

[a16z's AI-in-bio evaluation framework](https://a16z.com/evaluating-ai-in-bio-how-to-know-whether-it-is-worth-the-work/) discusses data quality, differentiation, comparative methods, leakage and prospective evaluation. This pitch follows those questions; it does not claim investment readiness or guaranteed investor interest.

[GSE183248](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE183248) and its [original publication](https://doi.org/10.1038/s42003-021-02973-7) ground the first study review. Machine-readable measurements and input hashes are in real-data-review/real_data_audit.json.
