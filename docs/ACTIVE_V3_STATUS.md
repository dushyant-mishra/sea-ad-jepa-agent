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
Stage 32C bulk approved external acquisition/schema audit is complete. Human matrix built: `True`; Stage 33 ready: `True`. No model was trained and external validation remains not run.

## Stage 33B external-pretrained benchmark status
Stage 33B external-pretrained internal benchmark is complete. Best external condition: `external_pretrained_no_graph_identity_jepa_ridge` (`0.2711`). Internal performance pass: `False`; graph-specific pass: `False`. No external validation or manuscript claim update.

## Stage 33C external-pretrained diagnostic/rescue status
Stage 33C external-pretrained diagnostic/rescue is complete. Best condition: `ext_svd32_raw_count_size_factor_log1p_direct_no_graph` (`0.3049`). Rescue performance pass: `False`; graph-specific pass: `False`. Stage 33C rescued part of the external-pretraining deficit but did not improve over the Stage 27C internal no-graph reference. Real topology outperformed shuffled topology but did not improve over the no-graph identity reference. No external validation or manuscript claim update.

## Stage 34A HBCA microglia/myeloid-filtered external pretraining status
Stage 34A is complete. Filtered HBCA cells: `10325`. Best condition: `filtered_ext_svd16_raw_count_size_factor_log1p_direct_no_graph` (`0.2945`). Biological-filter rescue pass: `False`; full internal performance pass: `False`; graph-specific pass: `False`. Microglia/myeloid filtering did not rescue the external-pretraining deficit under this implementation. Real topology outperformed shuffled topology but did not improve over the no-graph identity reference. No external validation or manuscript claim update.

## Stage 34B HBCC external pretraining status
Stage 34B is complete. HBCC cells used: `100000`. Best condition: `hbcc_ext_svd32_raw_count_size_factor_log1p_concat_module_pca_no_graph` (`0.2782`). Dataset rescue pass: `False`; full internal performance pass: `False`; graph-specific pass: `False`. HBCC external pretraining did not rescue the external-pretraining deficit under this compact benchmark. Graph-specific utility remains unestablished. No external validation or manuscript claim update.

## Stage 35A target-aware weak graph rescue status
Stage 35A is complete. Best condition: `target_aware_no_graph_identity_aux_ridge` (`0.3267`). Best real graph condition: `target_aware_real_graph_aux_weight_0_01_ridge` (`0.3264`). Internal performance pass: `False`; global graph-specific pass: `False`; target-specific rescue candidates: `0`. Target-aware weak graph injection did not improve over the Stage 27C internal no-graph reference under this implementation. Graph-specific utility remains unestablished. No external validation or manuscript claim update.

## Stage 36A module counterfactual agent status
Stage 36A is complete. Run pass: `True`; gene-level pass: `True`; knowledge-grounding pass: `False`; validation pass: `False`. Outputs are model-implied counterfactual hypotheses from the Stage 27C module_pca_ridge backbone and require independent validation. No external validation or therapeutic/causal claim update.

## Stage 35B graph Laplacian regularized ridge status
Stage 35B is complete. Best condition: `laplacian_real_graph_lambda_0_1_ridge` (`0.3194`). Graph-specific pass: `True`. Graph Laplacian regularization did not improve over the Stage 27C internal no-graph reference under this implementation. No external validation or manuscript claim update.

## Stage 35C latent module graph diagnostic status
Stage 35C is complete. Best condition: `module_graph_real_overlap_aux_weight_0_1_ridge` (`0.3273`). Module graph-specific pass: `True`; target-specific rescue candidates: `1`. Stage 35C completed under guarded internal benchmark rules. No external validation or manuscript claim update.

## Stage 35D perturbation graph diagnostic status
Stage 35D is complete as a feasibility audit. Benchmark run: `False`. Stage 35D completed a perturbation-graph feasibility audit but did not run a benchmark because no approved local perturbation-derived graph was available. No external validation, causal validation, or manuscript claim update.

## Stage 35E graph diagnostics synthesis status
Stage 35E graph diagnostics synthesis is complete. Across Stage 30, Stage 31, Stage 35A, Stage 35B, Stage 35C, and Stage 35D, most graph strategies did not improve over the Stage 27C no-graph reference. Stage 35C is the first guarded internal positive module-scale graph result, with best mean pooled OOF Spearman 0.327265 versus Stage 27C 0.326702 and matched module graph controls passed. The result is small, internal only, and not external validation.

## Stage 36B local knowledge grounding status
Stage 36B local knowledge grounding is complete. Knowledge grounding pass: `True`; schema-stable local resources: `103`; annotated Stage 36A gene hypotheses: `770`. This is local prior-knowledge annotation only, not validation, causality, or therapeutic evidence.

## Stage 36C ranked hypothesis package status
Stage 36C ranked hypothesis package is complete. It combines Stage 36A model-implied counterfactual sensitivity with Stage 36B local knowledge grounding for follow-up prioritization only. No new modeling, external validation, causal validation, or treatment claim was made.

## Stage 36D validation handoff status
Stage 36D validation handoff is complete. It freezes the Stage 36C ranked, locally grounded follow-up hypotheses into a compact validation-facing shortlist and assay-planning package. No new modeling, data download, external validation, causal validation, gene-ablation claim, or therapeutic claim was made.

## Stage 36E frozen validation protocol status
Stage 36E frozen validation protocol is complete. It consolidates Stage 36C/36D follow-up hypotheses into frozen mechanism bins, a priority candidate registry, assay map, and validation decision rules before new validation data are examined. No new modeling, download, web scraping, external validation, causal validation, gene-ablation claim, or therapeutic claim was made.

## Stage 37A validation dataset eligibility audit status
Stage 37A validation dataset eligibility audit is complete. It classified already identified datasets/resources for clean validation, stress-test, projection/signature, robustness-only, manual-review, or exclusion roles. No validation, modeling, download, or web scraping was run. Recommended next stage: `Stage37B_manual_dataset_approval`.

## Stage 37B manual dataset approval status
Stage 37B manual dataset approval dossier is complete. It converts the Stage 37A eligibility audit into a PI-facing decision packet, metadata checklist, dataset-use policy, candidate validation routes, approval template, and clean-validation gate. Stage 37C clean external validation allowed now: `False`. No validation, modeling, downloads, or external-validation claim was made.
