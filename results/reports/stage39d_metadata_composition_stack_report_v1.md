# Stage 39D metadata/composition stack report

Stage 39D is an internal metadata/composition enrichment benchmark. It uses locked donor-held-out folds, train-fold-only preprocessing, safe donor metadata, and local SEA-AD microglia/PVM composition features. Composition features are audited for possible pathology-proxy signal before being treated as a credible benchmark improvement. It does not use external data, select candidates, or claim clean external validation, causality, therapeutic relevance, disease modification, or gene ablation.

## Feature blocks

| feature_block | n_features_available | source | allowed | proxy_risk_note |
| --- | --- | --- | --- | --- |
| latent_module_pca | 15 | Stage 27C reconstructed module features | True |  |
| safe_metadata | 7 | SEA-AD donor metadata safe covariates | True |  |
| microglia_pvm_composition | 33 | local SEA-AD microglia/PVM H5AD obs | True | 13 high-risk and 8 moderate-risk proxy features flagged; restricted sensitivity required |

## Model registry

| condition | feature_blocks | include_interactions | shuffled_context_control | model |
| --- | --- | --- | --- | --- |
| stage39c_rank_int_latent_only_reproduction | latent | False | False | ridge |
| rank_int_metadata_only_ridge | metadata | False | False | ridge |
| rank_int_composition_only_ridge | composition | False | False | ridge |
| rank_int_metadata_composition_ridge | metadata;composition | False | False | ridge |
| rank_int_latent_metadata_ridge | latent;metadata | False | False | ridge |
| rank_int_latent_composition_ridge | latent;composition | False | False | ridge |
| rank_int_latent_metadata_composition_ridge | latent;metadata;composition | False | False | ridge |
| rank_int_latent_metadata_composition_interactions_ridge | latent;metadata;composition | True | False | ridge |
| rank_int_latent_metadata_composition_shuffled_context_control | latent;metadata;composition | False | True | ridge |

## Mean metrics

| condition | mean_pooled_oof_spearman | min_target_spearman | n_targets |
| --- | --- | --- | --- |
| rank_int_latent_composition_ridge | 0.5048658499544396 | 0.13704566163814924 | 5 |
| rank_int_latent_metadata_composition_interactions_ridge | 0.5008970335122 | 0.15126050420168066 | 5 |
| rank_int_latent_metadata_composition_ridge | 0.498382099827883 | 0.17146906955553307 | 5 |
| rank_int_composition_only_ridge | 0.4915379163713679 | 0.23203401842664775 | 5 |
| rank_int_metadata_composition_ridge | 0.4906996051432621 | 0.23557760453579024 | 5 |
| rank_int_latent_metadata_ridge | 0.37668522830819073 | 0.013688366913030272 | 5 |
| stage39c_rank_int_latent_only_reproduction | 0.3458094563126456 | 0.025473321858864025 | 5 |
| rank_int_metadata_only_ridge | 0.24245418649387468 | 0.009800546724713984 | 5 |
| rank_int_latent_metadata_composition_shuffled_context_control | -0.03221221018527893 | -0.0770274374810165 | 5 |

## Target metrics

| condition | target | n_donors | pooled_oof_spearman | mse | prediction_variance |
| --- | --- | --- | --- | --- | --- |
| rank_int_composition_only_ridge | 6e10/A_beta | 84 | 0.7314771691809254 | 1.624995737369859 | 0.9438872020928611 |
| rank_int_composition_only_ridge | AT8 | 84 | 0.6914447706793561 | 0.5895648570160906 | 0.38551077058793076 |
| rank_int_composition_only_ridge | GFAP | 84 | 0.32358003442340794 | 3.4534076908166065 | 0.20038864760203964 |
| rank_int_composition_only_ridge | Iba1 | 84 | 0.23203401842664775 | 2.240354688537049 | 0.1458815464211695 |
| rank_int_composition_only_ridge | NeuN | 84 | 0.47915358914650197 | 2.0106582768834818 | 0.2792774201994675 |
| rank_int_latent_composition_ridge | 6e10/A_beta | 84 | 0.7684114609699302 | 1.55008681348345 | 0.9053318306527455 |
| rank_int_latent_composition_ridge | AT8 | 84 | 0.7183152779183962 | 0.5525358572956729 | 0.4156210383670228 |
| rank_int_latent_composition_ridge | GFAP | 84 | 0.35885390300698594 | 3.4963998846302666 | 0.14969417128191442 |
| rank_int_latent_composition_ridge | Iba1 | 84 | 0.13704566163814924 | 2.3144223629030525 | 0.03616504188196694 |
| rank_int_latent_composition_ridge | NeuN | 84 | 0.5417029462387365 | 1.9404236088879987 | 0.32115843177616415 |
| rank_int_latent_metadata_composition_interactions_ridge | 6e10/A_beta | 84 | 0.8196820897033513 | 1.3949001685697238 | 0.9801142716384421 |
| rank_int_latent_metadata_composition_interactions_ridge | AT8 | 84 | 0.7006580945631263 | 0.6013889501405151 | 0.4896155214528206 |
| rank_int_latent_metadata_composition_interactions_ridge | GFAP | 84 | 0.31207856636630554 | 3.583592155583606 | 0.16927483165838192 |
| rank_int_latent_metadata_composition_interactions_ridge | Iba1 | 84 | 0.15126050420168066 | 2.3083593377462526 | 0.01773486881477034 |
| rank_int_latent_metadata_composition_interactions_ridge | NeuN | 84 | 0.5208059127265364 | 1.9911820262601456 | 0.33252050126206445 |
| rank_int_latent_metadata_composition_ridge | 6e10/A_beta | 84 | 0.8306975802369141 | 1.3754904175277174 | 0.9635379112288214 |
| rank_int_latent_metadata_composition_ridge | AT8 | 84 | 0.6985724410246026 | 0.5983989388718687 | 0.49170105718184987 |
| rank_int_latent_metadata_composition_ridge | GFAP | 84 | 0.2972157537713881 | 3.5705641252513436 | 0.1647159008015473 |
| rank_int_latent_metadata_composition_ridge | Iba1 | 84 | 0.17146906955553307 | 2.3093613761973666 | 0.017429953868224796 |
| rank_int_latent_metadata_composition_ridge | NeuN | 84 | 0.493955654550977 | 1.9789263045747916 | 0.3783507390693839 |
| rank_int_latent_metadata_composition_shuffled_context_control | 6e10/A_beta | 84 | -0.0770274374810165 | 1.4219150603401565 | 0.027647480639866467 |
| rank_int_latent_metadata_composition_shuffled_context_control | AT8 | 84 | -0.07093246937329149 | 0.837805320857401 | 0.10735276042071742 |
| rank_int_latent_metadata_composition_shuffled_context_control | GFAP | 84 | -0.01105598866052445 | 3.2733677471253237 | 0.06893823157747508 |
| rank_int_latent_metadata_composition_shuffled_context_control | Iba1 | 84 | -0.048597752353953624 | 2.380330929744625 | 0.01467647647600977 |
| rank_int_latent_metadata_composition_shuffled_context_control | NeuN | 84 | 0.04655259694239142 | 1.7890372460905213 | 0.04782344594159731 |
| rank_int_latent_metadata_ridge | 6e10/A_beta | 84 | 0.6347878910600385 | 1.2359782571732871 | 0.17448780091714397 |
| rank_int_latent_metadata_ridge | AT8 | 84 | 0.566791535891465 | 0.5663668530745556 | 0.22732575681854078 |
| rank_int_latent_metadata_ridge | GFAP | 84 | 0.26627518477270423 | 3.543800702547558 | 0.0739063196812901 |
| rank_int_latent_metadata_ridge | Iba1 | 84 | 0.013688366913030272 | 2.3354698770837246 | 0.0007796245759191342 |
| rank_int_latent_metadata_ridge | NeuN | 84 | 0.40188316290371573 | 1.7932286002980122 | 0.15060775423534864 |
| rank_int_metadata_composition_ridge | 6e10/A_beta | 84 | 0.8248051027639971 | 1.326934451311132 | 0.8157189496704133 |
| rank_int_metadata_composition_ridge | AT8 | 84 | 0.6708919712463299 | 0.617568212618185 | 0.46499189158356014 |
| rank_int_metadata_composition_ridge | GFAP | 84 | 0.24420370557861698 | 3.56888586462582 | 0.142626822654985 |
| rank_int_metadata_composition_ridge | Iba1 | 84 | 0.23557760453579024 | 2.247270202278633 | 0.17518012455422097 |
| rank_int_metadata_composition_ridge | NeuN | 84 | 0.47801964159157645 | 1.9699763785002848 | 0.27498470288531757 |
| rank_int_metadata_only_ridge | 6e10/A_beta | 84 | 0.5211906449326719 | 1.2685010963955226 | 0.4004891415683777 |
| rank_int_metadata_only_ridge | AT8 | 84 | 0.4066011946947454 | 0.6892471091765424 | 0.2467789528171272 |
| rank_int_metadata_only_ridge | GFAP | 84 | 0.08283891870001013 | 3.526186758124357 | 0.053307302123140964 |
| rank_int_metadata_only_ridge | Iba1 | 84 | 0.009800546724713984 | 2.3020027554081657 | 0.009991064996179312 |
| rank_int_metadata_only_ridge | NeuN | 84 | 0.19183962741723196 | 1.7707670519115137 | 0.012508521882261314 |
| stage39c_rank_int_latent_only_reproduction | 6e10/A_beta | 84 | 0.4001619925078465 | 1.3450791882953692 | 0.061414404161107855 |
| stage39c_rank_int_latent_only_reproduction | AT8 | 84 | 0.5254834463906044 | 0.5725139813852933 | 0.35410125835464334 |
| stage39c_rank_int_latent_only_reproduction | GFAP | 84 | 0.3122608079376329 | 3.605536437235708 | 0.062052522739399506 |
| stage39c_rank_int_latent_only_reproduction | Iba1 | 84 | 0.025473321858864025 | 2.4380960327601033 | 0.013426922850304128 |
| stage39c_rank_int_latent_only_reproduction | NeuN | 84 | 0.46566771286827985 | 1.8357926008866228 | 0.35088751377278565 |

## Block ablations and controls

| comparison | delta | passes |
| --- | --- | --- |
| best_vs_latent_only | 0.15905639364179402 | True |
| best_vs_metadata_only | 0.26241166346056494 | True |
| best_vs_composition_only | 0.013327933583071716 | True |
| best_vs_shuffled_context_control | 0.5370780601397186 | True |

## Composition proxy audit

The composition block is potentially powerful but risky: donor-level summaries of pseudo-progression or disease-enriched cell-state labels can encode pathology context. Stage 39D therefore reports full-composition performance and restricted sensitivity modes separately. The context-enrichment pass is only true if the restricted `no_pseudo_no_seaad` mode remains above Stage 39C.

| feature | source_family | proxy_risk_level | matched_terms | recommended_use | allowed_in_full_context_benchmark | allowed_in_restricted_sensitivity |
| --- | --- | --- | --- | --- | --- | --- |
| composition_count_Supertype_Micro_PVM_2_1_SEAAD | fine_cell_state_supertype | high_pathology_proxy_risk | seaa;supertype | exclude_from_primary_safe_benchmark | True | False |
| composition_count_Supertype_Micro_PVM_2_3_SEAAD | fine_cell_state_supertype | high_pathology_proxy_risk | seaa;supertype | exclude_from_primary_safe_benchmark | True | False |
| composition_count_Supertype_Micro_PVM_3_SEAAD | fine_cell_state_supertype | high_pathology_proxy_risk | seaa;supertype | exclude_from_primary_safe_benchmark | True | False |
| composition_count_Supertype_Micro_PVM_4_SEAAD | fine_cell_state_supertype | high_pathology_proxy_risk | seaa;supertype | exclude_from_primary_safe_benchmark | True | False |
| composition_prop_Supertype_Micro_PVM_2_1_SEAAD | fine_cell_state_supertype | high_pathology_proxy_risk | seaa;supertype | exclude_from_primary_safe_benchmark | True | False |
| composition_prop_Supertype_Micro_PVM_2_3_SEAAD | fine_cell_state_supertype | high_pathology_proxy_risk | seaa;supertype | exclude_from_primary_safe_benchmark | True | False |
| composition_prop_Supertype_Micro_PVM_3_SEAAD | fine_cell_state_supertype | high_pathology_proxy_risk | seaa;supertype | exclude_from_primary_safe_benchmark | True | False |
| composition_prop_Supertype_Micro_PVM_4_SEAAD | fine_cell_state_supertype | high_pathology_proxy_risk | seaa;supertype | exclude_from_primary_safe_benchmark | True | False |
| composition_pseudoprogression_max | pseudoprogression_summary | high_pathology_proxy_risk | pseudoprogression | exclude_from_primary_safe_benchmark | True | False |
| composition_pseudoprogression_mean | pseudoprogression_summary | high_pathology_proxy_risk | pseudoprogression | exclude_from_primary_safe_benchmark | True | False |
| composition_pseudoprogression_median | pseudoprogression_summary | high_pathology_proxy_risk | pseudoprogression | exclude_from_primary_safe_benchmark | True | False |
| composition_pseudoprogression_min | pseudoprogression_summary | high_pathology_proxy_risk | pseudoprogression | exclude_from_primary_safe_benchmark | True | False |
| composition_pseudoprogression_std | pseudoprogression_summary | high_pathology_proxy_risk | pseudoprogression | exclude_from_primary_safe_benchmark | True | False |
| composition_count_Brain Region_Human_MTG | other_composition_feature | low_obvious_proxy_risk |  | allowed_if_train_fold_only | True | True |
| composition_count_Brain Region_Human_MTG_All_Layers | other_composition_feature | low_obvious_proxy_risk |  | allowed_if_train_fold_only | True | True |
| composition_count_Brain Region_Human_MTG_L5 | other_composition_feature | low_obvious_proxy_risk |  | allowed_if_train_fold_only | True | True |
| composition_count_Class_Non_neuronal_and_Non_neural | broad_class_composition | low_obvious_proxy_risk |  | allowed_if_train_fold_only | True | True |
| composition_count_Subclass_Microglia_PVM | broad_subclass_composition | low_obvious_proxy_risk |  | allowed_if_train_fold_only | True | True |
| composition_prop_Brain Region_Human_MTG | other_composition_feature | low_obvious_proxy_risk |  | allowed_if_train_fold_only | True | True |
| composition_prop_Brain Region_Human_MTG_All_Layers | other_composition_feature | low_obvious_proxy_risk |  | allowed_if_train_fold_only | True | True |
| composition_prop_Brain Region_Human_MTG_L5 | other_composition_feature | low_obvious_proxy_risk |  | allowed_if_train_fold_only | True | True |
| composition_prop_Class_Non_neuronal_and_Non_neural | broad_class_composition | low_obvious_proxy_risk |  | allowed_if_train_fold_only | True | True |
| composition_prop_Subclass_Microglia_PVM | broad_subclass_composition | low_obvious_proxy_risk |  | allowed_if_train_fold_only | True | True |
| composition_total_cells | cell_count | low_obvious_proxy_risk |  | allowed_if_train_fold_only | True | True |
| microglia_pvm_n_cells | cell_count | low_obvious_proxy_risk |  | allowed_if_train_fold_only | True | True |
| composition_count_Supertype_Lymphocyte | fine_cell_state_supertype | moderate_cell_state_proxy_risk | supertype | sensitivity_only | True | True |
| composition_count_Supertype_Micro_PVM_1 | fine_cell_state_supertype | moderate_cell_state_proxy_risk | supertype | sensitivity_only | True | True |
| composition_count_Supertype_Micro_PVM_2 | fine_cell_state_supertype | moderate_cell_state_proxy_risk | supertype | sensitivity_only | True | True |
| composition_count_Supertype_Monocyte | fine_cell_state_supertype | moderate_cell_state_proxy_risk | supertype | sensitivity_only | True | True |
| composition_prop_Supertype_Lymphocyte | fine_cell_state_supertype | moderate_cell_state_proxy_risk | supertype | sensitivity_only | True | True |

## Restricted composition sensitivity

| sensitivity_mode | condition | n_composition_features | mean_pooled_oof_spearman | delta_vs_full_best | delta_vs_stage39c | proxy_sensitivity_interpretation | 6e10/A_beta_spearman | AT8_spearman | GFAP_spearman | Iba1_spearman | NeuN_spearman |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_composition | sensitivity_full_composition_latent_composition_ridge | 33 | 0.5048658499544396 | 0.0 | 0.15905639364179402 | full context benchmark; includes audited proxy-risk features | 0.7684114609699302 | 0.7183152779183962 | 0.35885390300698594 | 0.13704566163814924 | 0.5417029462387365 |
| no_pseudoprogression | sensitivity_no_pseudoprogression_latent_composition_ridge | 28 | 0.296766224562114 | -0.20809962539232563 | -0.0490432317505316 | does_not_survive_restricted_proxy_removal | 0.26390604434544906 | 0.48198845803381596 | 0.2563328946036246 | 0.11436671053963755 | 0.3672370152880429 |
| no_seaad_supertypes | sensitivity_no_seaad_supertypes_latent_composition_ridge | 25 | 0.5231183557760454 | 0.018252505821605758 | 0.17730889946339978 | survives restricted proxy removal versus Stage39C | 0.7760858560291587 | 0.6968512706287334 | 0.37958894401133947 | 0.18467145894502382 | 0.5783942492659715 |
| no_pseudo_no_seaad | sensitivity_no_pseudo_no_seaad_latent_composition_ridge | 20 | 0.31541966184063985 | -0.18944618811379976 | -0.030389794472005738 | does_not_survive_restricted_proxy_removal | 0.2755492558469171 | 0.44797003138604846 | 0.2499544396071682 | 0.16701427558975396 | 0.43661030677331175 |
| broad_subclass_count_only | sensitivity_broad_subclass_count_only_latent_composition_ridge | 6 | 0.34010732003644834 | -0.16475852991799128 | -0.005702136276197256 | does_not_survive_restricted_proxy_removal | 0.3193074820289562 | 0.5080895008605852 | 0.356019034119672 | 0.04837501265566467 | 0.4687455705173636 |

## Delta versus Stage 39C and Stage 27C

| best_condition | stage27c_reference_mean | stage39c_best_mean | best_mean_pooled_oof_spearman | delta_vs_stage27c | delta_vs_stage39c | bootstrap_ci_lower_95 | bootstrap_ci_upper_95 | n_targets_improved_vs_stage39c | block_ablation_pass | leakage_audit_pass | n_high_pathology_proxy_features | n_moderate_cell_state_proxy_features | no_pseudo_no_seaad_mean_pooled_oof_spearman | broad_subclass_count_only_mean_pooled_oof_spearman | composition_proxy_sensitivity_pass | stage39d_context_enrichment_pass | recommended_next_step | allowed_claim_language | prohibited_claim_language |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rank_int_latent_composition_ridge | 0.3267024400121495 | 0.3458094563126456 | 0.5048658499544396 | 0.17816340994229013 | 0.15905639364179402 | 0.4243225718919451 | 0.5696572943742619 | 5 | True | True | 13 | 8 | 0.31541966184063985 | 0.34010732003644834 | False | False | do not replace Stage 39C yet; inspect composition proxy sensitivity before treating Stage 39D as a benchmark | internal metadata/composition enrichment benchmark; donor-held-out model comparison; hypothesis prioritization only | clean external validation; causal regulator; therapeutic target; disease-modifying target; gene-ablation result |

## Bootstrap CI

| condition | n_bootstrap | bootstrap_mean | ci_lower_95 | ci_upper_95 |
| --- | --- | --- | --- | --- |
| rank_int_latent_composition_ridge | 500 | 0.4980204698450781 | 0.4243225718919451 | 0.5696572943742619 |

## Leakage and claim audits

| covariate_column | forbidden_term_hits | leakage_risk | allowed_for_stage39c | audit_type | audit_item | pass | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Age at Death |  | False | True | covariate |  |  |  |
| PMI |  | False | True | covariate |  |  |  |
| RIN |  | False | True | covariate |  |  |  |
| Years of education |  | False | True | covariate |  |  |  |
| Sex |  | False | True | covariate |  |  |  |
| APOE Genotype |  | False | True | covariate |  |  |  |
| Primary Study Name |  | False | True | covariate |  |  |  |
|  |  |  |  | oof | no_duplicate_condition_target_donor_rows | True | duplicate_rows=0 |
|  |  |  |  | oof | heldout_donor_leakage_not_detected | True | heldout_donor_leakage_detected=False |
|  |  |  |  | oof | clean_holdout_not_used | True | clean_holdout_used=False |

| audit_item | pass | evidence |
| --- | --- | --- |
| train_fold_only_preprocessing | True | Stage 39D is an internal metadata/composition enrichment benchmark. It uses locked donor-held-out folds, train-fold-only preprocessing, safe donor metadata, and local SEA-AD microglia/PVM composition features. Composition features are audited for possible pathology-proxy signal before being treated as a credible benchmark improvement. It does not use external data, select candidates, or claim clean external validation, causality, therapeutic relevance, disease modification, or gene ablation. |
| donor_heldout_only | True | Stage 39D is an internal metadata/composition enrichment benchmark. It uses locked donor-held-out folds, train-fold-only preprocessing, safe donor metadata, and local SEA-AD microglia/PVM composition features. Composition features are audited for possible pathology-proxy signal before being treated as a credible benchmark improvement. It does not use external data, select candidates, or claim clean external validation, causality, therapeutic relevance, disease modification, or gene ablation. |
| no_external_data | True | Stage 39D is an internal metadata/composition enrichment benchmark. It uses locked donor-held-out folds, train-fold-only preprocessing, safe donor metadata, and local SEA-AD microglia/PVM composition features. Composition features are audited for possible pathology-proxy signal before being treated as a credible benchmark improvement. It does not use external data, select candidates, or claim clean external validation, causality, therapeutic relevance, disease modification, or gene ablation. |
| no_candidate_selection | True | Stage 39D is an internal metadata/composition enrichment benchmark. It uses locked donor-held-out folds, train-fold-only preprocessing, safe donor metadata, and local SEA-AD microglia/PVM composition features. Composition features are audited for possible pathology-proxy signal before being treated as a credible benchmark improvement. It does not use external data, select candidates, or claim clean external validation, causality, therapeutic relevance, disease modification, or gene ablation. |
| no_clean_external_validation_claim | True | Stage 39D is an internal metadata/composition enrichment benchmark. It uses locked donor-held-out folds, train-fold-only preprocessing, safe donor metadata, and local SEA-AD microglia/PVM composition features. Composition features are audited for possible pathology-proxy signal before being treated as a credible benchmark improvement. It does not use external data, select candidates, or claim clean external validation, causality, therapeutic relevance, disease modification, or gene ablation. |
| no_causal_claim | True | Stage 39D is an internal metadata/composition enrichment benchmark. It uses locked donor-held-out folds, train-fold-only preprocessing, safe donor metadata, and local SEA-AD microglia/PVM composition features. Composition features are audited for possible pathology-proxy signal before being treated as a credible benchmark improvement. It does not use external data, select candidates, or claim clean external validation, causality, therapeutic relevance, disease modification, or gene ablation. |
| no_therapeutic_claim | True | Stage 39D is an internal metadata/composition enrichment benchmark. It uses locked donor-held-out folds, train-fold-only preprocessing, safe donor metadata, and local SEA-AD microglia/PVM composition features. Composition features are audited for possible pathology-proxy signal before being treated as a credible benchmark improvement. It does not use external data, select candidates, or claim clean external validation, causality, therapeutic relevance, disease modification, or gene ablation. |
| no_gene_ablation_claim | True | Stage 39D is an internal metadata/composition enrichment benchmark. It uses locked donor-held-out folds, train-fold-only preprocessing, safe donor metadata, and local SEA-AD microglia/PVM composition features. Composition features are audited for possible pathology-proxy signal before being treated as a credible benchmark improvement. It does not use external data, select candidates, or claim clean external validation, causality, therapeutic relevance, disease modification, or gene ablation. |
| negative_null_results_reported | True | Stage 39D is an internal metadata/composition enrichment benchmark. It uses locked donor-held-out folds, train-fold-only preprocessing, safe donor metadata, and local SEA-AD microglia/PVM composition features. Composition features are audited for possible pathology-proxy signal before being treated as a credible benchmark improvement. It does not use external data, select candidates, or claim clean external validation, causality, therapeutic relevance, disease modification, or gene ablation. |
| safety_audit_pass | True | all safety checks passed |
