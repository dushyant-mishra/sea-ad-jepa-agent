# Stage 27 non-graph v3 report

## 1. Executive summary

Best SEA-AD-only condition: `module_only_mlp` with mean pooled OOF Spearman `0.1883`.
Official baseline: module_mean_baseline = `0.3128`. Minimum v3 success threshold = `0.3228`.
This stage runs non-graph neural training regimes only. It does not support graph-topology claims.

## 2. What was run

- Stage 27A `v3_sea_ad_only_non_graph` over locked Stage 24 donor folds.
- Conditions: module_only_mlp, expression_residual_only_mlp, late_fusion_module_residual_mlp.
- Fold-local scaling, feature selection, target scaling, and inner validation.
- Bootstrap uncertainty: `True` with `500` donor resamples per completed condition/target.

## 3. What was not run

- No real graph branch.
- No no-graph/identity graph-control branch.
- No strict-shuffled graph branch.
- No external validation.
- No H5AD/expression matrix downloads.
- No manuscript claim update.

## 4. Dataset roles used

- SEA-AD internal donor-held-out folds were used for Stage 27A.
- Stage 27B external pretraining status: `missing_external_matrix`.
- Eligible external datasets in registry: `7`.
- Clean holdout datasets were not used.

## 5. Leakage controls

- Locked donor folds from Stage 24.
- All feature selection happens inside training folds only.
- Standard scalers fit on training donors only.
- Inner validation donors are selected from training donors only.
- Held-out donor targets are never used for fitting.

## 6. Architecture conditions

- `module_only_mlp`: predefined microglia module branch only.
- `expression_residual_only_mlp`: top-variance non-module expression residual branch only.
- `late_fusion_module_residual_mlp`: module and residual branches fused late.

## 7. SEA-AD-only results

```csv
run_id,architecture_condition,mean_pooled_oof_spearman,min_target_pooled_oof_spearman,n_targets
v3_sea_ad_only_non_graph,expression_residual_only_mlp,0.1484237782015982,-0.07801964159157639,5
v3_sea_ad_only_non_graph,late_fusion_module_residual_mlp,0.1781277802259438,-0.10073909081704971,5
v3_sea_ad_only_non_graph,module_only_mlp,0.18826769261921633,-0.10104282676926192,5
```

## 8. External-pretrained results or skipped status

Status: `missing_external_matrix`.
Usable local matrices: `none`.
No automatic external matrix download was attempted.

## 9. Comparison against module_mean_baseline = 0.3128

```csv
run_id,architecture_condition,target,pooled_oof_spearman,module_mean_baseline_target_spearman,delta_vs_module_mean_baseline
v3_sea_ad_only_non_graph,expression_residual_only_mlp,6e10/Aβ,0.04282676926192164,0.3267793864533765,-0.28395261719145487
v3_sea_ad_only_non_graph,expression_residual_only_mlp,AT8,0.16572929902662,0.5417434443656981,-0.37601414533907807
v3_sea_ad_only_non_graph,expression_residual_only_mlp,GFAP,0.14245216158752658,0.2607876885694037,-0.11833552698187713
v3_sea_ad_only_non_graph,expression_residual_only_mlp,Iba1,-0.07801964159157639,0.0291181532854105,-0.10713779487698688
v3_sea_ad_only_non_graph,expression_residual_only_mlp,NeuN,0.46913030272349904,0.405770983092032,0.06335931963146701
v3_sea_ad_only_non_graph,late_fusion_module_residual_mlp,6e10/Aβ,0.07739192062367116,0.3267793864533765,-0.24938746582970533
v3_sea_ad_only_non_graph,late_fusion_module_residual_mlp,AT8,0.20213024465508092,0.5417434443656981,-0.3396131997106172
v3_sea_ad_only_non_graph,late_fusion_module_residual_mlp,GFAP,0.22423812898653436,0.2607876885694037,-0.036549559582869345
v3_sea_ad_only_non_graph,late_fusion_module_residual_mlp,Iba1,-0.10073909081704971,0.0291181532854105,-0.12985724410246022
v3_sea_ad_only_non_graph,late_fusion_module_residual_mlp,NeuN,0.4876176976814823,0.405770983092032,0.08184671458945025
v3_sea_ad_only_non_graph,module_only_mlp,6e10/Aβ,0.14431507542776148,0.3267793864533765,-0.18246431102561503
v3_sea_ad_only_non_graph,module_only_mlp,AT8,0.4369950389794472,0.5417434443656981,-0.10474840538625091
v3_sea_ad_only_non_graph,module_only_mlp,GFAP,0.1832540245013668,0.2607876885694037,-0.07753366406803691
v3_sea_ad_only_non_graph,module_only_mlp,Iba1,-0.10104282676926192,0.0291181532854105,-0.13016098005467241
v3_sea_ad_only_non_graph,module_only_mlp,NeuN,0.27781715095676823,0.405770983092032,-0.1279538321352638
```

## 10. Pass/fail against 0.3228

```csv
run_id,architecture_condition,status,mean_pooled_oof_spearman,minimum_success_threshold,all_five_targets_reported,target_degradation_check_pass,clean_holdout_used,heldout_donor_leakage_detected,stage27_pass,notes
v3_sea_ad_only_non_graph,expression_residual_only_mlp,complete,0.1484237782015982,0.3228,True,False,False,False,False,SEA-AD-only non-graph v3 condition; no graph topology.
v3_sea_ad_only_non_graph,late_fusion_module_residual_mlp,complete,0.1781277802259438,0.3228,True,False,False,False,False,SEA-AD-only non-graph v3 condition; no graph topology.
v3_sea_ad_only_non_graph,module_only_mlp,complete,0.18826769261921633,0.3228,True,False,False,False,False,SEA-AD-only non-graph v3 condition; no graph topology.
v3_external_pretrained_non_graph,external_pretraining_interface,missing_external_matrix,,0.3228,False,False,False,False,False,No automatic downloads are allowed; Stage 27B is skipped unless approved local aligned matrices exist.
```

## 11. Target-level degradation check

A condition fails the target-level degradation gate if any target delta versus module_mean_baseline is `< -0.02`.

## 12. Recommendation for next stage

Use these Stage 27A results as the non-graph neural baseline. Stage 27B should remain skipped until approved local external matrices pass matrix, gene-overlap, donor-mapping, and role-registry audits. Graph branches should not be run until non-graph regimes and leakage checks are accepted.

## Fold audit

Fold assignment rows saved in OOF predictions and fold audit. Unique folds: `[1, 2, 3, 4, 5]`.
