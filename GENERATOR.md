# Generator specification

## Inputs

Discipline, specific interests, experience, available weeks, software/compute access, and optional preferred output medium. The prototype exposes the first four; future feasibility checks must capture the rest.

## Future AI pipeline

1. Retrieve verified student examples and primary research appropriate to the discipline.
2. Extract question, method, artifact, evaluation, resources, and limitations into source records.
3. Propose distinct directions: reproduction with an extension; application in a new context; a novel question with uncertain feasibility.
4. Adapt the scope to the student and identify missing prerequisites or blocked data access.
5. Validate references and reject fabricated sources, unbounded scope, inaccessible dependencies, and unsupported novelty claims.
6. Return three meaningfully different briefs. Regeneration should change the underlying question or approach, not just the title.

## Output contract

Title; discipline; research question; motivation; artifact; method; baseline or counterevidence; evaluation; prerequisites; data/source access; first milestone; time estimate and assumptions; extension; source lineage; claimed contribution; explicit uncertainties.

## Discipline-aware review

- Computing: correct behavior, meaningful constraints, reproducibility, failure analysis.
- Empirical science: hypothesis, controls, data quality, uncertainty.
- Economics/social science: identification assumptions, confounding, robustness, limits of causal claims.
- Humanities: provenance, close reading, alternative interpretations, transparent corpus selection.
- Design/arts: intended audience, creative decisions, critique, documented iteration. Numerical metrics are optional.

## Quality rubric

Score specificity, student feasibility, depth, inspectable outcome, evaluation quality, and source grounding separately. Review the claimed difference from prior work; do not treat a numerical score as a novelty certificate.

## Acceptance checks

Every URL resolves to a supporting source. Every brief has a feasible first milestone and a way to assess the outcome. No hardware is required. Different disciplines preserve their own standards. Unavailable data and compute are disclosed. AI-generated suggestions are identified. Failure returns an actionable error rather than fabricated content.

## Current catalog expansion
303 named directions across 30 fields. 288 are topic-specific proposals assembled from seven method structures (simulation, data analysis, software, close reading, creative comparison, argument cases, and signal experiments). These have not each received a separate literature review or feasibility audit. Search returns named choices, not fabricated citations. The 15 initial adaptations remain available.
