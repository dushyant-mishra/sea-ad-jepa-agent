# Stage 40A conditional dual-head EMA+VICReg report

Stage 40A is a conditional internal low-capacity dual-head EMA+VICReg experiment after Stage 39H did not recover a lockable proxy-safe context benchmark. It uses only internal module features, locked donor-held-out folds, and train-fold-only preprocessing. It does not use external data, proxy context features, graph additions, candidate selection, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims.

## Training gate

| inputs_found | stage39f_no_benchmark_locked | stage39h_no_proxy_safe_lock_candidate | torch_available | no_external_data | no_proxy_context_features | stage40a_training_allowed | reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| True | True | True | True | True | True | True | Stage 39F/H did not lock a new benchmark; conditional low-capacity Stage 40A allowed |

## Model registry

| condition | model_type | latent_dim | lock_candidate | comparator_only | shuffle_targets |
| --- | --- | --- | --- | --- | --- |
| stage39e_pca8_reference | reference_oof | 8 | False | True |  |
| dualhead_ema_vicreg_latent8 | dualhead_ema_vicreg | 8 | True | False |  |
| dualhead_ema_vicreg_latent16 | dualhead_ema_vicreg | 16 | True | False |  |
| supervised_mlp_no_ema_latent8_control | supervised_mlp_no_ema | 8 | False | True |  |
| dualhead_ema_vicreg_latent8_target_shuffled_control | dualhead_ema_vicreg | 8 | False | True | True |

## Mean metrics

| condition | mean_pooled_oof_spearman | min_target_spearman | n_targets |
| --- | --- | --- | --- |
| stage39e_pca8_reference | 0.35808116279206914 | 0.056974172849842526 | 5 |
| dualhead_ema_vicreg_latent16 | 0.20855839806587548 | 0.020962768894271955 | 5 |
| supervised_mlp_no_ema_latent8_control | 0.17951896940658757 | -0.04807259127589806 | 5 |
| dualhead_ema_vicreg_latent8 | 0.1767506072685233 | -0.049389093670224316 | 5 |
| dualhead_ema_vicreg_latent8_target_shuffled_control | 0.009599712884185317 | -0.10716636615404931 | 5 |

## Target metrics and guards

| condition | target | n_donors | pooled_oof_spearman | prediction_variance |
| --- | --- | --- | --- | --- |
| dualhead_ema_vicreg_latent16 | 6e10/A_beta | 84 | 0.2431781130030666 | 0.5496390948670743 |
| dualhead_ema_vicreg_latent16 | AT8 | 84 | 0.38818061798632963 | 0.6993510925970637 |
| dualhead_ema_vicreg_latent16 | GFAP | 84 | 0.1654059230016288 | 0.44205633129393573 |
| dualhead_ema_vicreg_latent16 | Iba1 | 84 | 0.020962768894271955 | 0.35886672519352214 |
| dualhead_ema_vicreg_latent16 | NeuN | 84 | 0.2250645674440804 | 0.4363818912013889 |
| dualhead_ema_vicreg_latent8 | 6e10/A_beta | 84 | 0.21274033269757617 | 0.5357986276131947 |
| dualhead_ema_vicreg_latent8 | AT8 | 84 | 0.3987119437729886 | 0.6649927545451031 |
| dualhead_ema_vicreg_latent8 | GFAP | 84 | -0.04391854340994637 | 0.5305410303710839 |
| dualhead_ema_vicreg_latent8 | Iba1 | 84 | -0.049389093670224316 | 0.2805996175561506 |
| dualhead_ema_vicreg_latent8 | NeuN | 84 | 0.36560839695222247 | 0.3206970966151751 |
| dualhead_ema_vicreg_latent8_target_shuffled_control | 6e10/A_beta | 84 | 0.03051881266570475 | 0.29805196170155157 |
| dualhead_ema_vicreg_latent8_target_shuffled_control | AT8 | 84 | -0.10716636615404931 | 0.3008581120988734 |
| dualhead_ema_vicreg_latent8_target_shuffled_control | GFAP | 84 | 0.14665168219110983 | 0.32551180008425157 |
| dualhead_ema_vicreg_latent8_target_shuffled_control | Iba1 | 84 | -0.04040649656432131 | 0.2858236479093049 |
| dualhead_ema_vicreg_latent8_target_shuffled_control | NeuN | 84 | 0.018400932282482636 | 0.26249983892267575 |
| stage39e_pca8_reference | 6e10/A_beta | 84 | 0.3746733755407961 | 0.10149201227703833 |
| stage39e_pca8_reference | AT8 | 84 | 0.5155185235317487 | 0.4521366514818513 |
| stage39e_pca8_reference | GFAP | 84 | 0.3823049963928304 | 0.06945277597660786 |
| stage39e_pca8_reference | Iba1 | 84 | 0.056974172849842526 | 0.014534498810187995 |
| stage39e_pca8_reference | NeuN | 84 | 0.4609347456451279 | 0.3345980282262346 |
| supervised_mlp_no_ema_latent8_control | 6e10/A_beta | 84 | 0.205568968818612 | 0.5232626725869792 |
| supervised_mlp_no_ema_latent8_control | AT8 | 84 | 0.3763936341251075 | 0.5949992862336326 |
| supervised_mlp_no_ema_latent8_control | GFAP | 84 | -0.005468299156414812 | 0.4160546793117336 |
| supervised_mlp_no_ema_latent8_control | Iba1 | 84 | -0.04807259127589806 | 0.26657761916550016 |
| supervised_mlp_no_ema_latent8_control | NeuN | 84 | 0.3691731345215311 | 0.3201447092088396 |

| condition | target | target_score | stage39e_pca8_reference | delta_vs_stage39e_pca8 | guard_threshold | target_guard_pass |
| --- | --- | --- | --- | --- | --- | --- |
| dualhead_ema_vicreg_latent16 | 6e10/A_beta | 0.2431781130030666 | 0.3746733755407961 | -0.1314952625377295 | -0.05 | False |
| dualhead_ema_vicreg_latent16 | AT8 | 0.38818061798632963 | 0.5155185235317487 | -0.12733790554541902 | -0.05 | False |
| dualhead_ema_vicreg_latent16 | GFAP | 0.1654059230016288 | 0.3823049963928304 | -0.2168990733912016 | -0.05 | False |
| dualhead_ema_vicreg_latent16 | Iba1 | 0.020962768894271955 | 0.056974172849842526 | -0.03601140395557057 | -0.05 | True |
| dualhead_ema_vicreg_latent16 | NeuN | 0.2250645674440804 | 0.4609347456451279 | -0.23587017820104747 | -0.05 | False |
| dualhead_ema_vicreg_latent8 | 6e10/A_beta | 0.21274033269757617 | 0.3746733755407961 | -0.16193304284321994 | -0.05 | False |
| dualhead_ema_vicreg_latent8 | AT8 | 0.3987119437729886 | 0.5155185235317487 | -0.11680657975876008 | -0.05 | False |
| dualhead_ema_vicreg_latent8 | GFAP | -0.04391854340994637 | 0.3823049963928304 | -0.4262235398027768 | -0.05 | False |
| dualhead_ema_vicreg_latent8 | Iba1 | -0.049389093670224316 | 0.056974172849842526 | -0.10636326652006683 | -0.05 | False |
| dualhead_ema_vicreg_latent8 | NeuN | 0.36560839695222247 | 0.4609347456451279 | -0.0953263486929054 | -0.05 | False |
| dualhead_ema_vicreg_latent8_target_shuffled_control | 6e10/A_beta | 0.03051881266570475 | 0.3746733755407961 | -0.34415456287509133 | -0.05 | False |
| dualhead_ema_vicreg_latent8_target_shuffled_control | AT8 | -0.10716636615404931 | 0.5155185235317487 | -0.6226848896857979 | -0.05 | False |
| dualhead_ema_vicreg_latent8_target_shuffled_control | GFAP | 0.14665168219110983 | 0.3823049963928304 | -0.23565331420172056 | -0.05 | False |
| dualhead_ema_vicreg_latent8_target_shuffled_control | Iba1 | -0.04040649656432131 | 0.056974172849842526 | -0.09738066941416385 | -0.05 | False |
| dualhead_ema_vicreg_latent8_target_shuffled_control | NeuN | 0.018400932282482636 | 0.4609347456451279 | -0.44253381336264525 | -0.05 | False |
| stage39e_pca8_reference | 6e10/A_beta | 0.3746733755407961 | 0.3746733755407961 | 0.0 | -0.05 | True |
| stage39e_pca8_reference | AT8 | 0.5155185235317487 | 0.5155185235317487 | 0.0 | -0.05 | True |
| stage39e_pca8_reference | GFAP | 0.3823049963928304 | 0.3823049963928304 | 0.0 | -0.05 | True |
| stage39e_pca8_reference | Iba1 | 0.056974172849842526 | 0.056974172849842526 | 0.0 | -0.05 | True |
| stage39e_pca8_reference | NeuN | 0.4609347456451279 | 0.4609347456451279 | 0.0 | -0.05 | True |
| supervised_mlp_no_ema_latent8_control | 6e10/A_beta | 0.205568968818612 | 0.3746733755407961 | -0.1691044067221841 | -0.05 | False |
| supervised_mlp_no_ema_latent8_control | AT8 | 0.3763936341251075 | 0.5155185235317487 | -0.13912488940664114 | -0.05 | False |
| supervised_mlp_no_ema_latent8_control | GFAP | -0.005468299156414812 | 0.3823049963928304 | -0.3877732955492452 | -0.05 | False |
| supervised_mlp_no_ema_latent8_control | Iba1 | -0.04807259127589806 | 0.056974172849842526 | -0.10504676412574059 | -0.05 | False |
| supervised_mlp_no_ema_latent8_control | NeuN | 0.3691731345215311 | 0.4609347456451279 | -0.09176161112359676 | -0.05 | False |

## Bootstrap and Iba1

| condition | n_bootstrap | ci_lower_95 | ci_upper_95 | lower_ci_above_stage27c | lower_ci_above_material_threshold |
| --- | --- | --- | --- | --- | --- |
| dualhead_ema_vicreg_latent16 | 500 | 0.08744154637976982 | 0.3196575261390173 | False | False |
| dualhead_ema_vicreg_latent8 | 500 | 0.05618325229843622 | 0.27940169103932816 | False | False |
| dualhead_ema_vicreg_latent8_target_shuffled_control | 500 | -0.12213319718446718 | 0.11556958253887754 | False | False |
| stage39e_pca8_reference | 500 | 0.24500594348797894 | 0.4550058824577675 | False | False |
| supervised_mlp_no_ema_latent8_control | 500 | 0.03631608156849642 | 0.28627701186812565 | False | False |

| condition | target | n_donors | pooled_oof_spearman | prediction_variance | stage39e_pca8_iba1_reference | delta_vs_stage39e_pca8 | iba1_nonnegative | iba1_improved_vs_stage39e_pca8 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dualhead_ema_vicreg_latent16 | Iba1 | 84 | 0.020962768894271955 | 0.35886672519352214 | 0.056974172849842526 | -0.03601140395557057 | True | False |
| dualhead_ema_vicreg_latent8 | Iba1 | 84 | -0.049389093670224316 | 0.2805996175561506 | 0.056974172849842526 | -0.10636326652006683 | False | False |
| dualhead_ema_vicreg_latent8_target_shuffled_control | Iba1 | 84 | -0.04040649656432131 | 0.2858236479093049 | 0.056974172849842526 | -0.09738066941416385 | False | False |
| stage39e_pca8_reference | Iba1 | 84 | 0.056974172849842526 | 0.014534498810187995 | 0.056974172849842526 | 0.0 | True | False |
| supervised_mlp_no_ema_latent8_control | Iba1 | 84 | -0.04807259127589806 | 0.26657761916550016 | 0.056974172849842526 | -0.10504676412574059 | False | False |

## Negative controls and benchmark decision

| condition | mean_pooled_oof_spearman | min_target_spearman | n_targets | real_score | control_score | delta_vs_control | control_pass |
| --- | --- | --- | --- | --- | --- | --- | --- |
| dualhead_ema_vicreg_latent8_target_shuffled_control | 0.009599712884185317 | -0.10716636615404931 | 5 | 0.20855839806587548 | 0.009599712884185317 | 0.19895868518169016 | True |
| stage39e_pca8_reference | 0.35808116279206914 | 0.056974172849842526 | 5 | 0.20855839806587548 | 0.35808116279206914 | -0.14952276472619366 | False |
| supervised_mlp_no_ema_latent8_control | 0.17951896940658757 | -0.04807259127589806 | 5 | 0.20855839806587548 | 0.17951896940658757 | 0.029039428659287908 | True |

| condition | model_type | mean_pooled_oof_spearman | delta_vs_stage27c | delta_vs_stage39e_pca8 | lower_ci_above_stage27c | lower_ci_above_material_threshold | target_guard_pass | iba1_nonnegative | iba1_improved_vs_stage39e_pca8 | negative_controls_pass | benchmark_lock_eligible | recommended_decision | allowed_claim_language | prohibited_claim_language |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dualhead_ema_vicreg_latent16 | dualhead_ema_vicreg | 0.20855839806587548 | -0.11814404194627401 | -0.14952276472619366 | False | False | False | True | False | False | False | does_not_improve_over_stage39e_pca8 | conditional internal representation-learning rescue experiment; donor-held-out model comparison only | external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim |
| dualhead_ema_vicreg_latent8 | dualhead_ema_vicreg | 0.1767506072685233 | -0.1499518327436262 | -0.18133055552354585 | False | False | False | False | False | False | False | does_not_improve_over_stage39e_pca8 | conditional internal representation-learning rescue experiment; donor-held-out model comparison only | external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim |
| dualhead_ema_vicreg_latent8_target_shuffled_control | dualhead_ema_vicreg | 0.009599712884185317 | -0.31710272712796417 | -0.3484814499078838 | False | False | False | False | False | False | False | does_not_improve_over_stage39e_pca8 | conditional internal representation-learning rescue experiment; donor-held-out model comparison only | external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim |
| stage39e_pca8_reference | reference_oof | 0.35808116279206914 | 0.031378722779919654 | 0.0 | False | False | True | True | False | False | False | does_not_improve_over_stage39e_pca8 | conditional internal representation-learning rescue experiment; donor-held-out model comparison only | external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim |
| supervised_mlp_no_ema_latent8_control | supervised_mlp_no_ema | 0.17951896940658757 | -0.14718347060556192 | -0.17856219338548157 | False | False | False | False | False | False | False | does_not_improve_over_stage39e_pca8 | conditional internal representation-learning rescue experiment; donor-held-out model comparison only | external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim |

## Claim boundaries

| audit_item | pass | evidence |
| --- | --- | --- |
| conditional_after_stage39h_no_lock | True | Stage 40A is a conditional internal low-capacity dual-head EMA+VICReg experiment after Stage 39H did not recover a lockable proxy-safe context benchmark. It uses only internal module features, locked donor-held-out folds, and train-fold-only preprocessing. It does not use external data, proxy context features, graph additions, candidate selection, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| no_external_data_used | True | Stage 40A is a conditional internal low-capacity dual-head EMA+VICReg experiment after Stage 39H did not recover a lockable proxy-safe context benchmark. It uses only internal module features, locked donor-held-out folds, and train-fold-only preprocessing. It does not use external data, proxy context features, graph additions, candidate selection, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| no_external_model_selection | True | Stage 40A is a conditional internal low-capacity dual-head EMA+VICReg experiment after Stage 39H did not recover a lockable proxy-safe context benchmark. It uses only internal module features, locked donor-held-out folds, and train-fold-only preprocessing. It does not use external data, proxy context features, graph additions, candidate selection, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| no_proxy_context_features | True | Stage 40A is a conditional internal low-capacity dual-head EMA+VICReg experiment after Stage 39H did not recover a lockable proxy-safe context benchmark. It uses only internal module features, locked donor-held-out folds, and train-fold-only preprocessing. It does not use external data, proxy context features, graph additions, candidate selection, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| no_graph_additions | True | Stage 40A is a conditional internal low-capacity dual-head EMA+VICReg experiment after Stage 39H did not recover a lockable proxy-safe context benchmark. It uses only internal module features, locked donor-held-out folds, and train-fold-only preprocessing. It does not use external data, proxy context features, graph additions, candidate selection, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| no_candidate_selection | True | Stage 40A is a conditional internal low-capacity dual-head EMA+VICReg experiment after Stage 39H did not recover a lockable proxy-safe context benchmark. It uses only internal module features, locked donor-held-out folds, and train-fold-only preprocessing. It does not use external data, proxy context features, graph additions, candidate selection, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| donor_held_out_evaluation_preserved | True | Stage 40A is a conditional internal low-capacity dual-head EMA+VICReg experiment after Stage 39H did not recover a lockable proxy-safe context benchmark. It uses only internal module features, locked donor-held-out folds, and train-fold-only preprocessing. It does not use external data, proxy context features, graph additions, candidate selection, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| train_fold_only_preprocessing_preserved | True | Stage 40A is a conditional internal low-capacity dual-head EMA+VICReg experiment after Stage 39H did not recover a lockable proxy-safe context benchmark. It uses only internal module features, locked donor-held-out folds, and train-fold-only preprocessing. It does not use external data, proxy context features, graph additions, candidate selection, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| negative_controls_reported | True | Stage 40A is a conditional internal low-capacity dual-head EMA+VICReg experiment after Stage 39H did not recover a lockable proxy-safe context benchmark. It uses only internal module features, locked donor-held-out folds, and train-fold-only preprocessing. It does not use external data, proxy context features, graph additions, candidate selection, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| no_clean_external_validation_claim | True | Stage 40A is a conditional internal low-capacity dual-head EMA+VICReg experiment after Stage 39H did not recover a lockable proxy-safe context benchmark. It uses only internal module features, locked donor-held-out folds, and train-fold-only preprocessing. It does not use external data, proxy context features, graph additions, candidate selection, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| no_causal_claim | True | Stage 40A is a conditional internal low-capacity dual-head EMA+VICReg experiment after Stage 39H did not recover a lockable proxy-safe context benchmark. It uses only internal module features, locked donor-held-out folds, and train-fold-only preprocessing. It does not use external data, proxy context features, graph additions, candidate selection, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| no_therapeutic_claim | True | Stage 40A is a conditional internal low-capacity dual-head EMA+VICReg experiment after Stage 39H did not recover a lockable proxy-safe context benchmark. It uses only internal module features, locked donor-held-out folds, and train-fold-only preprocessing. It does not use external data, proxy context features, graph additions, candidate selection, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| no_gene_ablation_claim | True | Stage 40A is a conditional internal low-capacity dual-head EMA+VICReg experiment after Stage 39H did not recover a lockable proxy-safe context benchmark. It uses only internal module features, locked donor-held-out folds, and train-fold-only preprocessing. It does not use external data, proxy context features, graph additions, candidate selection, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| no_disease_modifying_claim | True | Stage 40A is a conditional internal low-capacity dual-head EMA+VICReg experiment after Stage 39H did not recover a lockable proxy-safe context benchmark. It uses only internal module features, locked donor-held-out folds, and train-fold-only preprocessing. It does not use external data, proxy context features, graph additions, candidate selection, or support external validation, causal, therapeutic, disease-modifying, or gene-ablation claims. |
| safety_audit_pass | True | all safety checks passed |
