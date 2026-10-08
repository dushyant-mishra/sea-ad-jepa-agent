# v3 primary baseline protocol audit v1

## 1. Executive summary

Stage 25 used mean fold-level Spearman for its ranking. Stage 25B recomputed deterministic per-donor OOF predictions and recommends pooled donor-level OOF Spearman as the official benchmark metric.

Module mean pooled OOF Spearman is `0.3128` versus Stage 25 fold-mean `0.3325`. Official pooled best baseline is `module_mean_baseline` at `0.3128`, so the recommended minimum v3 target is `0.3228`.

No v3 training, graph neural model, external validation, evidence-level change, candidate biology card, or manuscript prose was run.

## 2. Why the Stage 25 number increased

The Stage 25 increase partly reflects a stronger locked donor-fold module baseline, but it was reported using mean fold-level correlations. With 16-17 donors per fold, fold-level Spearman is noisy. Pooled donor-level OOF Spearman is the safer official aggregation.

## 3. Fold-mean vs pooled OOF comparison

- 6e10/Aβ: fold_mean=0.3170, pooled=0.3268, difference=0.0098
- AT8: fold_mean=0.5518, pooled=0.5417, difference=-0.0100
- GFAP: fold_mean=0.2494, pooled=0.2608, difference=0.0114
- Iba1: fold_mean=0.1050, pooled=0.0291, difference=-0.0759
- NeuN: fold_mean=0.4394, pooled=0.4058, difference=-0.0336

Pooled ranking:

- `module_mean_baseline`: pooled mean OOF Spearman=0.3128
- `lightgbm_raw_expression`: pooled mean OOF Spearman=0.2679
- `raw_expression_ridge`: pooled mean OOF Spearman=0.2644
- `xgboost_raw_expression`: pooled mean OOF Spearman=0.2462
- `raw_expression_elasticnet`: pooled mean OOF Spearman=0.2367
- `pca_ridge`: pooled mean OOF Spearman=0.2297
- `pca_elasticnet`: pooled mean OOF Spearman=0.2182
- `wgcna_module_summary_ridge`: pooled mean OOF Spearman=-0.0278
- `wgcna_module_summary_elasticnet`: pooled mean OOF Spearman=-0.0742

## 4. Apples-to-apples comparison with v2 baseline

- donor_count: same (risk=medium)
- fold_split: unknown (risk=medium)
- target_table: same (risk=medium)
- feature_table: unknown (risk=high)
- module_definitions: unknown (risk=high)
- target_transform: unknown (risk=medium)
- metric_aggregation: different (risk=high)
- missing_target_handling: same (risk=low)

The v2 comparison is not fully apples-to-apples unless exact feature table, module definitions, target transform, and aggregation provenance are reconciled.

## 5. Module baseline leakage sanity check

Module definitions come from `src/sea_ad_jepa/gene_sets.py` and are target-independent named microglia modules. Stage 25B confirms module means are computed from expression values only; pathology targets are not used to define module features, and held-out donor target values are not used in feature construction.

## 6. Generalization risk

Locked donor CV prevents cell leakage but does not prove external cohort generalization. External/stress tests are required before broad generalization claims.

## 7. Official recommended v3 benchmark target

- Old target: module_mean_baseline = `0.2999`
- Old v2 real Graph-JEPA = `0.2892`
- Stage 25 fold-mean module mean = `0.3325`
- Stage 25B pooled module mean = `0.3128`
- Official pooled best primary baseline = `module_mean_baseline` at `0.3128`
- Recommended minimum v3 success = `0.3228`

The official target should use the pooled best primary baseline: module_mean_baseline at 0.3128, giving minimum v3 success 0.3228.

## 8. Recommended next stage

- Treat pooled donor-level OOF Spearman as official.
- Update Stage 25 report/target language if desired so fold-mean values are audit-only.
- Before v3 training, decide whether to reconcile v2/Stage25 feature and module provenance or use Stage25B as a new locked internal benchmark.
- Do not start v3 neural model training until this target policy is accepted.

## Audit table summary

- aggregation_check: pass_with_revision; risk=medium; Stage25 ranking used mean fold-level Spearman. Pooled module_mean_baseline mean OOF Spearman is 0.3128 vs fold-mean 0.3325 (difference -0.0197).
- prediction_storage_check: pass; risk=low; Per-donor OOF predictions recomputed and saved for 84 donors.
- apples_to_apples_v2_comparison: caution; risk=medium; 5 protocol components are unknown or different at medium/high risk.
- module_baseline_sanity_check: pass; risk=low; Module features are computed from expression-only predefined target-independent modules; module feature sources observed: ['predefined_microglia_gene_modules'].
- generalization_caution: caution; risk=medium; Locked donor CV prevents cell leakage but does not prove external cohort generalization.

Leakage stop condition:

No high-risk leakage failure was detected.
