# JEPA target-discovery Bayesian replication spike preregistration — 2026-10-09

Status: `EXPLORATORY_SPIKE_ONLY__RETROSPECTIVE_HISTORICAL_INPUTS__NON_AUTHORIZING`

## Purpose

Test whether a dependency-aware Bayesian hierarchical model can recover the qualitative relational-evidence structure already present in historical TD57B, TD57C and TD59 without being given the historical PASS/FAIL labels during fitting and without treating related source/panel/split cases as independent experiments.

This is a feasibility spike, not production Bayesian infrastructure and not target-selection authority.

## Inputs allowed

Only authenticated historical target-discovery result/statistic surfaces needed to reconstruct the native observed-vs-null/comparator margins for TD57B, TD57C and TD59 may be used.

The authenticated historical archive is:

`JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip`

SHA-256:

`c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417`

Corrected S174-substrate TD replay output is excluded from this spike. Macha's pending G4/G5 local execution and any later G6/G7 corrected-value replay must remain unseen by the model until after this spike has been evaluated and, if retained, a successor model contract has been prospectively frozen.

## Outcome withholding rule

Historical stage verdict labels are not model inputs.

During fitting, the spike must not consume:

- TD57B historical PASS/FAIL labels;
- TD57C historical PASS/FAIL labels;
- TD59 historical PASS/FAIL labels;
- downstream narrative interpretations of those verdicts.

Those labels may be inspected only after model fitting and posterior predictive diagnostics are complete, solely as an external sanity check.

## Unit of evidence

The spike models relational experiment cases, not individual target genes.

For each eligible case, the evidence ledger must preserve at minimum:

- stage identity;
- source identity;
- panel identity;
- donor split / half identity where represented;
- observed statistic;
- frozen null/comparator statistic;
- signed native margin = observed - frozen comparator;
- exact input artifact identity;
- producer/result identity when recoverable;
- dependence keys for shared substrate, source, panel and split.

Raw statistics from different stages must not be pooled directly when their scales differ. The primary modeled quantity is each stage's signed margin over its own frozen comparator/null.

## Dependency rule

Related cases must not be multiplied as if independent merely because there are many rows.

At minimum the model must account for clustering/dependence induced by shared:

- source;
- panel;
- donor split or half;
- historical Sample-A substrate / expression substrate;
- stage-level construction.

The spike must include a negative-control analysis in which duplicated/correlated evidence is repeated. Posterior confidence must not increase as though each duplicate were a new independent experiment.

## Model family

Primary spike model: skeptical hierarchical location model over signed margins.

Conceptual structure:

`margin_case ~ StudentT(nu, stage_mean + source_effect + panel_effect, residual_scale)`

with skeptical zero-centered priors on stage means and regularizing priors on heterogeneity terms.

The implementation may use an analytically convenient or sampling-based equivalent, but any simplification must preserve the dependency-aware objective and be documented.

## Required posterior quantities

For each modeled stage/hypothesis family, report at least:

- posterior probability that the latent mean margin is > 0;
- posterior mean/median latent margin;
- credible interval;
- posterior source heterogeneity;
- posterior predictive probability of positive margin in a new source/case;
- posterior predictive interval for a new case.

The spike must not emit a target-winner score or therapeutic rank.

## Prior sensitivity

Run at least three prospectively declared prior regimes:

1. skeptical/narrow;
2. weakly informative/default;
3. broader sensitivity prior.

If a substantive qualitative conclusion changes across these priors, classify it as `PRIOR_SENSITIVE` rather than promoting the most favorable result.

## Posterior predictive / falsification controls

Required controls:

- null synthetic world centered at zero;
- positive synthetic world with transportable positive margin;
- source-specific artifact with no transportable common effect;
- duplicated/correlated-evidence world;
- high-heterogeneity world.

The model should distinguish transportable common support from one-source or duplicated-evidence artifacts.

## Historical sanity-check target

Only after fitting is frozen and complete, compare the model's qualitative ordering against historical evidence:

- TD57B historically showed strong prospective recurrence;
- TD57C historically failed its frozen nearest-third sequential test;
- TD59 historically showed weaker but positive nearest-half mesoscale evidence.

Agreement is useful evidence that the model is capturing the historical structure; disagreement triggers diagnosis, not post-hoc retuning until agreement.

## Prohibited interpretations

This spike cannot:

- rescue or overwrite the historical TD57C fail;
- convert TD57B or TD59 into target authority;
- select a target or representation;
- authorize TD60;
- authorize G6/G7 value reads;
- authorize corrected TD replay;
- authorize JEPA training, EMA updates or Stage4;
- use protected TEST, DEV/SEALED, pathology, Morabito or other protected outcomes;
- reinterpret Nott, SCENIC+, NIH-CARD or genetics as target-selection authority.

## Success criterion for the spike

The spike is worth advancing to a formal B0/B1 Bayesian contract only if all of the following hold:

1. authenticated historical margins can be reconstructed without inventing pseudo-replicates;
2. the dependency-aware model is numerically stable under the three prior regimes;
3. null and duplicate-evidence controls do not generate false certainty;
4. source-artifact controls show appropriate heterogeneity/poor new-source prediction;
5. posterior predictive summaries are scientifically interpretable;
6. historical sanity checking does not require post-outcome retuning.

If these conditions are not met, record the failure and discard the spike.

## Authority

Hard project terminal remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
