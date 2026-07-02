# Stage 39E strong simple-model leaderboard report

Stage 39E is an internal strong simple-model leaderboard under locked donor-held-out folds. It uses only Stage 27C module features and train-fold-only target/feature preprocessing. Composition/proxy features flagged in Stage 39D are excluded from the primary benchmark. It does not use external data, select candidates, or support claims of clean external validation, causality, therapeutic relevance, disease modification, or gene ablation.

## Inputs

| input_name | path | exists | size_bytes |
| --- | --- | --- | --- |
| stage27c_script | scripts/run_stage27c_non_graph_rescue_v1.py | True | 36188 |
| stage39c_mean_metrics | results/tables/stage39c_mean_metrics_v1.csv | True | 678 |
| stage39c_target_metrics | results/tables/stage39c_target_metrics_v1.csv | True | 4186 |
| stage39d_restricted_composition_sensitivity | results/tables/stage39d_restricted_composition_sensitivity_v1.csv | True | 1642 |
| locked_folds | results/tables/v3_locked_donor_folds_v1.csv | True | 12554 |

## Model registry

| condition | target_transform | feature_view | n_components | model | primary_leaderboard_allowed |
| --- | --- | --- | --- | --- | --- |
| rank_inverse_normal_module_pca4_ridge | rank_inverse_normal | pca | 4.0 | ridge | True |
| rank_inverse_normal_module_pca4_elasticnet | rank_inverse_normal | pca | 4.0 | elasticnet | True |
| rank_inverse_normal_module_pca4_huber | rank_inverse_normal | pca | 4.0 | huber | True |
| rank_inverse_normal_module_pca8_ridge | rank_inverse_normal | pca | 8.0 | ridge | True |
| rank_inverse_normal_module_pca8_elasticnet | rank_inverse_normal | pca | 8.0 | elasticnet | True |
| rank_inverse_normal_module_pca8_huber | rank_inverse_normal | pca | 8.0 | huber | True |
| rank_inverse_normal_module_pca12_ridge | rank_inverse_normal | pca | 12.0 | ridge | True |
| rank_inverse_normal_module_pca12_elasticnet | rank_inverse_normal | pca | 12.0 | elasticnet | True |
| rank_inverse_normal_module_pca12_huber | rank_inverse_normal | pca | 12.0 | huber | True |
| rank_inverse_normal_module_pca16_ridge | rank_inverse_normal | pca | 16.0 | ridge | True |
| rank_inverse_normal_module_pca16_elasticnet | rank_inverse_normal | pca | 16.0 | elasticnet | True |
| rank_inverse_normal_module_pca16_huber | rank_inverse_normal | pca | 16.0 | huber | True |
| rank_inverse_normal_module_direct_ridge | rank_inverse_normal | direct |  | ridge | True |
| rank_inverse_normal_module_direct_elasticnet | rank_inverse_normal | direct |  | elasticnet | True |
| rank_inverse_normal_module_direct_huber | rank_inverse_normal | direct |  | huber | True |
| rank_inverse_normal_module_pca2_pls | rank_inverse_normal | pca | 2.0 | pls | True |
| rank_inverse_normal_module_pca4_pls | rank_inverse_normal | pca | 4.0 | pls | True |
| rank_inverse_normal_module_pca6_pls | rank_inverse_normal | pca | 6.0 | pls | True |
| raw_log1p_module_pca4_ridge | raw_log1p | pca | 4.0 | ridge | True |
| raw_log1p_module_pca4_elasticnet | raw_log1p | pca | 4.0 | elasticnet | True |
| raw_log1p_module_pca4_huber | raw_log1p | pca | 4.0 | huber | True |
| raw_log1p_module_pca8_ridge | raw_log1p | pca | 8.0 | ridge | True |
| raw_log1p_module_pca8_elasticnet | raw_log1p | pca | 8.0 | elasticnet | True |
| raw_log1p_module_pca8_huber | raw_log1p | pca | 8.0 | huber | True |
| raw_log1p_module_pca12_ridge | raw_log1p | pca | 12.0 | ridge | True |
| raw_log1p_module_pca12_elasticnet | raw_log1p | pca | 12.0 | elasticnet | True |
| raw_log1p_module_pca12_huber | raw_log1p | pca | 12.0 | huber | True |
| raw_log1p_module_pca16_ridge | raw_log1p | pca | 16.0 | ridge | True |
| raw_log1p_module_pca16_elasticnet | raw_log1p | pca | 16.0 | elasticnet | True |
| raw_log1p_module_pca16_huber | raw_log1p | pca | 16.0 | huber | True |
| winsor_log1p_module_pca4_ridge | winsor_log1p | pca | 4.0 | ridge | True |
| winsor_log1p_module_pca4_elasticnet | winsor_log1p | pca | 4.0 | elasticnet | True |
| winsor_log1p_module_pca4_huber | winsor_log1p | pca | 4.0 | huber | True |
| winsor_log1p_module_pca8_ridge | winsor_log1p | pca | 8.0 | ridge | True |
| winsor_log1p_module_pca8_elasticnet | winsor_log1p | pca | 8.0 | elasticnet | True |
| winsor_log1p_module_pca8_huber | winsor_log1p | pca | 8.0 | huber | True |
| winsor_log1p_module_pca12_ridge | winsor_log1p | pca | 12.0 | ridge | True |
| winsor_log1p_module_pca12_elasticnet | winsor_log1p | pca | 12.0 | elasticnet | True |
| winsor_log1p_module_pca12_huber | winsor_log1p | pca | 12.0 | huber | True |
| winsor_log1p_module_pca16_ridge | winsor_log1p | pca | 16.0 | ridge | True |

## Leaderboard

| condition | mean_pooled_oof_spearman | min_target_spearman | n_targets | target_transform | feature_view | n_components | model | primary_leaderboard_allowed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rank_inverse_normal_module_direct_elasticnet | 0.37851256756728835 | 0.12208036796026417 | 5 | rank_inverse_normal | direct |  | elasticnet | True |
| rank_inverse_normal_module_pca8_ridge | 0.35808116279206914 | 0.056974172849842526 | 5 | rank_inverse_normal | pca | 8.0 | ridge | True |
| rank_inverse_normal_module_pca8_huber | 0.35501069559916243 | -0.015960059795832177 | 5 | rank_inverse_normal | pca | 8.0 | huber | True |
| rank_inverse_normal_module_pca12_ridge | 0.3441957425548366 | 0.0721139503845945 | 5 | rank_inverse_normal | pca | 12.0 | ridge | True |
| rank_inverse_normal_module_pca4_huber | 0.34286388270560486 | 0.16955538144772725 | 5 | rank_inverse_normal | pca | 4.0 | huber | True |
| rank_inverse_normal_module_direct_ridge | 0.34123240177127856 | 0.06999741961217766 | 5 | rank_inverse_normal | direct |  | ridge | True |
| rank_inverse_normal_module_pca16_ridge | 0.34123240177127856 | 0.06999741961217766 | 5 | rank_inverse_normal | pca | 16.0 | ridge | True |
| rank_inverse_normal_module_pca12_huber | 0.3336317223197651 | 0.05467535713051899 | 5 | rank_inverse_normal | pca | 12.0 | huber | True |
| rank_inverse_normal_module_direct_huber | 0.33240631677446497 | 0.0025114814907147083 | 5 | rank_inverse_normal | direct |  | huber | True |
| rank_inverse_normal_module_pca16_huber | 0.33240631677446497 | 0.0025114814907147083 | 5 | rank_inverse_normal | pca | 16.0 | huber | True |
| rank_inverse_normal_module_pca8_elasticnet | 0.33220078538945647 | 0.015541478923225355 | 5 | rank_inverse_normal | pca | 8.0 | elasticnet | True |
| raw_log1p_module_pca8_huber | 0.33112078566366304 | -0.02824744355573555 | 5 | raw_log1p | pca | 8.0 | huber | True |
| winsor_log1p_module_pca8_huber | 0.3272253603297952 | -0.03411265594707373 | 5 | winsor_log1p | pca | 8.0 | huber | True |
| rank_inverse_normal_module_pca4_pls | 0.32606185703396917 | 0.1401366164052828 | 5 | rank_inverse_normal | pca | 4.0 | pls | True |
| rank_inverse_normal_module_pca12_elasticnet | 0.325831486597565 | 0.015541478923225355 | 5 | rank_inverse_normal | pca | 12.0 | elasticnet | True |
| rank_inverse_normal_module_pca16_elasticnet | 0.32390725859779523 | 0.015541478923225355 | 5 | rank_inverse_normal | pca | 16.0 | elasticnet | True |
| rank_inverse_normal_module_pca6_pls | 0.323487796203756 | 0.0700683082026414 | 5 | rank_inverse_normal | pca | 6.0 | pls | True |
| raw_log1p_module_pca12_ridge | 0.3142695150349296 | 0.04357598461071176 | 5 | raw_log1p | pca | 12.0 | ridge | True |
| raw_log1p_module_pca4_huber | 0.3121676622456212 | 0.13767338260605447 | 5 | raw_log1p | pca | 4.0 | huber | True |
| raw_log1p_module_pca16_ridge | 0.3117950794775742 | 0.06186088893388681 | 5 | raw_log1p | pca | 16.0 | ridge | True |
| raw_log1p_module_pca8_ridge | 0.3108352738685836 | -0.06325807431406297 | 5 | raw_log1p | pca | 8.0 | ridge | True |
| winsor_log1p_module_pca4_huber | 0.31041129440707804 | 0.13755429832027208 | 5 | winsor_log1p | pca | 4.0 | huber | True |
| raw_log1p_module_pca8_elasticnet | 0.3093959982219144 | 0.002968651634022669 | 5 | raw_log1p | pca | 8.0 | elasticnet | True |
| winsor_log1p_module_pca12_huber | 0.3064367406587374 | -0.011310132589160391 | 5 | winsor_log1p | pca | 12.0 | huber | True |
| raw_log1p_module_pca12_huber | 0.30582565556343017 | -0.009172825756808748 | 5 | raw_log1p | pca | 12.0 | huber | True |
| rank_inverse_normal_module_pca4_ridge | 0.30432761587449925 | 0.11027226593706635 | 5 | rank_inverse_normal | pca | 4.0 | ridge | True |
| raw_log1p_module_pca16_huber | 0.30363065708211 | -0.055887415207046674 | 5 | raw_log1p | pca | 16.0 | huber | True |
| winsor_log1p_module_pca16_huber | 0.30114619669839765 | -0.06092485925602334 | 5 | winsor_log1p | pca | 16.0 | huber | True |
| winsor_log1p_module_pca8_elasticnet | 0.29704522164498637 | -0.05349143689217885 | 5 | winsor_log1p | pca | 8.0 | elasticnet | True |
| winsor_log1p_module_pca8_ridge | 0.2970406352456866 | -0.08464879896632128 | 5 | winsor_log1p | pca | 8.0 | ridge | True |

## Best-model target deltas versus Stage 39C

| target | stage39e | stage39c | delta_vs_stage39c |
| --- | --- | --- | --- |
| 6e10/A_beta | 0.33392422739803806 | 0.4001619925078465 | -0.06623776510980844 |
| AT8 | 0.6297023981186389 | 0.5254834463906044 | 0.10421895172803453 |
| GFAP | 0.3369586193142646 | 0.3122608079376329 | 0.024697811376631684 |
| Iba1 | 0.12208036796026417 | 0.025473321858864 | 0.09660704610140017 |
| NeuN | 0.46989722504523623 | 0.4656677128682798 | 0.00422951217695644 |

## Negative controls

| condition | mean_pooled_oof_spearman | min_target_spearman | n_targets | target_transform | feature_view | n_components | model | primary_leaderboard_allowed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| negative_control_rank_int_pca8_shuffled_features_ridge | -0.06368554330095158 | -0.1505774930864395 | 5 | rank_inverse_normal | pca | 8.0 | ridge | False |
| negative_control_rank_int_pca8_donor_shuffled_target_ridge | -0.12667518718833465 | -0.3585410116617617 | 5 | rank_inverse_normal | pca | 8.0 | ridge | False |

## Bootstrap CI and pass/fail

| condition | n_bootstrap | bootstrap_mean | ci_lower_95 | ci_upper_95 |
| --- | --- | --- | --- | --- |
| rank_inverse_normal_module_direct_elasticnet | 500 | 0.37223767455441303 | 0.28346790137616135 | 0.4556144030588269 |

| best_condition | stage27c_reference_mean | stage39c_best_mean | best_mean_pooled_oof_spearman | best_min_target_spearman | delta_vs_stage27c | delta_vs_stage39c | bootstrap_ci_lower_95 | bootstrap_ci_upper_95 | negative_control_max_mean_pooled_oof_spearman | negative_controls_pass | no_target_drop_guard_violation | stage39e_material_leaderboard_pass | recommended_next_step | allowed_claim_language | prohibited_claim_language |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rank_inverse_normal_module_direct_elasticnet | 0.3267024400121495 | 0.3458094563126456 | 0.37851256756728835 | 0.12208036796026417 | 0.05181012755513886 | 0.03270311125464276 | 0.28346790137616135 | 0.4556144030588269 | -0.06368554330095158 | True | False | False | retain Stage 39C as credible benchmark; use Stage 39E as negative/leaderboard evidence | internal simple-model leaderboard; donor-held-out model comparison; benchmark selection support only | clean external validation; causal regulator; therapeutic target; disease-modifying target; gene-ablation result |

## Claim boundary audit

| audit_item | pass | evidence |
| --- | --- | --- |
| train_fold_only_preprocessing | True | Stage 39E is an internal strong simple-model leaderboard under locked donor-held-out folds. It uses only Stage 27C module features and train-fold-only target/feature preprocessing. Composition/proxy features flagged in Stage 39D are excluded from the primary benchmark. It does not use external data, select candidates, or support claims of clean external validation, causality, therapeutic relevance, disease modification, or gene ablation. |
| donor_heldout_only | True | Stage 39E is an internal strong simple-model leaderboard under locked donor-held-out folds. It uses only Stage 27C module features and train-fold-only target/feature preprocessing. Composition/proxy features flagged in Stage 39D are excluded from the primary benchmark. It does not use external data, select candidates, or support claims of clean external validation, causality, therapeutic relevance, disease modification, or gene ablation. |
| no_external_data | True | Stage 39E is an internal strong simple-model leaderboard under locked donor-held-out folds. It uses only Stage 27C module features and train-fold-only target/feature preprocessing. Composition/proxy features flagged in Stage 39D are excluded from the primary benchmark. It does not use external data, select candidates, or support claims of clean external validation, causality, therapeutic relevance, disease modification, or gene ablation. |
| no_composition_proxy_features | True | Stage 39E is an internal strong simple-model leaderboard under locked donor-held-out folds. It uses only Stage 27C module features and train-fold-only target/feature preprocessing. Composition/proxy features flagged in Stage 39D are excluded from the primary benchmark. It does not use external data, select candidates, or support claims of clean external validation, causality, therapeutic relevance, disease modification, or gene ablation. |
| no_candidate_selection | True | Stage 39E is an internal strong simple-model leaderboard under locked donor-held-out folds. It uses only Stage 27C module features and train-fold-only target/feature preprocessing. Composition/proxy features flagged in Stage 39D are excluded from the primary benchmark. It does not use external data, select candidates, or support claims of clean external validation, causality, therapeutic relevance, disease modification, or gene ablation. |
| no_clean_external_validation_claim | True | Stage 39E is an internal strong simple-model leaderboard under locked donor-held-out folds. It uses only Stage 27C module features and train-fold-only target/feature preprocessing. Composition/proxy features flagged in Stage 39D are excluded from the primary benchmark. It does not use external data, select candidates, or support claims of clean external validation, causality, therapeutic relevance, disease modification, or gene ablation. |
| no_causal_claim | True | Stage 39E is an internal strong simple-model leaderboard under locked donor-held-out folds. It uses only Stage 27C module features and train-fold-only target/feature preprocessing. Composition/proxy features flagged in Stage 39D are excluded from the primary benchmark. It does not use external data, select candidates, or support claims of clean external validation, causality, therapeutic relevance, disease modification, or gene ablation. |
| no_therapeutic_claim | True | Stage 39E is an internal strong simple-model leaderboard under locked donor-held-out folds. It uses only Stage 27C module features and train-fold-only target/feature preprocessing. Composition/proxy features flagged in Stage 39D are excluded from the primary benchmark. It does not use external data, select candidates, or support claims of clean external validation, causality, therapeutic relevance, disease modification, or gene ablation. |
| no_gene_ablation_claim | True | Stage 39E is an internal strong simple-model leaderboard under locked donor-held-out folds. It uses only Stage 27C module features and train-fold-only target/feature preprocessing. Composition/proxy features flagged in Stage 39D are excluded from the primary benchmark. It does not use external data, select candidates, or support claims of clean external validation, causality, therapeutic relevance, disease modification, or gene ablation. |
| negative_controls_reported | True | Stage 39E is an internal strong simple-model leaderboard under locked donor-held-out folds. It uses only Stage 27C module features and train-fold-only target/feature preprocessing. Composition/proxy features flagged in Stage 39D are excluded from the primary benchmark. It does not use external data, select candidates, or support claims of clean external validation, causality, therapeutic relevance, disease modification, or gene ablation. |
| safety_audit_pass | True | all safety checks passed |

## Interpretation

Stage 39E asks whether a predeclared set of strong but low-capacity simple models can beat the Stage 39C target-engineering lead without using external data or Stage 39D composition/proxy features. A Stage 39E material pass requires a margin over Stage 39C, bootstrap CI support, negative-control separation, and no target-drop guard violation.
