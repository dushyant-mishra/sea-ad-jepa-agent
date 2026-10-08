# v3 generalization and stability gates v1

## 1. Executive summary

Stage 26 establishes robustness gates around the Stage 25B official pooled donor-level OOF metric. The official internal benchmark remains `module_mean_baseline` at pooled mean OOF Spearman `0.3128`; the minimum internal v3 success target is `0.3228`.

No v3 training, graph neural model, external validation, evidence-level change, candidate biology card, or manuscript prose was run.

## 2. Official v3 benchmark target

- Official metric: pooled donor-level OOF Spearman.
- Module baseline pooled mean OOF Spearman: `0.3128`.
- Required margin: `+0.01`.
- Minimum internal v3 success target: `0.3228`.

## 3. Why fold-mean metric was superseded

Stage 25 used mean fold-level Spearman, which is noisy with approximately 16-17 held-out donors per fold. Stage 25B recomputed per-donor pooled OOF Spearman and superseded the fold-mean-derived 0.3425 target.

## 4. Bootstrap uncertainty

Top mean-across-target bootstrap intervals:

- `module_mean_baseline`: pooled=0.3128, CI=(0.2154, 0.3939)
- `lightgbm_raw_expression`: pooled=0.2679, CI=(0.1729, 0.3527)
- `raw_expression_ridge`: pooled=0.2644, CI=(0.1772, 0.3559)
- `xgboost_raw_expression`: pooled=0.2462, CI=(0.1465, 0.3306)
- `raw_expression_elasticnet`: pooled=0.2367, CI=(0.1411, 0.3163)

Module baseline target-level bootstrap intervals:

- 6e10/Aβ: pooled=0.3268, CI=(0.1363, 0.5124)
- AT8: pooled=0.5417, CI=(0.3499, 0.7037)
- GFAP: pooled=0.2608, CI=(0.0482, 0.4584)
- Iba1: pooled=0.0291, CI=(-0.1907, 0.2621)
- NeuN: pooled=0.4058, CI=(0.2095, 0.5685)

## 5. Target-specific stability

- `module_mean_baseline`: mean=0.3128, worst=Iba1 (0.0291), best=AT8 (0.5417), spread=0.5126, passes=True
- `lightgbm_raw_expression`: mean=0.2679, worst=Iba1 (-0.0078), best=AT8 (0.5994), spread=0.6072, passes=False
- `raw_expression_ridge`: mean=0.2644, worst=Iba1 (0.0339), best=AT8 (0.4317), spread=0.3979, passes=False
- `xgboost_raw_expression`: mean=0.2462, worst=Iba1 (-0.0713), best=AT8 (0.5207), spread=0.5920, passes=False
- `raw_expression_elasticnet`: mean=0.2367, worst=Iba1 (-0.0563), best=NeuN (0.5727), spread=0.6290, passes=False
- `pca_ridge`: mean=0.2297, worst=Iba1 (-0.0022), best=NeuN (0.4951), spread=0.4973, passes=False
- `pca_elasticnet`: mean=0.2182, worst=Iba1 (-0.0747), best=NeuN (0.5407), spread=0.6155, passes=False
- `wgcna_module_summary_ridge`: mean=-0.0278, worst=GFAP (-0.2358), best=Iba1 (0.2629), spread=0.4987, passes=False
- `wgcna_module_summary_elasticnet`: mean=-0.0742, worst=6e10/Aβ (-0.2207), best=Iba1 (0.2583), spread=0.4789, passes=False

Future v3 must report all five targets and must not hide a target-specific degradation behind a higher mean.

## 6. Stratum stability

Stratum rows generated: `540`; underpowered rows: `0`. Underpowered strata report log1p-scale MAE rather than Spearman and should not be overinterpreted.

- `lightgbm_raw_expression` / diagnosis: mean powered-stratum metric=0.1897
- `lightgbm_raw_expression` / locked_fold_pathology_stratum: mean powered-stratum metric=0.1373
- `lightgbm_raw_expression` / pathology_stratum: mean powered-stratum metric=0.1373
- `lightgbm_raw_expression` / sex: mean powered-stratum metric=0.2584
- `module_mean_baseline` / diagnosis: mean powered-stratum metric=0.2360
- `module_mean_baseline` / locked_fold_pathology_stratum: mean powered-stratum metric=0.1126
- `module_mean_baseline` / pathology_stratum: mean powered-stratum metric=0.1126
- `module_mean_baseline` / sex: mean powered-stratum metric=0.3040
- `pca_elasticnet` / diagnosis: mean powered-stratum metric=0.1318
- `pca_elasticnet` / locked_fold_pathology_stratum: mean powered-stratum metric=0.0464
- `pca_elasticnet` / pathology_stratum: mean powered-stratum metric=0.0464
- `pca_elasticnet` / sex: mean powered-stratum metric=0.2154
- `pca_ridge` / diagnosis: mean powered-stratum metric=0.1489
- `pca_ridge` / locked_fold_pathology_stratum: mean powered-stratum metric=0.1041
- `pca_ridge` / pathology_stratum: mean powered-stratum metric=0.1041
- `pca_ridge` / sex: mean powered-stratum metric=0.2272
- `raw_expression_elasticnet` / diagnosis: mean powered-stratum metric=0.1589
- `raw_expression_elasticnet` / locked_fold_pathology_stratum: mean powered-stratum metric=0.0341
- `raw_expression_elasticnet` / pathology_stratum: mean powered-stratum metric=0.0341
- `raw_expression_elasticnet` / sex: mean powered-stratum metric=0.2297

## 7. Generalization gates for future v3

- `pooled_oof_required`: pooled donor-level OOF Spearman reported for every target
- `beat_module_mean_by_0p01`: >= 0.3228 mean pooled OOF Spearman
- `no_large_target_degradation`: target_delta_vs_module_mean >= -0.02 for every target
- `bootstrap_uncertainty_reported`: >=500 donor bootstrap resamples; 1000 preferred
- `target_specific_performance_required`: all five target metrics reported
- `graph_controls_required`: real graph > no-graph and strict-shuffled under pooled OOF gate
- `stratum_reporting_required_if_powered`: report strata with n>=8; mark smaller strata underpowered
- `no_external_generalization_claim_without_external_validation`: external validation required for external-generalization claims
- `anti_overfitting_controls`: predeclared model-selection protocol only

## 8. Anti-overfitting rules

- n donors = 84.
- Internal donor CV is not external validation.
- High-capacity models require stricter gates.
- Model selection must not use test-fold labels.
- No target dropping after results.
- No threshold changes after results.
- No external generalization claim without external validation.

## 9. Recommended Stage 27 plan

- Implement a minimal non-graph v3 predictor first: module branch + expression residual branch + target-specific heads.
- Compare it against module_mean_baseline, raw_expression_ridge, and pca_elasticnet.
- Use pooled donor-level OOF only.
- Only after that add typed graph branches and graph controls.

## Protocol audit carry-forward

- aggregation_check: pass_with_revision; risk=medium
- prediction_storage_check: pass; risk=low
- apples_to_apples_v2_comparison: caution; risk=medium
- module_baseline_sanity_check: pass; risk=low
- generalization_caution: caution; risk=medium
