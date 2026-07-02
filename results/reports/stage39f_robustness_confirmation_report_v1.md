# Stage 39F robustness confirmation report

Stage 39F reuses existing donor-held-out OOF predictions from Stage 27C and Stage 39C-E to audit whether any candidate should be locked as a new internal benchmark. It does not train new models, use external data, select candidates, or support validation, causal, therapeutic, disease-modifying, or gene-ablation claims.

## Candidate registry

| candidate_id | source_stage | model_name | model_role | expected_mean_oof_spearman | candidate_type | primary_candidate_for_lock | comparator_only | known_limitation | reason_included |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| stage27c_locked_reference | Stage 27C | module_pca_ridge | locked_reference | 0.3267024400121495 | reference | False | True | locked historical reference | baseline for benchmark-lock audit |
| stage39c_rank_int_module_pca_ridge | Stage 39C | rank_int_module_pca_ridge | target_engineering_candidate | 0.3458094563126456 | candidate | False | False | bootstrap lower CI previously weak | credible Stage 39C point-estimate improvement |
| stage39e_rank_inverse_normal_module_pca8_ridge | Stage 39E | rank_inverse_normal_module_pca8_ridge | balanced_simple_model_candidate | 0.35808116279206914 | primary_lock_candidate | True | False | requires bootstrap and fold/donor sensitivity confirmation | best balanced Stage 39E model passing target-drop guard preliminarily |
| stage39e_rank_inverse_normal_module_direct_elasticnet | Stage 39E | rank_inverse_normal_module_direct_elasticnet | high_score_guard_failing_comparator | 0.37851256756728835 | guard_failing_comparator | False | True | A_beta/6e10 target-drop guard failure | highest Stage 39E point estimate but not lockable without guard pass |
| stage39d_rank_int_latent_composition_ridge_proxy_risk | Stage 39D | rank_int_latent_composition_ridge | proxy_risk_comparator | 0.5048658499544396 | proxy_risk_comparator | False | True | composition proxy/leakage sensitivity | high score but proxy-risk caution |
| stage39d_no_pseudo_no_seaad_restricted | Stage 39D | sensitivity_no_pseudo_no_seaad_latent_composition_ridge | restricted_sensitivity_comparator | 0.31541966184063985 | sensitivity_control | False | True | restricted composition sensitivity does not beat Stage 27C | tests whether Stage 39D signal survives proxy removal |

## OOF score confirmation

| candidate_id | source_stage | model_name | mean_pooled_oof_spearman | delta_vs_stage27c | delta_vs_material_threshold_0_3317 | score_recomputed_from_oof_predictions | oof_predictions_available | confirmation_status | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| stage27c_locked_reference | Stage 27C | module_pca_ridge | 0.3267024400121495 | 0.0 | -0.0050000000000000044 | True | True | recomputed_from_oof | does_not_beat_stage27c |
| stage39c_rank_int_module_pca_ridge | Stage 39C | rank_int_module_pca_ridge | 0.34580945631264554 | 0.01910701630049605 | 0.014107016300496045 | True | True | recomputed_from_oof | point_estimate_above_stage27c |
| stage39d_no_pseudo_no_seaad_restricted | Stage 39D | sensitivity_no_pseudo_no_seaad_latent_composition_ridge | 0.31541966184063985 | -0.011282778171509633 | -0.016282778171509638 | False | False | summary_only | does_not_beat_stage27c |
| stage39d_rank_int_latent_composition_ridge_proxy_risk | Stage 39D | rank_int_latent_composition_ridge | 0.5048658499544396 | 0.17816340994229013 | 0.17316340994229013 | True | True | recomputed_from_oof | point_estimate_above_stage27c |
| stage39e_rank_inverse_normal_module_direct_elasticnet | Stage 39E | rank_inverse_normal_module_direct_elasticnet | 0.3785125675672884 | 0.05181012755513892 | 0.046810127555138914 | True | True | recomputed_from_oof | point_estimate_above_stage27c |
| stage39e_rank_inverse_normal_module_pca8_ridge | Stage 39E | rank_inverse_normal_module_pca8_ridge | 0.35808116279206914 | 0.031378722779919654 | 0.02637872277991965 | True | True | recomputed_from_oof | point_estimate_above_stage27c |

## Target-level confirmation

| candidate_id | target | target_oof_spearman | stage27c_target_reference | stage39c_target_reference_if_applicable | delta_vs_stage27c | delta_vs_stage39c | target_drop_guard_pass | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| stage27c_locked_reference | 6e10/A_beta | 0.3347372684013365 | 0.3347372684013365 | 0.4001619925078465 | 0.0 | -0.06542472410651001 | True | guard_pass |
| stage27c_locked_reference | AT8 | 0.5284398096588033 | 0.5284398096588033 | 0.5254834463906044 | 0.0 | 0.002956363268198925 | True | guard_pass |
| stage27c_locked_reference | GFAP | 0.30229826870507237 | 0.30229826870507237 | 0.3122608079376329 | 0.0 | -0.009962539232560519 | True | guard_pass |
| stage27c_locked_reference | Iba1 | 0.016077756403766325 | 0.016077756403766325 | 0.025473321858864025 | 0.0 | -0.0093955654550977 | True | guard_pass |
| stage27c_locked_reference | NeuN | 0.4519590968917688 | 0.4519590968917688 | 0.46566771286827985 | 0.0 | -0.013708615976511074 | True | guard_pass |
| stage39c_rank_int_module_pca_ridge | 6e10/A_beta | 0.4001619925078465 | 0.3347372684013365 | 0.4001619925078465 | 0.06542472410651001 | 0.0 | True | guard_pass |
| stage39c_rank_int_module_pca_ridge | AT8 | 0.5254834463906044 | 0.5284398096588033 | 0.5254834463906044 | -0.002956363268198925 | 0.0 | True | guard_pass |
| stage39c_rank_int_module_pca_ridge | GFAP | 0.3122608079376329 | 0.30229826870507237 | 0.3122608079376329 | 0.009962539232560519 | 0.0 | True | guard_pass |
| stage39c_rank_int_module_pca_ridge | Iba1 | 0.025473321858864025 | 0.016077756403766325 | 0.025473321858864025 | 0.0093955654550977 | 0.0 | True | guard_pass |
| stage39c_rank_int_module_pca_ridge | NeuN | 0.46566771286827985 | 0.4519590968917688 | 0.46566771286827985 | 0.013708615976511074 | 0.0 | True | guard_pass |
| stage39d_no_pseudo_no_seaad_restricted | 6e10/A_beta | 0.2755492558469171 | 0.3347372684013365 | 0.4001619925078465 | -0.05918801255441941 | -0.12461273666092942 | False | target_drop_guard_fail |
| stage39d_no_pseudo_no_seaad_restricted | AT8 | 0.4479700313860484 | 0.5284398096588033 | 0.5254834463906044 | -0.08046977827275492 | -0.077513415004556 | False | target_drop_guard_fail |
| stage39d_no_pseudo_no_seaad_restricted | GFAP | 0.2499544396071682 | 0.30229826870507237 | 0.3122608079376329 | -0.052343829097904165 | -0.062306368330464684 | False | target_drop_guard_fail |
| stage39d_no_pseudo_no_seaad_restricted | Iba1 | 0.1670142755897539 | 0.016077756403766325 | 0.025473321858864025 | 0.15093651918598758 | 0.14154095373088987 | True | guard_pass |
| stage39d_no_pseudo_no_seaad_restricted | NeuN | 0.4366103067733117 | 0.4519590968917688 | 0.46566771286827985 | -0.015348790118457079 | -0.029057406094968152 | True | guard_pass |
| stage39d_rank_int_latent_composition_ridge_proxy_risk | 6e10/A_beta | 0.7684114609699302 | 0.3347372684013365 | 0.4001619925078465 | 0.4336741925685937 | 0.3682494684620837 | True | guard_pass |
| stage39d_rank_int_latent_composition_ridge_proxy_risk | AT8 | 0.7183152779183962 | 0.5284398096588033 | 0.5254834463906044 | 0.1898754682595929 | 0.19283183152779182 | True | guard_pass |
| stage39d_rank_int_latent_composition_ridge_proxy_risk | GFAP | 0.35885390300698594 | 0.30229826870507237 | 0.3122608079376329 | 0.05655563430191357 | 0.04659309506935305 | True | guard_pass |
| stage39d_rank_int_latent_composition_ridge_proxy_risk | Iba1 | 0.13704566163814924 | 0.016077756403766325 | 0.025473321858864025 | 0.12096790523438292 | 0.11157233977928521 | True | guard_pass |
| stage39d_rank_int_latent_composition_ridge_proxy_risk | NeuN | 0.5417029462387365 | 0.4519590968917688 | 0.46566771286827985 | 0.08974384934696772 | 0.07603523337045665 | True | guard_pass |
| stage39e_rank_inverse_normal_module_direct_elasticnet | 6e10/A_beta | 0.33392422739803806 | 0.3347372684013365 | 0.4001619925078465 | -0.0008130410032984314 | -0.06623776510980844 | False | target_drop_guard_fail |
| stage39e_rank_inverse_normal_module_direct_elasticnet | AT8 | 0.6297023981186389 | 0.5284398096588033 | 0.5254834463906044 | 0.1012625884598356 | 0.10421895172803453 | True | guard_pass |
| stage39e_rank_inverse_normal_module_direct_elasticnet | GFAP | 0.3369586193142646 | 0.30229826870507237 | 0.3122608079376329 | 0.0346603506091922 | 0.024697811376631684 | True | guard_pass |
| stage39e_rank_inverse_normal_module_direct_elasticnet | Iba1 | 0.12208036796026417 | 0.016077756403766325 | 0.025473321858864025 | 0.10600261155649784 | 0.09660704610140014 | True | guard_pass |
| stage39e_rank_inverse_normal_module_direct_elasticnet | NeuN | 0.46989722504523623 | 0.4519590968917688 | 0.46566771286827985 | 0.01793812815346746 | 0.004229512176956385 | True | guard_pass |
| stage39e_rank_inverse_normal_module_pca8_ridge | 6e10/A_beta | 0.3746733755407961 | 0.3347372684013365 | 0.4001619925078465 | 0.03993610713945961 | -0.025488616967050404 | True | guard_pass |
| stage39e_rank_inverse_normal_module_pca8_ridge | AT8 | 0.5155185235317487 | 0.5284398096588033 | 0.5254834463906044 | -0.012921286127054676 | -0.009964922858855751 | True | guard_pass |
| stage39e_rank_inverse_normal_module_pca8_ridge | GFAP | 0.3823049963928304 | 0.30229826870507237 | 0.3122608079376329 | 0.08000672768775802 | 0.0700441884551975 | True | guard_pass |
| stage39e_rank_inverse_normal_module_pca8_ridge | Iba1 | 0.056974172849842526 | 0.016077756403766325 | 0.025473321858864025 | 0.0408964164460762 | 0.031500850990978504 | True | guard_pass |
| stage39e_rank_inverse_normal_module_pca8_ridge | NeuN | 0.4609347456451279 | 0.4519590968917688 | 0.46566771286827985 | 0.0089756487533591 | -0.004732967223151974 | True | guard_pass |

## Bootstrap confidence intervals

| candidate_id | n_bootstrap | bootstrap_unit | mean_oof_spearman | ci_lower_95 | ci_upper_95 | lower_ci_above_stage27c | lower_ci_above_0_3317 | bootstrap_confirmation_pass | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| stage27c_locked_reference | 500 | donor | 0.3267024400121495 | 0.2125019906760157 | 0.42635302821627746 | False | False | False | donor bootstrap over existing OOF predictions |
| stage39c_rank_int_module_pca_ridge | 500 | donor | 0.34580945631264554 | 0.24932456692965593 | 0.4378643786868736 | False | False | False | donor bootstrap over existing OOF predictions |
| stage39d_no_pseudo_no_seaad_restricted | 0 | not_available_summary_only |  |  |  | False | False | False | OOF predictions unavailable for donor bootstrap |
| stage39d_rank_int_latent_composition_ridge_proxy_risk | 500 | donor | 0.5048658499544396 | 0.41767440920016424 | 0.5707503519807144 | True | True | True | donor bootstrap over existing OOF predictions |
| stage39e_rank_inverse_normal_module_direct_elasticnet | 500 | donor | 0.3785125675672884 | 0.2813235156768179 | 0.4621462646162579 | False | False | False | donor bootstrap over existing OOF predictions |
| stage39e_rank_inverse_normal_module_pca8_ridge | 500 | donor | 0.35808116279206914 | 0.2440153669355859 | 0.4498411498099251 | False | False | False | donor bootstrap over existing OOF predictions |

## Target-drop, Iba1, and Aβ audits

| candidate_id | target | target_score | comparator_score | delta_vs_comparator | target_drop_guard_pass | guard_threshold | guard_pass | failure_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| stage27c_locked_reference | 6e10/A_beta | 0.3347372684013365 | 0.4001619925078465 | -0.06542472410651001 | True | -0.05 | True | none |
| stage27c_locked_reference | AT8 | 0.5284398096588033 | 0.5254834463906044 | 0.002956363268198925 | True | -0.05 | True | none |
| stage27c_locked_reference | GFAP | 0.30229826870507237 | 0.3122608079376329 | -0.009962539232560519 | True | -0.05 | True | none |
| stage27c_locked_reference | Iba1 | 0.016077756403766325 | 0.025473321858864025 | -0.0093955654550977 | True | -0.05 | True | none |
| stage27c_locked_reference | NeuN | 0.4519590968917688 | 0.46566771286827985 | -0.013708615976511074 | True | -0.05 | True | none |
| stage39c_rank_int_module_pca_ridge | 6e10/A_beta | 0.4001619925078465 | 0.4001619925078465 | 0.0 | True | -0.05 | True | none |
| stage39c_rank_int_module_pca_ridge | AT8 | 0.5254834463906044 | 0.5254834463906044 | 0.0 | True | -0.05 | True | none |
| stage39c_rank_int_module_pca_ridge | GFAP | 0.3122608079376329 | 0.3122608079376329 | 0.0 | True | -0.05 | True | none |
| stage39c_rank_int_module_pca_ridge | Iba1 | 0.025473321858864025 | 0.025473321858864025 | 0.0 | True | -0.05 | True | none |
| stage39c_rank_int_module_pca_ridge | NeuN | 0.46566771286827985 | 0.46566771286827985 | 0.0 | True | -0.05 | True | none |
| stage39d_no_pseudo_no_seaad_restricted | 6e10/A_beta | 0.2755492558469171 | 0.4001619925078465 | -0.12461273666092942 | False | -0.05 | False | target dropped more than allowed versus Stage39C |
| stage39d_no_pseudo_no_seaad_restricted | AT8 | 0.4479700313860484 | 0.5254834463906044 | -0.077513415004556 | False | -0.05 | False | target dropped more than allowed versus Stage39C |
| stage39d_no_pseudo_no_seaad_restricted | GFAP | 0.2499544396071682 | 0.3122608079376329 | -0.062306368330464684 | False | -0.05 | False | target dropped more than allowed versus Stage39C |
| stage39d_no_pseudo_no_seaad_restricted | Iba1 | 0.1670142755897539 | 0.025473321858864025 | 0.14154095373088987 | True | -0.05 | True | none |
| stage39d_no_pseudo_no_seaad_restricted | NeuN | 0.4366103067733117 | 0.46566771286827985 | -0.029057406094968152 | True | -0.05 | True | none |
| stage39d_rank_int_latent_composition_ridge_proxy_risk | 6e10/A_beta | 0.7684114609699302 | 0.4001619925078465 | 0.3682494684620837 | True | -0.05 | True | none |
| stage39d_rank_int_latent_composition_ridge_proxy_risk | AT8 | 0.7183152779183962 | 0.5254834463906044 | 0.19283183152779182 | True | -0.05 | True | none |
| stage39d_rank_int_latent_composition_ridge_proxy_risk | GFAP | 0.35885390300698594 | 0.3122608079376329 | 0.04659309506935305 | True | -0.05 | True | none |
| stage39d_rank_int_latent_composition_ridge_proxy_risk | Iba1 | 0.13704566163814924 | 0.025473321858864025 | 0.11157233977928521 | True | -0.05 | True | none |
| stage39d_rank_int_latent_composition_ridge_proxy_risk | NeuN | 0.5417029462387365 | 0.46566771286827985 | 0.07603523337045665 | True | -0.05 | True | none |
| stage39e_rank_inverse_normal_module_direct_elasticnet | 6e10/A_beta | 0.33392422739803806 | 0.4001619925078465 | -0.06623776510980844 | False | -0.05 | False | target dropped more than allowed versus Stage39C |
| stage39e_rank_inverse_normal_module_direct_elasticnet | AT8 | 0.6297023981186389 | 0.5254834463906044 | 0.10421895172803453 | True | -0.05 | True | none |
| stage39e_rank_inverse_normal_module_direct_elasticnet | GFAP | 0.3369586193142646 | 0.3122608079376329 | 0.024697811376631684 | True | -0.05 | True | none |
| stage39e_rank_inverse_normal_module_direct_elasticnet | Iba1 | 0.12208036796026417 | 0.025473321858864025 | 0.09660704610140014 | True | -0.05 | True | none |
| stage39e_rank_inverse_normal_module_direct_elasticnet | NeuN | 0.46989722504523623 | 0.46566771286827985 | 0.004229512176956385 | True | -0.05 | True | none |
| stage39e_rank_inverse_normal_module_pca8_ridge | 6e10/A_beta | 0.3746733755407961 | 0.4001619925078465 | -0.025488616967050404 | True | -0.05 | True | none |
| stage39e_rank_inverse_normal_module_pca8_ridge | AT8 | 0.5155185235317487 | 0.5254834463906044 | -0.009964922858855751 | True | -0.05 | True | none |
| stage39e_rank_inverse_normal_module_pca8_ridge | GFAP | 0.3823049963928304 | 0.3122608079376329 | 0.0700441884551975 | True | -0.05 | True | none |
| stage39e_rank_inverse_normal_module_pca8_ridge | Iba1 | 0.056974172849842526 | 0.025473321858864025 | 0.031500850990978504 | True | -0.05 | True | none |
| stage39e_rank_inverse_normal_module_pca8_ridge | NeuN | 0.4609347456451279 | 0.46566771286827985 | -0.004732967223151974 | True | -0.05 | True | none |

| candidate_id | iba1_score | stage27c_iba1_score | delta_vs_stage27c | iba1_nonnegative | iba1_materially_improved | interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| stage27c_locked_reference | 0.016077756403766325 | 0.016077756403766325 | 0.0 | True | False | Iba1 not materially improved |
| stage39c_rank_int_module_pca_ridge | 0.025473321858864025 | 0.016077756403766325 | 0.0093955654550977 | True | False | Iba1 not materially improved |
| stage39d_no_pseudo_no_seaad_restricted | 0.1670142755897539 | 0.016077756403766325 | 0.15093651918598758 | True | True | Iba1 materially improved |
| stage39d_rank_int_latent_composition_ridge_proxy_risk | 0.13704566163814924 | 0.016077756403766325 | 0.12096790523438292 | True | True | Iba1 materially improved |
| stage39e_rank_inverse_normal_module_direct_elasticnet | 0.12208036796026417 | 0.016077756403766325 | 0.10600261155649784 | True | True | Iba1 materially improved |
| stage39e_rank_inverse_normal_module_pca8_ridge | 0.056974172849842526 | 0.016077756403766325 | 0.0408964164460762 | True | False | Iba1 not materially improved |

| candidate_id | abeta_score | stage27c_abeta_score | stage39c_abeta_score_if_applicable | delta_vs_stage27c | delta_vs_stage39c | abeta_guard_pass | failure_reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| stage27c_locked_reference | 0.3347372684013365 | 0.3347372684013365 | 0.4001619925078465 | 0.0 | -0.06542472410651001 | True | none |
| stage39c_rank_int_module_pca_ridge | 0.4001619925078465 | 0.3347372684013365 | 0.4001619925078465 | 0.06542472410651001 | 0.0 | True | none |
| stage39d_no_pseudo_no_seaad_restricted | 0.2755492558469171 | 0.3347372684013365 | 0.4001619925078465 | -0.05918801255441941 | -0.12461273666092942 | False | A_beta/6e10 dropped more than target guard versus Stage39C |
| stage39d_rank_int_latent_composition_ridge_proxy_risk | 0.7684114609699302 | 0.3347372684013365 | 0.4001619925078465 | 0.4336741925685937 | 0.3682494684620837 | True | none |
| stage39e_rank_inverse_normal_module_direct_elasticnet | 0.33392422739803806 | 0.3347372684013365 | 0.4001619925078465 | -0.0008130410032984314 | -0.06623776510980844 | False | A_beta/6e10 dropped more than target guard versus Stage39C |
| stage39e_rank_inverse_normal_module_pca8_ridge | 0.3746733755407961 | 0.3347372684013365 | 0.4001619925078465 | 0.03993610713945961 | -0.025488616967050404 | True | none |

## Negative controls and proxy/leakage risk

| candidate_id | control_type | real_score | control_score | delta_vs_control | control_pass | interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| stage39c_rank_int_module_pca_ridge | raw_log1p_module_pca_ridge_donor_shuffled_control | 0.34580945631264554 | -0.16876379467449637 | 0.5145732509871419 | True | control separated |
| stage39c_rank_int_module_pca_ridge | raw_log1p_metadata_only_ridge | 0.34580945631264554 | 0.14140326009922044 | 0.2044061962134251 | True | control separated |
| stage39e_rank_inverse_normal_module_pca8_ridge | negative_control_rank_int_pca8_shuffled_features_ridge | 0.35808116279206914 | -0.0636855433009515 | 0.42176670609302064 | True | control separated |
| stage39e_rank_inverse_normal_module_pca8_ridge | negative_control_rank_int_pca8_donor_shuffled_target_ridge | 0.35808116279206914 | -0.1266751871883346 | 0.48475634998040373 | True | control separated |
| stage39e_rank_inverse_normal_module_direct_elasticnet | negative_control_rank_int_pca8_shuffled_features_ridge | 0.3785125675672884 | -0.0636855433009515 | 0.4421981108682399 | True | control separated |
| stage39e_rank_inverse_normal_module_direct_elasticnet | negative_control_rank_int_pca8_donor_shuffled_target_ridge | 0.3785125675672884 | -0.1266751871883346 | 0.5051877547556229 | True | control separated |
| stage27c_locked_reference | not_applicable_or_comparator | 0.3267024400121495 |  |  | True | reference_or_sensitivity_comparator |
| stage39d_rank_int_latent_composition_ridge_proxy_risk | not_applicable_or_comparator | 0.5048658499544396 |  |  | False | proxy comparator cannot pass lock controls |
| stage39d_no_pseudo_no_seaad_restricted | not_applicable_or_comparator | 0.31541966184063985 |  |  | True | reference_or_sensitivity_comparator |

| candidate_id | proxy_or_leakage_risk_level | suspected_proxy_features | restricted_sensitivity_score | unrestricted_score | sensitivity_delta | lock_allowed | reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| stage27c_locked_reference | low | none in primary benchmark inputs |  | 0.3267024400121495 |  | True | uses module OOF predictions, not Stage39D composition proxy features |
| stage39c_rank_int_module_pca_ridge | low | none in primary benchmark inputs |  | 0.34580945631264554 |  | True | uses module OOF predictions, not Stage39D composition proxy features |
| stage39d_no_pseudo_no_seaad_restricted | low_after_restriction | removed | 0.31541966184063985 | 0.31541966184063985 | 0.0 | False | restricted score does not beat Stage27C |
| stage39d_rank_int_latent_composition_ridge_proxy_risk | high | pseudoprogression;SEAAD-labeled/fine composition features | 0.31541966184063985 | 0.5048658499544396 | 0.18944618811379976 | False | large full score collapses after restricted proxy removal |
| stage39e_rank_inverse_normal_module_direct_elasticnet | low | none in primary benchmark inputs |  | 0.3785125675672884 |  | True | uses module OOF predictions, not Stage39D composition proxy features |
| stage39e_rank_inverse_normal_module_pca8_ridge | low | none in primary benchmark inputs |  | 0.35808116279206914 |  | True | uses module OOF predictions, not Stage39D composition proxy features |

## Benchmark lock decision

| candidate_id | mean_pooled_oof_spearman | delta_vs_stage27c | lower_ci_above_stage27c | lower_ci_above_material_threshold | target_drop_guard_pass | negative_controls_pass | proxy_leakage_risk_pass | iba1_rescue_status | high_influence_donor_or_fold_flag | benchmark_lock_eligible | recommended_decision | allowed_claim_language | prohibited_claim_language |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| stage27c_locked_reference | 0.3267024400121495 | 0.0 | False | False | True | True | True | Iba1 not materially improved | False | False | not_lockable | internal robustness confirmation; candidate benchmark audit; point-estimate improvement only unless all lock gates pass | external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim |
| stage39c_rank_int_module_pca_ridge | 0.34580945631264554 | 0.01910701630049605 | False | False | True | True | True | Iba1 not materially improved | False | False | not_lockable | internal robustness confirmation; candidate benchmark audit; point-estimate improvement only unless all lock gates pass | external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim |
| stage39e_rank_inverse_normal_module_pca8_ridge | 0.35808116279206914 | 0.031378722779919654 | False | False | True | True | True | Iba1 not materially improved | False | False | robustness_candidate_not_locked | internal robustness confirmation; candidate benchmark audit; point-estimate improvement only unless all lock gates pass | external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim |
| stage39e_rank_inverse_normal_module_direct_elasticnet | 0.3785125675672884 | 0.05181012755513892 | False | False | False | True | True | Iba1 materially improved | False | False | high_score_guard_fail | internal robustness confirmation; candidate benchmark audit; point-estimate improvement only unless all lock gates pass | external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim |
| stage39d_rank_int_latent_composition_ridge_proxy_risk | 0.5048658499544396 | 0.17816340994229013 | True | True | True | False | False | Iba1 materially improved | False | False | proxy_sensitive_not_lockable | internal robustness confirmation; candidate benchmark audit; point-estimate improvement only unless all lock gates pass | external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim |
| stage39d_no_pseudo_no_seaad_restricted | 0.31541966184063985 | -0.011282778171509633 | False | False | False | True | False | Iba1 materially improved | False | False | sensitivity_control_not_improved | internal robustness confirmation; candidate benchmark audit; point-estimate improvement only unless all lock gates pass | external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim |

## Claim boundaries

| audit_item | pass | evidence |
| --- | --- | --- |
| no_external_data_used | True | Stage 39F reuses existing donor-held-out OOF predictions from Stage 27C and Stage 39C-E to audit whether any candidate should be locked as a new internal benchmark. It does not train new models, use external data, select candidates, or support validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| no_external_model_selection | True | Stage 39F reuses existing donor-held-out OOF predictions from Stage 27C and Stage 39C-E to audit whether any candidate should be locked as a new internal benchmark. It does not train new models, use external data, select candidates, or support validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| no_candidate_selection | True | Stage 39F reuses existing donor-held-out OOF predictions from Stage 27C and Stage 39C-E to audit whether any candidate should be locked as a new internal benchmark. It does not train new models, use external data, select candidates, or support validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| frozen_candidates_preserved | True | Stage 39F reuses existing donor-held-out OOF predictions from Stage 27C and Stage 39C-E to audit whether any candidate should be locked as a new internal benchmark. It does not train new models, use external data, select candidates, or support validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| donor_held_out_evaluation_preserved | True | Stage 39F reuses existing donor-held-out OOF predictions from Stage 27C and Stage 39C-E to audit whether any candidate should be locked as a new internal benchmark. It does not train new models, use external data, select candidates, or support validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| oof_predictions_reused_or_recomputed_safely | True | Stage 39F reuses existing donor-held-out OOF predictions from Stage 27C and Stage 39C-E to audit whether any candidate should be locked as a new internal benchmark. It does not train new models, use external data, select candidates, or support validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| negative_controls_reported | True | Stage 39F reuses existing donor-held-out OOF predictions from Stage 27C and Stage 39C-E to audit whether any candidate should be locked as a new internal benchmark. It does not train new models, use external data, select candidates, or support validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| proxy_leakage_risk_audited | True | Stage 39F reuses existing donor-held-out OOF predictions from Stage 27C and Stage 39C-E to audit whether any candidate should be locked as a new internal benchmark. It does not train new models, use external data, select candidates, or support validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| no_clean_external_validation_claim | True | Stage 39F reuses existing donor-held-out OOF predictions from Stage 27C and Stage 39C-E to audit whether any candidate should be locked as a new internal benchmark. It does not train new models, use external data, select candidates, or support validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| no_causal_claim | True | Stage 39F reuses existing donor-held-out OOF predictions from Stage 27C and Stage 39C-E to audit whether any candidate should be locked as a new internal benchmark. It does not train new models, use external data, select candidates, or support validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| no_therapeutic_claim | True | Stage 39F reuses existing donor-held-out OOF predictions from Stage 27C and Stage 39C-E to audit whether any candidate should be locked as a new internal benchmark. It does not train new models, use external data, select candidates, or support validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| no_gene_ablation_claim | True | Stage 39F reuses existing donor-held-out OOF predictions from Stage 27C and Stage 39C-E to audit whether any candidate should be locked as a new internal benchmark. It does not train new models, use external data, select candidates, or support validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| no_disease_modifying_claim | True | Stage 39F reuses existing donor-held-out OOF predictions from Stage 27C and Stage 39C-E to audit whether any candidate should be locked as a new internal benchmark. It does not train new models, use external data, select candidates, or support validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| safety_audit_pass | True | all safety checks passed |
