# v3 primary baseline benchmark suite v1

## 1. Executive summary

Stage 25 evaluated the nine approved primary leakage-safe non-neural baselines using the locked Stage 24 donor folds. The current high-water mark is `module_mean_baseline` with mean OOF Spearman `0.3325` across the five pathology targets.

No v3 model, graph neural model, neural/deep baseline, transductive embedding, external validation, evidence-level change, candidate biology card, or manuscript prose was run.

## 2. Locked donor-fold protocol

- Runtime: `sea-ad-jepa-v3`
- Donors evaluated: `84`
- Folds: `5`
- Split unit: donor only; all preprocessing/model fitting happens inside training donors.
- Targets are transformed with `log1p` for regression; Spearman comparisons remain rank-based.

## 3. Primary baselines evaluated

- `raw_expression_ridge`
- `raw_expression_elasticnet`
- `pca_ridge`
- `pca_elasticnet`
- `module_mean_baseline`
- `wgcna_module_summary_ridge`
- `wgcna_module_summary_elasticnet`
- `xgboost_raw_expression`
- `lightgbm_raw_expression`

## 4. Leakage-safety protocol

- Locked donor folds from Stage 24 only.
- No cell-level random splits.
- Scalers, variance feature filters, PCA, ElasticNet inner CV, and models are fit inside each training fold only.
- PCA is fit on training donors and used only to transform held-out donors.
- Module mean features use target-independent predefined microglia modules.
- WGCNA module summaries use target-independent graph components from the WGCNA/TOM edge asset, without pathology labels.
- XGBoost/LightGBM use conservative shallow settings with no test-fold tuning.

## 5. Target-level performance

- 6e10/Aβ / `raw_expression_ridge`: Spearman=0.3175, R2=-0.1211, MAE=0.6070, RMSE=0.7271
- 6e10/Aβ / `module_mean_baseline`: Spearman=0.3170, R2=0.0579, MAE=0.5881, RMSE=0.6926
- 6e10/Aβ / `pca_ridge`: Spearman=0.2225, R2=-0.1556, MAE=0.6362, RMSE=0.7539
- 6e10/Aβ / `pca_elasticnet`: Spearman=0.1721, R2=-0.0726, MAE=0.6217, RMSE=0.7313
- 6e10/Aβ / `lightgbm_raw_expression`: Spearman=0.1245, R2=-0.1026, MAE=0.6217, RMSE=0.7387
- 6e10/Aβ / `xgboost_raw_expression`: Spearman=0.1055, R2=-0.1091, MAE=0.6292, RMSE=0.7413
- 6e10/Aβ / `raw_expression_elasticnet`: Spearman=0.0309, R2=-0.2674, MAE=0.6753, RMSE=0.7926
- 6e10/Aβ / `wgcna_module_summary_elasticnet`: Spearman=-0.0907, R2=-0.0595, MAE=0.6192, RMSE=0.7380
- 6e10/Aβ / `wgcna_module_summary_ridge`: Spearman=-0.1260, R2=-0.0723, MAE=0.6227, RMSE=0.7431
- AT8 / `lightgbm_raw_expression`: Spearman=0.6444, R2=0.3619, MAE=0.3641, RMSE=0.4459
- AT8 / `module_mean_baseline`: Spearman=0.5518, R2=0.3990, MAE=0.3400, RMSE=0.4278
- AT8 / `xgboost_raw_expression`: Spearman=0.5293, R2=0.3386, MAE=0.3836, RMSE=0.4604
- AT8 / `raw_expression_elasticnet`: Spearman=0.5109, R2=0.3570, MAE=0.3583, RMSE=0.4484
- AT8 / `raw_expression_ridge`: Spearman=0.4136, R2=0.1427, MAE=0.4061, RMSE=0.5072
- AT8 / `pca_elasticnet`: Spearman=0.3872, R2=0.1041, MAE=0.4438, RMSE=0.5295
- AT8 / `pca_ridge`: Spearman=0.3181, R2=0.0351, MAE=0.4369, RMSE=0.5414
- AT8 / `wgcna_module_summary_ridge`: Spearman=0.1727, R2=-0.0448, MAE=0.5023, RMSE=0.5754
- AT8 / `wgcna_module_summary_elasticnet`: Spearman=-0.0181, R2=-0.0669, MAE=0.5046, RMSE=0.5818
- GFAP / `module_mean_baseline`: Spearman=0.2494, R2=-0.0966, MAE=0.5071, RMSE=0.6021
- GFAP / `raw_expression_ridge`: Spearman=0.1840, R2=-0.3756, MAE=0.5597, RMSE=0.6701
- GFAP / `pca_elasticnet`: Spearman=0.1675, R2=-0.1091, MAE=0.5172, RMSE=0.6162
- GFAP / `xgboost_raw_expression`: Spearman=0.1624, R2=-0.1904, MAE=0.5276, RMSE=0.6322
- GFAP / `lightgbm_raw_expression`: Spearman=0.1556, R2=-0.1499, MAE=0.5217, RMSE=0.6281
- GFAP / `pca_ridge`: Spearman=0.1526, R2=-0.3751, MAE=0.5469, RMSE=0.6741
- GFAP / `raw_expression_elasticnet`: Spearman=0.0981, R2=-0.1704, MAE=0.5248, RMSE=0.6315
- GFAP / `wgcna_module_summary_ridge`: Spearman=-0.1151, R2=-0.2010, MAE=0.5472, RMSE=0.6405
- GFAP / `wgcna_module_summary_elasticnet`: Spearman=-0.1279, R2=-0.1961, MAE=0.5465, RMSE=0.6386
- Iba1 / `wgcna_module_summary_ridge`: Spearman=0.3145, R2=-0.0763, MAE=0.3411, RMSE=0.4257
- Iba1 / `wgcna_module_summary_elasticnet`: Spearman=0.3116, R2=-0.0828, MAE=0.3416, RMSE=0.4271
- Iba1 / `pca_elasticnet`: Spearman=0.2085, R2=-0.1591, MAE=0.3571, RMSE=0.4446
- Iba1 / `module_mean_baseline`: Spearman=0.1050, R2=-0.2026, MAE=0.3564, RMSE=0.4541
- Iba1 / `raw_expression_ridge`: Spearman=0.0953, R2=-0.4868, MAE=0.3905, RMSE=0.4974
- Iba1 / `lightgbm_raw_expression`: Spearman=0.0745, R2=-0.2784, MAE=0.3670, RMSE=0.4663
- Iba1 / `raw_expression_elasticnet`: Spearman=0.0558, R2=-0.1967, MAE=0.3559, RMSE=0.4512
- Iba1 / `pca_ridge`: Spearman=0.0213, R2=-0.4676, MAE=0.3761, RMSE=0.4964
- Iba1 / `xgboost_raw_expression`: Spearman=0.0125, R2=-0.3263, MAE=0.3744, RMSE=0.4755
- NeuN / `raw_expression_elasticnet`: Spearman=0.5923, R2=0.2999, MAE=0.3643, RMSE=0.4484
- NeuN / `pca_elasticnet`: Spearman=0.5654, R2=0.2662, MAE=0.3730, RMSE=0.4591
- NeuN / `pca_ridge`: Spearman=0.5077, R2=0.2381, MAE=0.3875, RMSE=0.4676
- NeuN / `xgboost_raw_expression`: Spearman=0.4875, R2=0.1552, MAE=0.4027, RMSE=0.4919
- NeuN / `module_mean_baseline`: Spearman=0.4394, R2=0.1416, MAE=0.4061, RMSE=0.4975
- NeuN / `raw_expression_ridge`: Spearman=0.4393, R2=0.1157, MAE=0.4157, RMSE=0.5048
- NeuN / `lightgbm_raw_expression`: Spearman=0.4019, R2=0.1206, MAE=0.4104, RMSE=0.5024
- NeuN / `wgcna_module_summary_ridge`: Spearman=0.1590, R2=-0.0371, MAE=0.4423, RMSE=0.5469
- NeuN / `wgcna_module_summary_elasticnet`: Spearman=0.0441, R2=-0.0802, MAE=0.4482, RMSE=0.5575

## 6. Mean OOF Spearman ranking

- 1. `module_mean_baseline`: mean=0.3325, median=0.3170
- 2. `pca_elasticnet`: mean=0.3001, median=0.2085
- 3. `raw_expression_ridge`: mean=0.2900, median=0.3175
- 4. `lightgbm_raw_expression`: mean=0.2802, median=0.1556
- 5. `xgboost_raw_expression`: mean=0.2594, median=0.1624
- 6. `raw_expression_elasticnet`: mean=0.2576, median=0.0981
- 7. `pca_ridge`: mean=0.2445, median=0.2225
- 8. `wgcna_module_summary_ridge`: mean=0.0810, median=0.1590
- 9. `wgcna_module_summary_elasticnet`: mean=0.0238, median=-0.0181

## 7. Pairwise deltas

Frozen small-difference band: `0.01`.

- baseline_vs_prior_graph_jepa_real_graph_latent: `lightgbm_raw_expression` vs `graph_jepa_real_graph_latent` on Iba1: Δ=-0.0529 (v3_target_updated)
- baseline_vs_prior_graph_jepa_real_graph_latent: `module_mean_baseline` vs `graph_jepa_real_graph_latent` on Iba1: Δ=-0.0224 (v3_target_updated)
- baseline_vs_prior_graph_jepa_real_graph_latent: `pca_elasticnet` vs `graph_jepa_real_graph_latent` on Iba1: Δ=0.0811 (new_high_watermark_established)
- baseline_vs_prior_graph_jepa_real_graph_latent: `pca_ridge` vs `graph_jepa_real_graph_latent` on Iba1: Δ=-0.1062 (v3_target_updated)
- baseline_vs_prior_graph_jepa_real_graph_latent: `raw_expression_elasticnet` vs `graph_jepa_real_graph_latent` on Iba1: Δ=-0.0717 (v3_target_updated)
- baseline_vs_prior_graph_jepa_real_graph_latent: `raw_expression_ridge` vs `graph_jepa_real_graph_latent` on Iba1: Δ=-0.0322 (v3_target_updated)
- baseline_vs_prior_graph_jepa_real_graph_latent: `wgcna_module_summary_elasticnet` vs `graph_jepa_real_graph_latent` on Iba1: Δ=0.1841 (new_high_watermark_established)
- baseline_vs_prior_graph_jepa_real_graph_latent: `wgcna_module_summary_ridge` vs `graph_jepa_real_graph_latent` on Iba1: Δ=0.1871 (new_high_watermark_established)
- baseline_vs_prior_graph_jepa_real_graph_latent: `xgboost_raw_expression` vs `graph_jepa_real_graph_latent` on Iba1: Δ=-0.1150 (v3_target_updated)
- baseline_vs_prior_graph_jepa_real_graph_latent: `lightgbm_raw_expression` vs `graph_jepa_real_graph_latent` on NeuN: Δ=-0.0909 (v3_target_updated)
- baseline_vs_prior_graph_jepa_real_graph_latent: `module_mean_baseline` vs `graph_jepa_real_graph_latent` on NeuN: Δ=-0.0534 (v3_target_updated)
- baseline_vs_prior_graph_jepa_real_graph_latent: `pca_elasticnet` vs `graph_jepa_real_graph_latent` on NeuN: Δ=0.0726 (new_high_watermark_established)
- baseline_vs_prior_graph_jepa_real_graph_latent: `pca_ridge` vs `graph_jepa_real_graph_latent` on NeuN: Δ=0.0150 (new_high_watermark_established)
- baseline_vs_prior_graph_jepa_real_graph_latent: `raw_expression_elasticnet` vs `graph_jepa_real_graph_latent` on NeuN: Δ=0.0995 (raw_expression_remains_competitive)
- baseline_vs_prior_graph_jepa_real_graph_latent: `raw_expression_ridge` vs `graph_jepa_real_graph_latent` on NeuN: Δ=-0.0535 (v3_target_updated)
- baseline_vs_prior_graph_jepa_real_graph_latent: `wgcna_module_summary_elasticnet` vs `graph_jepa_real_graph_latent` on NeuN: Δ=-0.4487 (v3_target_updated)
- baseline_vs_prior_graph_jepa_real_graph_latent: `wgcna_module_summary_ridge` vs `graph_jepa_real_graph_latent` on NeuN: Δ=-0.3338 (v3_target_updated)
- baseline_vs_prior_graph_jepa_real_graph_latent: `xgboost_raw_expression` vs `graph_jepa_real_graph_latent` on NeuN: Δ=-0.0052 (difference_within_small_band)
- best_primary_vs_old_v2_module_mean_target: `module_mean_baseline` vs `old_v2_module_mean_target_0.2999` on mean_across_targets: Δ=0.0326 (new_high_watermark_established)
- best_primary_vs_old_v2_real_graph_0.2892: `module_mean_baseline` vs `old_v2_real_graph_0.2892` on mean_across_targets: Δ=0.0433 (new_high_watermark_established)

Full pairwise table: `results/tables/v3_primary_baseline_pairwise_deltas_v1.csv`.

## 8. New high-water mark

- Old target: module_mean_baseline = `0.2999`
- Old v2 real Graph-JEPA = `0.2892`
- New target: best primary baseline mean OOF Spearman = `0.3325` from `module_mean_baseline`
- Minimum v3 success: best primary baseline + 0.01 = `0.3425` mean OOF Spearman

## 9. Implication for v3 success criterion

The v3 model should not be judged against the old module-mean target alone. It must exceed the Stage 25 best primary baseline by at least the frozen small-difference band.

## 10. Deferred baselines

t-SNE, UMAP, supervised UMAP, PHATE, diffusion maps, scVI/VAE, autoencoder, MLPs, graph-only GNN, v3 real graph, v3 no-graph, v3 strict shuffled graph, and causal estimator layers remain deferred.

## 11. Overfitting cautions

- n_donors is `84`, so XGBoost and LightGBM are high-capacity baselines despite conservative settings.
- ElasticNet uses inner training-fold CV only.
- WGCNA summaries are target-independent graph-derived means, not pathology-supervised modules.
- Raw expression feature count before fold-internal filtering: `36601`.
- Predefined module features: `15`; WGCNA module features: `2`.

## 12. Recommended Stage 26 plan

- Treat this benchmark as the new primary high-water mark.
- Audit whether the winning baseline is robust target-by-target before starting v3 training.
- Only after this benchmark is accepted, implement v3 controls in order: no-graph, strict shuffled graph, then real graph.
- Keep manifold/deep/causal baselines deferred until their leakage-safe protocols are explicitly approved.

## Target-specific winners

- 6e10/Aβ: `raw_expression_ridge` (0.3175)
- AT8: `lightgbm_raw_expression` (0.6444)
- GFAP: `module_mean_baseline` (0.2494)
- Iba1: `wgcna_module_summary_ridge` (0.3145)
- NeuN: `raw_expression_elasticnet` (0.5923)

## Direct questions

- XGBoost beats module mean: `False`.
- LightGBM beats module mean: `False`.
- Best WGCNA module summary beats module mean: `False`.
- Old v2 module mean remains best: `False`.
