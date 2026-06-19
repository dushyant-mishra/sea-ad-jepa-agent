# v3 locked donor folds and benchmark harness v1

## 1. Executive summary

Stage 24 locked donor-level folds and the no-training benchmark harness for `Causal Module-Gated Typed Perturbation Graph-JEPA v3`. It created manifests only; no v3 training, full benchmark suite, external validation, evidence-level changes, candidate biology cards, or manuscript prose were run.

## 2. Runtime used

- Runtime environment: `sea-ad-jepa-v3`
- Python: 3.11.15
- Package status: 18/18 packages import successfully

## 3. Locked donor fold protocol

- Fold seed: `7`
- Requested/default folds: `5`
- Locked donors: `84`
- Actual folds: `5`
- Split unit: donor only; Stage 25 must never split cells from the same donor across train/test.
- Fold table stores each donor's held-out outer fold assignment. For fold k, train on all donors with `fold_id != k` and test on donors with `fold_id == k`.

## 4. Target manifest

- AT8 (`percent AT8 positive area_Grey matter`): available=True, donors=84
- 6e10/Aβ (`percent 6e10 positive area_Grey matter`): available=True, donors=84
- GFAP (`percent GFAP positive area_Grey matter`): available=True, donors=84
- Iba1 (`percent Iba1 positive area_Grey matter`): available=True, donors=84
- NeuN (`percent NeuN positive area_Grey matter`): available=True, donors=84

All five pathology targets are preserved before seeing v3 benchmark results; targets must not be dropped post hoc.

## 5. Primary benchmark baselines

- `raw_expression_ridge`: fit scaler/model on training donors only; evaluate held-out donors
- `raw_expression_elasticnet`: fit scaler/model and hyperparameters inside training donors only
- `pca_ridge`: fit PCA on training donors/cells; transform held-out donors/cells
- `pca_elasticnet`: fit PCA and ElasticNet inside training folds; transform held-out donors/cells
- `module_mean_baseline`: use target-independent predefined modules; aggregate held-out donors without target access
- `wgcna_module_summary_ridge`: use precomputed target-independent WGCNA modules or recompute modules inside each training fold
- `wgcna_module_summary_elasticnet`: use precomputed target-independent WGCNA modules or recompute modules inside each training fold
- `xgboost_raw_expression`: feature screening, scaling, and model fitting occur inside training donors only
- `lightgbm_raw_expression`: feature screening, scaling, and model fitting occur inside training donors only

## 6. Leakage-sensitive/deferred baselines

- `wgcna_module_summary_ridge` (medium): use precomputed target-independent WGCNA modules or recompute modules inside each training fold
- `wgcna_module_summary_elasticnet` (medium): use precomputed target-independent WGCNA modules or recompute modules inside each training fold
- `tsne_knn_or_ridge` (high): exclude from primary unless a documented train-only fit plus valid held-out transform is used
- `umap_ridge_or_knn` (medium): fit UMAP on training donors/cells and transform held-out donors/cells
- `supervised_umap` (high): must not use held-out target labels; train labels only if used at all
- `phate_ridge_or_knn` (high): exclude from primary unless a documented train/test transform protocol is used
- `diffusion_maps_ridge_or_knn` (high): exclude from primary unless a documented train/test transform protocol is used
- `autoencoder_latent_ridge` (medium): train autoencoder only on training donors/cells; encode held-out donors/cells after training
- `vae_or_scvi_latent_ridge` (medium): train VAE/scVI only on training donors/cells; encode held-out donors/cells after training
- `expression_only_mlp` (medium): train MLP only on training donors/cells with held-out donors untouched
- `module_only_mlp` (medium): train MLP only on training donors using leakage-free module summaries
- `graph_only_gnn` (medium): train only on training donor folds; no held-out donor labels in graph supervision
- `v3_no_graph` (medium): train only on training donor folds; compare against real graph and shuffled graph
- `v3_strict_shuffled_graph` (medium): train only on training donor folds using predeclared shuffled graph
- `v3_real_graph` (medium): train only after baseline suite is locked and scored; donor folds fixed
- `perturbation_latent_delta_baseline` (medium): estimate perturbation deltas only from training donors; apply frozen rule to held-out donors
- `module_delta_perturbation_baseline` (medium): estimate module deltas only from training donors; no held-out target use
- `causal_inference_estimator_layer` (medium): fit causal estimators on training donors only; report assumptions separately

Transductive embeddings over all donors/cells are exploratory only and excluded from the primary benchmark.

## 7. Runtime package status

18/18 packages import successfully. See `results/tables/v3_benchmark_runtime_package_status_v1.csv` for versions and notes.

## 8. Smoke-test results

- donor_folds_built: pass (donors=84; folds=[1, 2, 3, 4, 5])
- target_manifest_built: pass (AT8:n=84; 6e10/Aβ:n=84; GFAP:n=84; Iba1:n=84; NeuN:n=84)
- baseline_registry_leakage_labels: pass ({'deferred': 12, 'primary': 9, 'exploratory': 4})
- runtime_package_imports: pass (available=18/18)
- tiny_synthetic_ridge_smoke: pass (fit 8 synthetic samples; predicted 4 held-out synthetic samples)

The tiny ridge smoke test is synthetic and is not a biological result.

## 9. Recommended Stage 25 plan

- Run the full baseline benchmark suite using these locked donor folds.
- Start with raw expression, PCA, module/WGCNA, XGBoost, and LightGBM baselines.
- Include UMAP/PHATE/diffusion/t-SNE only with clearly labeled leakage-safe or exploratory protocols.
- Do not start the v3 neural model until baselines are locked and scored.

## 10. Anti-leakage rules

- Donor IDs define split boundaries; no cell leakage across donor folds.
- All scaling, feature selection, PCA, module recomputation, manifold fitting, neural latent training, and causal fitting must occur inside training donors only.
- Held-out donors may only be transformed or scored by artifacts fitted without their labels or cells.
- WGCNA/module summaries are primary only if precomputed without target leakage or recomputed within training folds.
- Supervised UMAP must not use test labels.
- scVI/VAE baselines must be trained only on training folds if used for a primary benchmark.
- Any all-donor/cell transductive embedding must be labeled exploratory and excluded from primary comparisons.
