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

## Stage 37B-rev1 dataset claim reclassification status
Stage 37B-rev1 is complete. It corrects Stage 37B wording by classifying datasets/resources by allowed claim level. Missing metadata is not treated as rejection; known disqualification requires explicit evidence. Stage 37C clean external validation allowed now: `False`.

## Stage 37C-F multi-dataset external support status
Stage 37C-F multi-dataset external support suite is complete. It checked local readiness, candidate mapping, mechanism coverage, support tiers, and microglia/cell-type specificity fields for frozen Stage 36E candidates. It did not run SEA-AD model training, select candidates, tune thresholds, download data, or claim clean external validation.

## Stage 38B prepared external support analysis status
Stage 38B prepared external support analysis is blocked. Ready datasets: `0`; analyzed datasets: `0`. It uses frozen Stage 36E candidates only and does not train SEA-AD models, tune thresholds, select candidates, or claim causal/therapeutic validation.

## Stage 38C external support prioritization status
Stage 38C external support prioritization is complete. It converts Stage 38B outputs into bounded PI-facing priorities using frozen Stage 36E mechanisms/candidates. No new candidates, causal claims, or therapeutic claims were created.

## Stage 38A external data acquisition/preprocessing status
Stage 38A is complete. It prepared local external inputs where available and wrote manifests/readiness summaries. No validation/modeling/candidate selection was run.
## Stage 39A external metadata rescue status
Stage 39A is complete. It inspected local external files, rescued explicit metadata mappings where possible, and wrote Stage 39B-ready input mappings plus manual acquisition/preprocessing gaps. Ready-for-Stage39B datasets: `gse138852`. No model training, threshold tuning, candidate selection, clean external validation, causal claim, therapeutic claim, or gene-ablation claim was made.

## Stage 39B-LPH internal model rescue status
Stage 39B-LPH is complete. LPH training allowed: `True`; training ran: `True`; best condition: `lph_aux_head_shuffled_latent_target`; best mean pooled OOF Spearman: `0.32559684114609705`; delta versus Stage 27C: `-0.0011055988660524374`; internal performance pass: `False`. This is an internal model-improvement experiment only, not external validation or causal/therapeutic evidence.

## Stage 39C target engineering residual-stack status
Stage 39C is complete. Best condition: `rank_int_module_pca_ridge`; mean pooled OOF Spearman: `0.3458094563126456`; delta versus Stage 27C: `0.019107016300496105`; internal rescue pass: `False`. This is an internal target-engineering benchmark only, not external validation or causal/therapeutic evidence.
## Stage 39D metadata/composition stack status
Stage 39D is complete with proxy-risk sensitivity added. Best condition: `rank_int_latent_composition_ridge`; mean pooled OOF Spearman: `0.5048658499544396`; delta versus Stage 39C: `0.15905639364179402`; restricted no-pseudo/no-SEAAD mean: `0.31541966184063985`; context enrichment pass: `False`. This is an internal metadata/composition benchmark only.

## Stage 39E strong simple-model leaderboard status
Stage 39E is complete. Best condition: `rank_inverse_normal_module_direct_elasticnet`; mean pooled OOF Spearman: `0.37851256756728835`; delta versus Stage 39C: `0.03270311125464276`; material leaderboard pass: `False`. Composition/proxy features from Stage 39D were excluded from the primary benchmark.

## Stage 39F robustness confirmation status
Stage 39F is complete. New benchmark locked: `False`. Recommended next stage: `Stage39G_restricted_rescue_or_Stage40A_conditional`. This reused existing internal OOF predictions only.

## Stage 39H proxy-safe context decomposition status
Stage 39H is complete. Best proxy-safe/caution candidate: `latent_plus_tier1_plus_tier2`. Lock-eligible candidates: `0`. Recommended next stage: `manual multimodal feature acquisition or Stage40A_conditional_dualhead_ema_vicreg`.

## Stage 40A conditional dual-head EMA+VICReg status
Stage 40A is complete. Lock-eligible candidates: `0`. Recommended next stage: `manual multimodal feature acquisition_or_stop_internal_rescue`.

## Stage 40B terminal rescue synthesis status
Stage 40B is complete. Stage 27C remains the locked benchmark; Stage 39E pca8 remains the best credible unlocked candidate; internal architecture tuning on the current feature matrix should pause; recommended next stage is Stage41A manual/internal multimodal feature acquisition.
## Stage 41 internal multimodal feature acquisition status
Stage 41 is complete. Safe new donor-linked multimodal/spatial/image sources available for benchmark training: `0`. Benchmark training ran: `False`. Recommended next stage: `Stage41A_manual_internal_feature_acquisition`.
## Stage 41A manual internal feature acquisition status
Stage 41A is complete. Highest priority resources are SEA-AD donor metadata and postmortem MRI volumetrics; safest first benchmark matrix is donor-linked safe metadata + MRI. Next executable stage is Stage41B safe feature matrix build after manual acquisition.
## Stage 41ABC SEA-AD safe feature acquisition/download benchmark gate
Stage 41ABC fetched SEA-AD resource pages, attempted bounded safe downloads, analyzed downloaded files/manifests, wrote safety/linkage audits, and preserved the Stage 27C locked benchmark unless a schema-reviewed donor-linked safe matrix exists.

Run pass: `True`. Benchmark decision: `manual_feature_acquisition_required`. Benchmark training ran: `False`.

Allowed claim: safe SEA-AD resource acquisition and benchmark-readiness support only. Disallowed claim: external validation; clean validation; causal mechanism; therapeutic target; gene-ablation validation; disease-modifying effect.
## Stage 41B safe metadata/MRI benchmark
Stage 41B built donor-linked Tier-1 metadata/MRI matrices from Stage 41ABC downloads and ran locked donor-held-out ridge benchmarks. Best condition: `latent_plus_safe_metadata` with mean pooled OOF Spearman `0.339423`. Lock decision: `do_not_lock_stage41b`.
## Stage 41 Full safe feature stability pipeline
Stage 41 Full completed the safe metadata/latent stability rescue. Best Stage 41C candidate: `blend_stage41b_with_stage39e_pca8` with mean pooled OOF Spearman `0.368087` and bootstrap lower 95% CI `0.260360`. Final decision: `credible_unlocked_stage41_signal`. Locked benchmark after Stage 41: `Stage27C`.

## Stage 42 safe external-support and manuscript synthesis
Stage 42 completed report/readiness-only synthesis. Stage 27C remains the official locked internal benchmark. Stage 41C is the best credible unlocked signal and is not rebranded as locked. Final decision: `proceed_to_manuscript_draft`. No external validation, clean validation, causal, therapeutic, gene-ablation, or disease-modifying claim is made.
## Stage 45 new safe feature acquisition benchmark
Stage45 built CELLxGENE donor composition and engineered MRI feature candidates. Best candidate `latent_plus_safe_metadata_plus_cellxgene_plus_mri_engineered` score `0.312143`; decision `do_not_lock_stage45`. Stage27C remains locked unless Stage45 decision says lock_new_stage45_benchmark.

## Stage 43 manuscript draft package
Stage43 generated the manuscript draft and PI review package. Stage27C remains official locked benchmark; Stage41C remains best credible unlocked signal; Stage45 remains a negative safe feature-acquisition benchmark. Next action: PI review / manuscript editing.

## Stage 44 manuscript polish and PI review package
Stage44 generated polished manuscript v2, publication table package, figure specs, and PI review packet. Stage27C remains official locked benchmark; Stage41C remains best credible unlocked signal; Stage45 remains negative safe feature-acquisition result. Next action: PI review and manual manuscript editing.

## Stage 47 cross-version candidate/network/druggability synthesis

Stage47 consolidated v1/v2/v3 candidate genes, modules, networks, in-silico perturbation evidence, and druggability gaps into a claim-bounded Graph-JEPA disease-state model story. Stage47 did not change the locked benchmark. Stage27C remains official locked benchmark. Stage41C remains best credible unlocked signal unless superseded by later validated stages. Candidate genes/networks/drugs remain hypothesis-generating.

## Stage 48 candidate evidence consistency dossier

Stage48 completed a bounded candidate evidence consistency/dossier audit. It did not rerun gene discovery or alter benchmarks. The decision is not to rerun the broad gene discovery/modeling stack now; final candidates are sufficiently traceable for PI review, with remaining work focused on targeted validation planning and manual review.

## Stage 49 known experimental evidence concordance

Stage49 performed a post hoc known-evidence concordance audit for Stage47/48 Graph-JEPA candidate genes, modules, networks, and druggability hypotheses. It did not run new modeling or change benchmark status. Stage27C remains official locked benchmark, Stage41C remains credible-unlocked, and Stage45 remains negative. Known evidence is treated as orthogonal support for hypothesis prioritization, not as model validation of causality or therapy.

## Stage 50 graph-specific Graph-JEPA topology audit

Stage50 attempted the graph-specific Graph-JEPA topology audit. It did not alter benchmark status. Stage27C remains official locked benchmark, Stage41C remains credible-unlocked, and Stage45 remains negative. Graph-specific decision: graph_specific_test_inconclusive_missing_controls. Graph-specific claims remain limited unless real graph models beat no-graph, random, and shuffled controls under leakage-safe frozen evaluation.

## Stage 51 STRING graph topology JEPA run

Stage51 ran a small leakage-safe STRING graph topology JEPA audit. Decision: graph_topology_benefit_not_established. Stage27C remains official locked benchmark and Stage41C remains credible-unlocked.

## Stage 53 heterogeneity/composition auxiliary JEPA

Stage53 built and evaluated heterogeneity/composition-aware auxiliary branches for the donor-level JEPA disease-state framework. It used local SEA-AD microglia/PVM Supertype labels and Stage45 CELLxGENE composition metadata to test whether within-donor microglial state heterogeneity and cell-type/cell-state composition improve frozen disease-state recovery beyond pseudobulk programming alone. Stage27C remains official locked benchmark, Stage41C remains credible-unlocked, Stage45 remains negative, and Stage51 remains graph-topology-null. No causal, therapeutic, validated-ablation, STRING-topology, or new-microglia-type discovery claim is made.
