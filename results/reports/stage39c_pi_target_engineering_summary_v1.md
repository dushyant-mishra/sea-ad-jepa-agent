# Stage 39C PI target-engineering summary

## Short answer

Best condition: `rank_int_module_pca_ridge`. Mean pooled OOF Spearman: `0.3458094563126456`. Delta versus Stage 27C: `0.019107016300496105`. Stage 39C internal rescue pass: `False`.

| best_condition | stage27c_reference_mean | best_mean_pooled_oof_spearman | delta_vs_stage27c | rescue_threshold | bootstrap_ci_lower_95 | bootstrap_ci_upper_95 | controls_pass | leakage_audit_pass | stage39c_internal_rescue_pass | recommended_next_step | allowed_claim_language | prohibited_claim_language |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rank_int_module_pca_ridge | 0.3267024400121495 | 0.3458094563126456 | 0.019107016300496105 | 0.3317024400121495 | 0.2384706378799647 | 0.4378608499288575 | True | True | False | do not replace Stage 27C; proceed to metadata/composition Stage 39D or refine target engineering | internal target-engineering benchmark; donor-held-out model comparison; hypothesis prioritization only | clean external validation; causal regulator; therapeutic target; disease-modifying target; gene-ablation result |

## What was tested

Train-fold-only target transformations were benchmarked with target-specific ridge/elastic-net/Huber models using locked donor-held-out folds. Metadata-only and donor-shuffled controls were included.

## Top conditions

| condition | mean_pooled_oof_spearman | min_target_spearman | n_targets |
| --- | --- | --- | --- |
| rank_int_module_pca_ridge | 0.3458094563126456 | 0.025473321858864025 | 5 |
| raw_log1p_module_pca_huber | 0.33112078566366304 | -0.02824744355573555 | 5 |
| covariate_residual_log1p_module_pca_ridge | 0.3215834767641997 | -0.11313151766730789 | 5 |
| raw_log1p_module_pca_elasticnet | 0.29264212616953955 | -0.08973054562289069 | 5 |
| raw_log1p_module_pca_ridge | 0.2920522425837805 | -0.09755998785056191 | 5 |
| winsor_log1p_module_pca_ridge | 0.28896628530930446 | -0.09745874253315785 | 5 |
| raw_log1p_metadata_only_ridge | 0.1414032600992204 | -0.18086463501063077 | 5 |
| raw_log1p_module_pca_ridge_donor_shuffled_control | -0.1687637946744963 | -0.26712564543889844 | 5 |

## Interpretation

No external validation, causal, therapeutic, disease-modifying, or gene-ablation claim is supported by Stage 39C. If this stage does not pass the strict rescue gate, Stage 27C remains the locked internal reference.
