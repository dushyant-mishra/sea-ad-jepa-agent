# Stage73 context-specific GRN graph-JEPA diagnostic

## Prediction lock decision

| context_graph_mean | no_graph_mean | string_graph_mean | target_shuffled_mean | gene_label_permuted_mean | beats_stage27c_mean | beats_no_graph_mean | beats_string_mean | beats_target_shuffled_mean | beats_gene_label_permuted_mean | bootstrap_vs_no_graph_positive | bootstrap_vs_all_graph_controls_positive | beats_stage41c_descriptive | context_graph_prediction_lock |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.323611 | 0.311254 | 0.331809 | 0.323611 | 0.323611 | False | True | False | False | False | True | False | False | False |

## Seed summary

| condition | mean_score | median_score | min_score | max_score |
| --- | --- | --- | --- | --- |
| string_graph_aux | 0.331809 | 0.33726 | 0.320482 | 0.340002 |
| context_grn_aux | 0.323611 | 0.33168 | 0.294146 | 0.336187 |
| gene_label_permuted_grn_aux | 0.323611 | 0.33168 | 0.294146 | 0.336187 |
| target_shuffled_grn_aux | 0.323611 | 0.33168 | 0.294146 | 0.336187 |
| no_graph_raw | 0.311254 | 0.311795 | 0.29705 | 0.332712 |

## Bootstrap deltas

| comparison | mean_delta | ci_lower_2p5 | ci_upper_97p5 | bootstrap_iterations | bootstrap_level |
| --- | --- | --- | --- | --- | --- |
| context_grn_vs_stage27c | -0.00269643 | -0.017543 | 0.00812311 | 1000 | seed_summary |
| context_grn_vs_no_graph | 0.0126242 | 0.00136722 | 0.0220925 | 1000 | seed_summary |
| context_grn_vs_string | -0.00779656 | -0.0256781 | 0.00556039 | 1000 | seed_summary |
| context_grn_vs_target_shuffled | 0 | 0 | 0 | 1000 | seed_summary |
| context_grn_vs_gene_label_permuted | 0 | 0 | 0 | 1000 | seed_summary |

## Claim boundary

| stage73_internal_graph_prior_diagnostic_only | uses_frozen_stage72b_edges | uses_frozen_stage64_68_signature | no_graph_threshold_tuning | no_new_candidate_selection | no_model_architecture_search | no_external_validation_claim | no_causal_claim | no_therapeutic_claim | no_gene_ablation_claim | no_validated_grn_claim | raw_data_not_committed | safety_audit_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| True | True | True | True | True | True | True | True | True | True | True | True | True |
