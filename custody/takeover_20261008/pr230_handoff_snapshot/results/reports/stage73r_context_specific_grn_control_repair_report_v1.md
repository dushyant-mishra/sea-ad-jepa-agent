# Stage73R context-specific GRN control repair

## Control integrity audit

| graph_name | n_nodes | edge_count_directed_nnz | matrix_nnz | matrix_hash | diff_nnz_vs_context | fraction_changed_edges_vs_context | node_coverage_fraction | degree_correlation_with_context | weighted_adjacency_correlation_with_context | distinct_from_context |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| context_grn_aux | 64 | 1082 | 1082 | 375f61871cce3aec50ddecb993f0732cad021939b9abb8a6898b33f9d8342dfb | 0 | 0 | 0.8125 | 1 | 1 | False |
| target_shuffled_grn_aux | 64 | 758 | 758 | a4bd05211b4d288c48e0d6a20289263949e174b819db92c0836219729021faad | 1196 | 0.461538 | 0.8125 | 1 | 0.488761 | True |
| gene_label_permuted_grn_aux | 64 | 1082 | 1082 | e25d6abab34b936c5ce4efad0b903ab61e59452900e910915905743b73e02945 | 1858 | 0.835307 | 0.8125 | -0.128205 | 0.00687729 | True |
| string_graph_aux | 64 | 270 | 270 | a9c34259503c534c849637aca0f9147ce68322257a31535489c02f7a5d254e0e | 1298 | 0.958398 | 0.71875 | 0.0556484 | -0.0459123 | True |
| no_graph_raw | 64 | 0 | 0 | 1d94e50ec3e9eeb03af2edb22dc6b77db037695debcc8a1e935f11a59f2d5d77 | 1082 | 1 | 0 |  |  | True |

## Prediction lock decision

| context_graph_mean | no_graph_mean | string_graph_mean | target_shuffled_mean | gene_label_permuted_mean | beats_stage27c_mean | beats_no_graph_mean | beats_string_mean | beats_target_shuffled_mean | beats_gene_label_permuted_mean | bootstrap_vs_no_graph_positive | bootstrap_vs_all_graph_controls_positive | beats_stage41c_descriptive | context_graph_prediction_lock |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.323611 | 0.311254 | 0.331809 | 0.33229 | 0.313402 | False | True | False | False | True | True | False | False | False |

## Seed summary

| condition | mean_score | median_score | min_score | max_score |
| --- | --- | --- | --- | --- |
| target_shuffled_grn_aux | 0.33229 | 0.333263 | 0.32475 | 0.337086 |
| string_graph_aux | 0.331809 | 0.33726 | 0.320482 | 0.340002 |
| context_grn_aux | 0.323611 | 0.33168 | 0.294146 | 0.336187 |
| gene_label_permuted_grn_aux | 0.313402 | 0.315359 | 0.297989 | 0.327869 |
| no_graph_raw | 0.311254 | 0.311795 | 0.29705 | 0.332712 |

## Bootstrap deltas

| comparison | mean_delta | ci_lower_2p5 | ci_upper_97p5 | bootstrap_iterations | bootstrap_level |
| --- | --- | --- | --- | --- | --- |
| context_grn_vs_stage27c | -0.00269643 | -0.017543 | 0.00812311 | 1000 | seed_summary |
| context_grn_vs_no_graph | 0.0126242 | 0.00136722 | 0.0220925 | 1000 | seed_summary |
| context_grn_vs_string | -0.00779656 | -0.0256781 | 0.00556039 | 1000 | seed_summary |
| context_grn_vs_target_shuffled | -0.0083663 | -0.019597 | 0.000169282 | 1000 | seed_summary |
| context_grn_vs_gene_label_permuted | 0.0104236 | 0.000690898 | 0.0184161 | 1000 | seed_summary |

## Claim boundary

| stage73_internal_graph_prior_diagnostic_only | uses_frozen_stage72b_edges | uses_frozen_stage64_68_signature | no_graph_threshold_tuning | no_new_candidate_selection | no_model_architecture_search | no_external_validation_claim | no_causal_claim | no_therapeutic_claim | no_gene_ablation_claim | no_validated_grn_claim | raw_data_not_committed | safety_audit_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| True | True | True | True | True | True | True | True | True | True | True | True | True |
