# Stage 27 failure diagnosis v1

## Summary

Stage 27 output integrity checks passed: `14/14`.
The original neural failure is not explained by missing targets, fold mismatch, collapsed predictions, cell leakage, or use of fold-mean rather than pooled OOF Spearman.

## Likely failure mechanism

The donor cohort has only 84 samples. The Stage 27 MLPs used more capacity than the linear module baseline, sacrificed training donors to inner validation, and optimized MSE rather than rank correlation. The weak Iba1 and amyloid targets amplify this small-sample variance. This motivates low-capacity linear rescue before graph branches.

## Checks

```csv
check_id,status,passed,details
all_required_outputs_exist,pass,True,missing=none
all_five_targets_present,pass,True,6e10/Aβ; AT8; GFAP; Iba1; NeuN
all_three_stage27_conditions_present,pass,True,expression_residual_only_mlp; late_fusion_module_residual_mlp; module_only_mlp
oof_row_count_expected,pass,True,observed=1260 expected=1260
no_duplicate_oof_rows,pass,True,duplicate_rows=0
donor_folds_match_stage24,pass,True,observed_donors=84 locked_donors=84
no_cell_level_rows,pass,True,OOF table is donor-level
prediction_variance_not_collapsed,pass,True,minimum_prediction_variance=0.407297
target_variance_not_collapsed,pass,True,minimum_target_variance=2.19883
module_feature_construction_matches_stage25,pass,True,n_modules=15
target_log_inverse_handling_rank_consistent,pass,True,log1p/expm1 are monotonic; Spearman rank is preserved
official_comparison_uses_pooled_oof_spearman,pass,True,Stage 27 target metrics contain pooled_oof_spearman
heldout_donor_leakage_not_reported,pass,True,all rows false
clean_holdout_not_used,pass,True,all rows false
```

## Interpretation boundary

A trustworthy harness still requires exact reproduction of the official module baseline. Rescue results must not be interpreted until that reproduction gate passes.
