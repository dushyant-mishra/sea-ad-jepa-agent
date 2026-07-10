# Stage71 full graph-JEPA hierarchical benchmark

## Lock decisions

| top5_jaccard_vs_stage68_ge_0p50 | candidate_cells_present_ge_70pct_donors | max_single_donor_contribution_le_10pct | effective_donor_count_ge_50pct | cross_region_core_concordance_ge_80pct | graph_real_beats_random_prediction | micro_pvm3_state_enrichment_present | core_concordance_rate | rare_cell_representation_lock |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| True | True | True | False | True | False | True | 1.0 | False |

| mean_beats_stage27c | bootstrap_delta_vs_stage27c_positive | bootstrap_delta_vs_no_aux_positive | bootstrap_delta_vs_random_graph_positive | no_target_decline_worse_than_0p05 | no_iba1_catastrophic_collapse | beats_stage41c_descriptive | real_graph_aux_mean | no_aux_mean | random_graph_mean | donor_prediction_lock | best_overall_internal_model_descriptive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| False | False | True | False | False | True | False | 0.31964199655765924 | 0.3112540245013668 | 0.3275399412777159 | False | False |

## Prediction seed summary

| condition | mean_score | median_score | min_score | max_score |
| --- | --- | --- | --- | --- |
| no_aux_raw | 0.3112540245013668 | 0.3117950794775742 | 0.2970497114508454 | 0.33271236205325505 |
| random_graph_aux | 0.3275399412777159 | 0.3290877796901893 | 0.3057527589348993 | 0.3553103168978435 |
| real_graph_aux | 0.31964199655765924 | 0.31738382099827883 | 0.3083365394350511 | 0.33969018932874356 |

## Bootstrap deltas

| comparison | mean_delta | ci_lower_2p5 | ci_upper_97p5 | bootstrap_iterations | bootstrap_level |
| --- | --- | --- | --- | --- | --- |
| real_graph_aux_vs_stage27c | -0.007304064797003167 | -0.01514062974587427 | 0.003671560190341151 | 1000 | seed_summary |
| real_graph_aux_vs_no_aux | 0.008431190037460762 | 0.005715905639364194 | 0.011292497721980377 | 1000 | seed_summary |
| real_graph_aux_vs_random_graph | -0.007725377341297959 | -0.014313657993317743 | 0.0005013668117849757 | 1000 | seed_summary |

## Representation audits

| dataset | top5_jaccard_vs_stage68 | n_model_top5 | n_stage68_high |
| --- | --- | --- | --- |
| DLPFC | 0.9455128205128205 | 2124 | 2125 |
| MTG | 0.8796992481203008 | 2000 | 2000 |

| n_high_tail_cells | n_contributing_donors | max_single_donor_contribution | effective_donor_count | candidate_cells_present_in_fraction_evaluable_donors |
| --- | --- | --- | --- | --- |
| 4125.0 | 86.0 | 0.07393939393939394 | 41.6662585490439 | 0.9662921348314607 |

## Claim boundary

| stage71_internal_hierarchical_benchmark_only | full_local_mtg_dlpfc_cells_used | frozen_stage64_68_signature | no_auxiliary_weight_search | no_graph_strength_search | no_gene_or_module_replacement | no_pathology_derived_rare_cell_threshold | no_target_specific_cell_selection | no_external_validation_claim | no_causal_claim | no_therapeutic_claim | no_gene_ablation_claim | no_new_microglia_subtype_claim | safety_audit_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| True | True | True | True | True | True | True | True | True | True | True | True | True | True |
