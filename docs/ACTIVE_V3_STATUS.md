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

## Stage 27A/27B run status

Stage 27 non-graph v3 has been run for SEA-AD-only conditions. The external-pretrained interface is implemented but remains skipped unless approved local external matrices are available. No graph branch or graph-specific control has been run in Stage 27.

## Stage 27C diagnosis and rescue status

Stage 27A failed and Stage 27B remains skipped because no approved external matrix is ready. Stage 27C completed with best condition `module_pca_ridge` at pooled mean OOF Spearman `0.3267`; pass=`True`; module reproduction pass=`True`. Graph-control status: non-graph gate passed; graph controls may proceed under locked protocol. No graph control was run in Stage 27C.

## Stage 30 graph-control status

Stage 30 graph controls are complete. Real graph mean pooled OOF Spearman: `0.3205`; graph-specific pass: `False`; controlled interpretation: `real_topology_beats_strict_shuffle_but_identity_no_graph_remains_best`. External validation remains not run, and in silico ablation remains unvalidated.

## Stage 31 residual graph-control status

Stage 31 residual graph controls are complete as an anti-oversmoothing experiment. Best Stage 31 condition: `weak_diffusion_real_graph_residual_pca_ridge_alpha_0_05` (`0.3264`). Full Stage 31 pass: `False`. Controlled interpretation: `graph_like_residual_features_contain_structure_but_topology_specific_utility_not_established`. Stage 27C remains the reference unless a residual graph condition passes all gates. External validation remains not run, and in silico ablation remains unvalidated.

## Stage 32 external pretraining matrix status

Stage 32 external pretraining matrix audit/build is complete. Matrix built: `False`; Stage 33 ready: `False`. Stage 27C remains the current best internal no-graph benchmark. Stage 30 mandatory graph controls failed graph-specific pass. Stage 31 weak residual graph nearly matched Stage 27C but did not beat it. External validation remains not run, and in silico ablation remains unvalidated.

## Stage 32B external pretraining acquisition status

Stage 32B acquisition/build audit is complete. Matrix built: `False`; Stage 33A ready: `False`. If no matrix was built, next action is manual approval/download/build of a specific approved pretraining candidate. External validation remains not run and in silico ablation remains unvalidated.

## Stage 33A external-pretrained benchmark status

Stage 33A status: `skipped`. Stage 33A full pass: `False`. Interpretation: `Stage 33A skipped because no approved external pretraining matrix was available`. External validation remains not run, manuscript claims are unchanged, and in silico ablation remains unvalidated.

## Stage 32C bulk external acquisition status
Stage 32C bulk approved external acquisition/schema audit is complete. Human matrix built: `False`; Stage 33 ready: `False`. No model was trained and external validation remains not run.
