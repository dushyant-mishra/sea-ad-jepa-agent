# Stage 40A PI conditional dual-head summary

## Short answer

Lock-eligible Stage 40A candidates: `0`.

## Mean metrics

| condition | mean_pooled_oof_spearman | min_target_spearman | n_targets |
| --- | --- | --- | --- |
| stage39e_pca8_reference | 0.35808116279206914 | 0.056974172849842526 | 5 |
| dualhead_ema_vicreg_latent16 | 0.20855839806587548 | 0.020962768894271955 | 5 |
| supervised_mlp_no_ema_latent8_control | 0.17951896940658757 | -0.04807259127589806 | 5 |
| dualhead_ema_vicreg_latent8 | 0.1767506072685233 | -0.049389093670224316 | 5 |
| dualhead_ema_vicreg_latent8_target_shuffled_control | 0.009599712884185317 | -0.10716636615404931 | 5 |

## Benchmark decision

| condition | model_type | mean_pooled_oof_spearman | delta_vs_stage27c | delta_vs_stage39e_pca8 | lower_ci_above_stage27c | lower_ci_above_material_threshold | target_guard_pass | iba1_nonnegative | iba1_improved_vs_stage39e_pca8 | negative_controls_pass | benchmark_lock_eligible | recommended_decision | allowed_claim_language | prohibited_claim_language |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dualhead_ema_vicreg_latent16 | dualhead_ema_vicreg | 0.20855839806587548 | -0.11814404194627401 | -0.14952276472619366 | False | False | False | True | False | False | False | does_not_improve_over_stage39e_pca8 | conditional internal representation-learning rescue experiment; donor-held-out model comparison only | external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim |
| dualhead_ema_vicreg_latent8 | dualhead_ema_vicreg | 0.1767506072685233 | -0.1499518327436262 | -0.18133055552354585 | False | False | False | False | False | False | False | does_not_improve_over_stage39e_pca8 | conditional internal representation-learning rescue experiment; donor-held-out model comparison only | external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim |
| dualhead_ema_vicreg_latent8_target_shuffled_control | dualhead_ema_vicreg | 0.009599712884185317 | -0.31710272712796417 | -0.3484814499078838 | False | False | False | False | False | False | False | does_not_improve_over_stage39e_pca8 | conditional internal representation-learning rescue experiment; donor-held-out model comparison only | external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim |
| stage39e_pca8_reference | reference_oof | 0.35808116279206914 | 0.031378722779919654 | 0.0 | False | False | True | True | False | False | False | does_not_improve_over_stage39e_pca8 | conditional internal representation-learning rescue experiment; donor-held-out model comparison only | external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim |
| supervised_mlp_no_ema_latent8_control | supervised_mlp_no_ema | 0.17951896940658757 | -0.14718347060556192 | -0.17856219338548157 | False | False | False | False | False | False | False | does_not_improve_over_stage39e_pca8 | conditional internal representation-learning rescue experiment; donor-held-out model comparison only | external validation; clean validation; causal mechanism; therapeutic target; validated biology; gene-ablation support; disease-modifying claim |

## Safe interpretation

Stage 40A is an internal conditional representation-learning experiment. It does not establish external validation, causality, therapeutic relevance, disease modification, or gene-ablation support.
