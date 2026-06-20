# Active Graph-JEPA v3 Status

Last locked: 2026-06-20

## Current phase

The project is post-Stage 26C and pre-Stage 27. Stage 26C successfully reran CELLxGENE Census metadata discovery from WSL/Linux, scanned 1,845 CELLxGENE dataset metadata rows, and emitted 700 candidate dataset rows. No expression matrices or H5AD payloads were downloaded.

Graph-JEPA v3 is now the active publication framework. v1 is proof-of-concept history, v2 is graph-specificity and failure-analysis motivation, and v3 is the final framework being prepared for controlled training and evaluation.

## Official internal benchmark policy

- Official metric: pooled donor-level out-of-fold Spearman.
- Official internal baseline: `module_mean_baseline = 0.3128`.
- Minimum internal v3 success threshold: `0.3228`.
- Required targets: AT8, 6e10/A beta, GFAP, Iba1, and NeuN.
- No target may drop by more than `-0.02` versus the module-mean baseline.
- Graph-specific claims require real graph performance to beat both no-graph/identity and strict-shuffled graph controls.

The previous fold-mean baseline is not the official decision metric. Use pooled donor-level OOF Spearman for active v3 gates.

## Current next modeling step

Stage 27 should begin with non-graph v3 training regimes before making graph-topology claims:

1. Stage 27A: SEA-AD-only non-graph v3.
2. Stage 27B: external-pretrained non-graph v3.

Both Stage 27A and Stage 27B are training regimes inside one Graph-JEPA v3 framework. They are not separate projects and should not be framed as "Graph-JEPA v3" versus "external-enriched v3." External enrichment is a training regime within Graph-JEPA v3.

## What Stage 26C fixed

Stage 26C replaced ad hoc CELLxGENE browsing with an auditable Census metadata search. It also corrected the provenance boundary: SEA-AD, Rexach, Olah, and Leng/Grubman/GSE138852-like datasets are not clean external holdouts because they are primary, previously used, or plausibility-context datasets.

Clean holdout candidates are now clearly separated from:

- self-supervised pretraining candidates,
- auxiliary supervision candidates,
- mouse-only auxiliary datasets,
- peripheral immune plausibility datasets,
- already-used plausibility-only datasets, and
- do-not-use-until-reviewed datasets.

## Dataset role principles

- A dataset used for training, pretraining, auxiliary supervision, architecture choice, threshold setting, candidate filtering, or model selection cannot later be called clean validation.
- Clean holdout candidates remain untouched until architecture, training regime, and evaluation rules are frozen.
- Already-used datasets are plausibility/context only.
- Mouse datasets require mouse-to-human ortholog mapping and are not human external validation.
- Peripheral immune datasets are plausibility/auxiliary only and are not direct brain microglia validation.
- No external dataset is allowed for model selection unless explicitly reclassified in a future registry update.

## Publication framing

The final paper should be a Graph-JEPA v3 paper:

- v1: proof-of-concept for SEA-AD pathology-linked JEPA representations.
- v2: graph-specificity motivation, failure analysis, and controls.
- v3: final framework with explicit internal gates, graph controls, external role freezing, and candidate-evidence tiers.

External pretraining or enrichment should be described as a v3 training regime, not as a separate project.

## No-overclaim rules

Current results do not prove causality, druggability, spatial plaque proximity, therapeutic efficacy, or experimental target validity. Model-implied counterfactuals are hypotheses unless supported by independent causal or experimental evidence.

Clean external validation is not yet available. Stage 26B/26C are metadata/schema discovery stages only.

