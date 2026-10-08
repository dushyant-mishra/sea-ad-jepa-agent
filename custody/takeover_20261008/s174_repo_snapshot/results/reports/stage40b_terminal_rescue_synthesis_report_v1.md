# Stage 40B terminal model-rescue synthesis report

## Executive summary

Stage 27C remains the official locked internal benchmark. Stage 39C-E produced point-estimate improvements, but Stage 39F confirmed no benchmark-lock eligible candidate. Stage 39H showed useful context signal but no proxy-safe lockable recovery. Stage 40A conditional dual-head EMA+VICReg failed versus the Stage 39E pca8 reference. Therefore internal architecture tuning on the current feature matrix should pause.

## Rescue attempt inventory

| stage | attempt | best_or_relevant_mean_oof_spearman | status | terminal_interpretation |
| --- | --- | --- | --- | --- |
| Stage 27C | module_pca_ridge locked internal reference | 0.3267024400121495 | locked_benchmark | official locked internal benchmark remains active |
| Stage 30 | graph controls versus rescue baseline |  | failed_or_negative | graph controls did not establish a superior benchmark |
| Stage 31 | anti-oversmoothing residual graph controls |  | failed_or_negative | graph residual strategy did not replace non-graph baseline |
| Stage 33/34/35 | external pretraining / graph rescue diagnostics |  | failed_or_negative | external-pretraining/graph rescue branch did not beat locked internal benchmark safely |
| Stage 36 | ranked hypothesis package |  | planning_only | hypothesis package; not a benchmark rescue |
| Stage 37/38 | external dataset readiness/support branch |  | support_readiness_only | support/readiness, not clean external validation |
| Stage 39C | target engineering rank-int module PCA ridge | 0.3458094563126456 | point_estimate_improved_not_locked | CI lower too weak; not locked |
| Stage 39D | full metadata/composition context | 0.5048658499544396 | proxy_sensitive_not_lockable | large point estimate but proxy/leakage risk |
| Stage 39E | rank_inverse_normal_module_pca8_ridge | 0.35808116279206914 | best_unlocked_candidate | best credible simple-model candidate but CI weak |
| Stage 39F | robustness confirmation |  | no_new_benchmark_locked | confirmed no lock-eligible Stage39 candidate |
| Stage 39H | proxy-safe context decomposition | 0.38781411359724616 | useful_not_lockable | context signal useful but not lockable |
| Stage 40A | conditional dual-head EMA+VICReg | 0.20855839806587548 | architecture_rescue_failed | neural route failed versus Stage39E pca8 |

## Best candidate summary

| candidate | role | mean_pooled_oof_spearman | lock_status | reason |
| --- | --- | --- | --- | --- |
| Stage 27C module_pca_ridge | official_locked_benchmark | 0.3267024400121495 | locked | pre-existing official internal benchmark; no later candidate passed all lock gates |
| Stage 39E rank_inverse_normal_module_pca8_ridge | best_credible_unlocked_candidate | 0.35808116279206914 | unlocked | passes target guard and improves point estimate, but bootstrap lower CI did not clear lock gates |
| Stage 39H latent_plus_tier1_plus_tier2 | useful_context_candidate | 0.38781411359724616 | unlocked_not_lockable | useful context signal but target guard/proxy-caution/CI gates failed |
| Stage 40A dualhead_ema_vicreg_latent16 | conditional_architecture_rescue | 0.20855839806587548 | failed | failed versus Stage 39E pca8 reference |

## Lock status

| decision_item | value | status |
| --- | --- | --- |
| locked_benchmark | Stage 27C module_pca_ridge | preserved |
| new_benchmark_locked_after_39c_to_40a | False | no_candidate_passed_all_gates |
| best_unlocked_candidate | Stage 39E pca8 ridge | retain_as_candidate_only |
| architecture_tuning_on_current_matrix | pause | not_recommended |

## Failure modes

| failure_mode | stage_or_branch | evidence |
| --- | --- | --- |
| weak_bootstrap_support | Stage 39C/39E/39H | point estimates improved but donor-bootstrap lower CIs did not clear lock thresholds |
| target_guard_failure | Stage 39E direct elasticnet / Stage 39H context | high mean scores traded off Aβ, GFAP, or NeuN |
| proxy_sensitive_context | Stage 39D/39H full context | large context gains involved risky or forbidden proxy features |
| architecture_failure | Stage 40A | dual-head EMA+VICReg underperformed simple Stage 39E pca8 reference |
| missing_safe_information | terminal synthesis | current module matrix appears insufficient for robust rescue without added safe modalities |

## What worked versus failed

| outcome_class | item | interpretation |
| --- | --- | --- |
| worked_partially | rank inverse-normal target handling | Stage 39C/39E improved point estimates |
| worked_partially | simple ridge/PCA module baseline | Stage 39E pca8 remains best credible unlocked candidate |
| worked_partially | safe metadata/context decomposition | Stage 39H showed context can improve point estimates |
| failed_lock_gate | full composition/context | too proxy-sensitive to lock |
| failed_lock_gate | direct elastic net high-score model | Aβ guard failed |
| failed | low-capacity neural dual-head EMA+VICReg | Stage 40A did not rescue benchmark |
| recommended | new safe feature acquisition | likely missing information is outside current matrix |

## Stop/continue decision

| decision | value | rationale | next_action |
| --- | --- | --- | --- |
| keep_stage27c_locked | True | No Stage 39C-H or Stage 40A candidate was benchmark-lock eligible. | Use Stage 27C for official internal benchmark language. |
| continue_internal_architecture_tuning_on_current_features | False | Stage 40A failed badly versus Stage 39E pca8; further tuning risks overfitting 84 donors. | Pause architecture rescue on current feature matrix. |
| start_manual_multimodal_feature_acquisition | True | Useful signal likely requires safer additional internal modalities/features. | Run Stage41A manual/internal multimodal feature acquisition. |
| continue_external_metadata_repair | True | External branch remains useful for support/readiness but not clean validation. | Maintain as separate support-readiness branch. |

## Missing information inventory

| missing_feature_class | why_missing_matters | priority |
| --- | --- | --- |
| internal image-derived pathology morphology | quantitative plaque/tangle/glial morphology beyond scalar pathology targets | high |
| section-level pathology image descriptors | slide/section heterogeneity and staining context | high |
| spatial neighborhood summaries | cell-cell neighborhood context around pathology structures | high |
| region/anatomy covariates | anatomical context and region-specific burden | medium |
| donor-level cell-neighborhood composition | local rather than global composition effects | high |
| manually curated pathology metadata | safer expert-curated descriptors not derived from held-out targets | high |
| slide/section-level covariates | batch/section technical variation and morphology context | medium |
| clean external dataset metadata for support-only analysis | external support/readiness, not clean validation | medium |

## Multimodal/spatial/image acquisition plan

| feature_class | source | internal_or_external | expected_signal | leakage_risk | proxy_risk | acquisition_complexity | recommended_priority | allowed_use | prohibited_use | next_stage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| image_pathology_morphology | internal pathology images | internal | plaque/tangle/glial morphology may explain residual target variation | medium | medium | high | high | train-fold-safe internal feature engineering; benchmark candidate after audit | direct target leakage or post-hoc validation claims | Stage41A |
| spatial_neighborhood_summaries | spatial transcriptomics / cell coordinates if available | internal | local microenvironment may improve GFAP/Iba1/NeuN without proxy labels | medium | medium | high | high | feature acquisition and proxy audit | causal or therapeutic claims | Stage41A |
| section_slide_covariates | internal slide/section metadata | internal | technical and anatomical context may stabilize OOF predictions | low | low_to_medium | medium | high | covariate audit and train-fold preprocessing | using direct pathology scores as covariates | Stage41A |
| manual_pathology_metadata | manual/expert-curated pathology descriptors | internal | could add safe non-target morphology context | medium | medium | medium | high | candidate features after provenance review | held-out target-derived pseudo-labels | Stage41A |
| external_metadata_repair | external dataset annotations | external | support/readiness for cross-dataset context | low | medium | medium | medium | support-only analysis and eligibility audit | clean external validation unless gates permit | Stage41B_or_external_repair |
| donor_cell_neighborhood_composition | internal cell neighborhoods | internal | local cell composition may outperform global broad composition | medium | medium | high | medium | proxy-safe decomposition after acquisition | global disease-state labels as predictors | Stage41A |

## External metadata repair branch

| repair_task | description | purpose | claim_boundary |
| --- | --- | --- | --- |
| repair_sample_metadata | map sample/cell IDs, disease labels, pathology metadata | support_readiness | do not use for internal model selection |
| celltype_harmonization | microglia/astrocyte/neuron labels where available | support_readiness | no clean validation claim |
| pathology_label_harmonization | tau/pTau/Aβ/amyloid metadata if available | conditional_support | claim only external support if prior gates permit |
| claim_level_audit | dataset-by-dataset allowed claim language | safety | avoid clean external validation overclaim |

## Manuscript readiness and claim boundaries

| manuscript_item | status_summary | readiness |
| --- | --- | --- |
| locked_internal_benchmark | Stage 27C remains locked | ready |
| model_rescue_attempts | Stage 39C-H and 40A negative/partial results preserved | ready_as_methods_or_supplement |
| candidate_model_language | Stage 39E pca8 is unlocked candidate only | safe_with_limitations |
| external_validation_language | not clean external validation | not_ready |
| causal_therapeutic_language | not supported | forbidden |
| next_data_acquisition | Stage41A recommended | ready_to_plan |

| audit_item | pass | evidence |
| --- | --- | --- |
| no_new_model_training | True | Stage 40B is a report-only terminal synthesis. |
| no_external_data_used_for_model_selection | True | Stage 40B is a report-only terminal synthesis. |
| frozen_candidates_preserved | True | Stage 40B is a report-only terminal synthesis. |
| stage27c_locked_benchmark_preserved | True | Stage 40B is a report-only terminal synthesis. |
| no_clean_external_validation_claim | True | Stage 40B is a report-only terminal synthesis. |
| no_causal_claim | True | Stage 40B is a report-only terminal synthesis. |
| no_therapeutic_claim | True | Stage 40B is a report-only terminal synthesis. |
| no_gene_ablation_claim | True | Stage 40B is a report-only terminal synthesis. |
| no_disease_modifying_claim | True | Stage 40B is a report-only terminal synthesis. |
| negative_results_preserved | True | Stage 40B is a report-only terminal synthesis. |
| safety_audit_pass | True | all safety checks passed |
