# Discovery Atlas Negative Controls

## Executive Summary

This report asks whether candidate scores and graph-neighborhood labels look stronger than simple matched nonsense. It is a falsification layer, not validation.

**Important scope limit:** pathology-axis scores currently exist only for the scored candidate/fingerprint table. Degree-matched decoys are therefore `score-available candidate-space` decoys, not genome-wide null controls. Stronger nulls require counterfactual scores for a larger gene universe or rerunning perturbations for degree/expression-matched decoy genes.

Negative-control status counts:

- `preliminary_support`: 14
- `not_testable_due_to_thin_null_pool`: 9
- `not_extreme_within_scored_candidate_space`: 7
- `requires_expanded_decoy_perturbations`: 2

## What Controls Were Run

- Score-available degree-matched decoys.
- Score-available degree plus broad-shift-magnitude matched decoys, used for summary percentiles and p-values when available.
- Shuffled pathology-axis labels for same-axis graph-neighborhood support.
- Fallback housekeeping genes and top-degree hub controls. These are descriptive unless the control gene also has fingerprint scores.

Null-pool interpretation:

- `<20` possible decoys: `not_testable`.
- `20-49` possible decoys: `thin_null_pool` and preliminary only.
- `50+` possible decoys: interpretable preliminary decoy control, still not genome-wide.

## Candidate-Level Interpretation

| candidate | pathology_axis_class | negative_control_status | observed_graph_coherence_status | label_shuffle_support | null_pool_size | null_pool_warning | discovery_sort_decoy_percentile | housekeeping_or_hub_warning |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| APOE | gliosis_inflating | not_extreme_within_scored_candidate_space | no_graph_enrichment | not_extreme_vs_shuffled_labels | 20 | thin_null_pool | 15.7 | False |
| APP | gliosis_inflating | preliminary_support | coherent_same_axis_neighborhood | survives_label_shuffle | 20 | thin_null_pool | 5.2 | False |
| BCL2 | gliosis_inflating | preliminary_support | candidate_enriched_neighborhood | not_extreme_vs_shuffled_labels | 22 | thin_null_pool | 28.8 | False |
| C1QA |  | not_testable_due_to_thin_null_pool | not_available | not_testable_missing_fingerprint |  |  |  | False |
| C1QB |  | not_testable_due_to_thin_null_pool | not_available | not_testable_missing_fingerprint |  |  |  | False |
| C1QC |  | not_testable_due_to_thin_null_pool | not_available | not_testable_missing_fingerprint |  |  |  | False |
| C3 |  | not_testable_due_to_thin_null_pool | not_available | not_testable_missing_fingerprint |  |  |  | False |
| CD4 | artifact_or_covariate_sensitive | requires_expanded_decoy_perturbations | no_graph_enrichment | not_extreme_vs_shuffled_labels | 21 | thin_null_pool | 91.5 | False |
| CD74 | gliosis_inflating | not_extreme_within_scored_candidate_space | no_graph_enrichment | not_extreme_vs_shuffled_labels | 20 | thin_null_pool | 53.2 | False |
| CHI3L1 | mixed_or_unclear | preliminary_support | no_scored_candidate_neighbors | not_testable_no_scored_neighbors | 23 | thin_null_pool | 69.2 | False |
| CSF1R | mixed_or_unclear | preliminary_support | candidate_enriched_neighborhood | not_extreme_vs_shuffled_labels | 21 | thin_null_pool | 57 | False |
| CTSD | amyloid_lowering_candidate | preliminary_support | no_graph_enrichment | not_extreme_vs_shuffled_labels | 21 | thin_null_pool | 95.3 | False |
| CX3CR1 | gliosis_inflating | preliminary_support | candidate_enriched_neighborhood | not_extreme_vs_shuffled_labels | 21 | thin_null_pool | 27.8 | False |
| DRAM1 | mixed_or_unclear | not_testable_due_to_thin_null_pool | not_in_graph_or_isolated | not_testable_no_scored_neighbors | 0 | not_testable |  | False |
| F13A1 | mixed_or_unclear | preliminary_support | no_scored_candidate_neighbors | not_testable_no_scored_neighbors | 23 | thin_null_pool | 78.8 | False |
| GRB2 | gliosis_inflating | not_extreme_within_scored_candidate_space | no_graph_enrichment | not_extreme_vs_shuffled_labels | 21 | thin_null_pool | 19.5 | False |
| HIF1A | amyloid_lowering_candidate | preliminary_support | coherent_same_axis_neighborhood | not_extreme_vs_shuffled_labels | 20 | thin_null_pool | 24.4 | False |
| HLA-DRA |  | not_testable_due_to_thin_null_pool | not_available | not_testable_missing_fingerprint |  |  |  | False |
| HSP90AA1 | amyloid_lowering_candidate | preliminary_support | coherent_same_axis_neighborhood | not_extreme_vs_shuffled_labels | 21 | thin_null_pool | 48.2 | False |
| MAPK1 | amyloid_lowering_candidate | preliminary_support | coherent_same_axis_neighborhood | not_extreme_vs_shuffled_labels | 22 | thin_null_pool | 40.6 | False |
| P2RY12 | gliosis_inflating | not_extreme_within_scored_candidate_space | no_graph_enrichment | not_extreme_vs_shuffled_labels | 21 | thin_null_pool | 24.1 | False |
| P2RY13 | amyloid_lowering_candidate | requires_expanded_decoy_perturbations | no_graph_enrichment | not_extreme_vs_shuffled_labels | 21 | thin_null_pool | 85.8 | False |
| PLCG2 | mixed_or_unclear | preliminary_support | coherent_same_axis_neighborhood | not_extreme_vs_shuffled_labels | 21 | thin_null_pool | 58.2 | False |
| PTPRG | dual_pathology_lowering_candidate | preliminary_support | no_scored_candidate_neighbors | not_testable_no_scored_neighbors | 21 | thin_null_pool | 100 | False |
| RHOA | neuron_risk | not_extreme_within_scored_candidate_space | no_graph_enrichment | not_extreme_vs_shuffled_labels | 21 | thin_null_pool | 8.3 | False |
| ROCK1 | amyloid_lowering_candidate | preliminary_support | coherent_same_axis_neighborhood | survives_label_shuffle | 20 | thin_null_pool | 73.3 | False |
| SPP1 |  | not_testable_due_to_thin_null_pool | not_available | not_testable_missing_fingerprint |  |  |  | False |
| STAT3 | gliosis_inflating | preliminary_support | candidate_enriched_neighborhood | not_extreme_vs_shuffled_labels | 21 | thin_null_pool | 0 | False |
| TLR2 | dual_pathology_lowering_candidate | not_extreme_within_scored_candidate_space | no_graph_enrichment | not_extreme_vs_shuffled_labels | 20 | thin_null_pool | 39.6 | False |
| TREM2 |  | not_testable_due_to_thin_null_pool | not_available | not_testable_missing_fingerprint |  |  |  | False |
| TYROBP |  | not_testable_due_to_thin_null_pool | not_available | not_testable_missing_fingerprint |  |  |  | False |
| UGCG | mixed_or_unclear | not_extreme_within_scored_candidate_space | no_scored_candidate_neighbors | not_testable_no_scored_neighbors | 21 | thin_null_pool | 63.6 | False |

## Degree-Matched Decoy Results

The table reports candidate-vs-null statistics for each score. Summary status uses the degree plus broad-shift-magnitude matched null when possible.

| candidate | score | degree | observed | null_pool_size | null_pool_scope | null_pool_warning | control_interpretation | degree_null_pool_size | degree_magnitude_null_pool_size | degree_null_mean | degree_null_sd | degree_z | degree_empirical_p | degree_percentile | degree_magnitude_null_mean | degree_magnitude_null_sd | degree_magnitude_z | degree_magnitude_empirical_p | degree_magnitude_percentile |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| APOE | therapeutic_like_score | 46 | -0.03474 | 20 | score_available_candidate_space_degree_and_broad_shift_matched | thin_null_pool | 20-49 score-available matched decoys; preliminary candidate-space falsification only | 20 | 20 | -0.01619 | 0.02097 | -0.8844 | 0.8332 | 16.7 | -0.01518 | 0.02082 | -0.9396 | 0.8432 | 15.7 |
| APOE | amyloid_selectivity_score | 46 | -0.04551 | 20 | score_available_candidate_space_degree_and_broad_shift_matched | thin_null_pool | 20-49 score-available matched decoys; preliminary candidate-space falsification only | 20 | 20 | -0.02909 | 0.0286 | -0.5741 | 0.7692 | 23.1 | -0.02709 | 0.02798 | -0.6581 | 0.8012 | 19.9 |
| APOE | tau_selectivity_score | 46 | -0.04551 | 20 | score_available_candidate_space_degree_and_broad_shift_matched | thin_null_pool | 20-49 score-available matched decoys; preliminary candidate-space falsification only | 20 | 20 | -0.03271 | 0.0281 | -0.4556 | 0.7283 | 27.2 | -0.03061 | 0.02762 | -0.5397 | 0.7532 | 24.7 |
| APOE | broad_shift_score | 46 | 0.01051 | 20 | score_available_candidate_space_degree_and_broad_shift_matched | thin_null_pool | 20-49 score-available matched decoys; preliminary candidate-space falsification only | 20 | 20 | 0.009954 | 0.007289 | 0.07619 | 0.7283 | 72.8 | 0.009353 | 0.007113 | 0.1626 | 0.7532 | 75.3 |
| APOE | gliosis_penalty | 46 | 0.03547 | 20 | score_available_candidate_space_degree_and_broad_shift_matched | thin_null_pool | 20-49 score-available matched decoys; preliminary candidate-space falsification only | 20 | 20 | 0.02667 | 0.02346 | 0.3749 | 0.7283 | 72.8 | 0.0248 | 0.02273 | 0.4696 | 0.7532 | 75.3 |
| APOE | discovery_sort_score | 46 | -0.03737 | 20 | score_available_candidate_space_degree_and_broad_shift_matched | thin_null_pool | 20-49 score-available matched decoys; preliminary candidate-space falsification only | 20 | 20 | -0.01868 | 0.02251 | -0.8303 | 0.8332 | 16.7 | -0.01752 | 0.0223 | -0.89 | 0.8432 | 15.7 |
| APP | therapeutic_like_score | 78 | -0.05557 | 20 | score_available_candidate_space_degree_and_broad_shift_matched | thin_null_pool | 20-49 score-available matched decoys; preliminary candidate-space falsification only | 20 | 20 | -0.01393 | 0.01864 | -2.234 | 0.952 | 4.8 | -0.01398 | 0.01894 | -2.196 | 0.9481 | 5.2 |
| APP | amyloid_selectivity_score | 78 | -0.0935 | 20 | score_available_candidate_space_degree_and_broad_shift_matched | thin_null_pool | 20-49 score-available matched decoys; preliminary candidate-space falsification only | 20 | 20 | -0.02503 | 0.0234 | -2.926 | 0.952 | 4.8 | -0.02479 | 0.02362 | -2.909 | 0.9481 | 5.2 |
| APP | tau_selectivity_score | 78 | -0.0959 | 20 | score_available_candidate_space_degree_and_broad_shift_matched | thin_null_pool | 20-49 score-available matched decoys; preliminary candidate-space falsification only | 20 | 20 | -0.02853 | 0.02302 | -2.926 | 0.952 | 4.8 | -0.02846 | 0.0232 | -2.907 | 0.9481 | 5.2 |
| APP | broad_shift_score | 78 | 0.02701 | 20 | score_available_candidate_space_degree_and_broad_shift_matched | thin_null_pool | 20-49 score-available matched decoys; preliminary candidate-space falsification only | 20 | 20 | 0.008678 | 0.005808 | 3.156 | 1 | 100 | 0.008658 | 0.005892 | 3.114 | 1 | 100 |
| APP | gliosis_penalty | 78 | 0.08183 | 20 | score_available_candidate_space_degree_and_broad_shift_matched | thin_null_pool | 20-49 score-available matched decoys; preliminary candidate-space falsification only | 20 | 20 | 0.02297 | 0.01865 | 3.157 | 1 | 100 | 0.02274 | 0.01874 | 3.153 | 1 | 100 |
| APP | discovery_sort_score | 78 | -0.06232 | 20 | score_available_candidate_space_degree_and_broad_shift_matched | thin_null_pool | 20-49 score-available matched decoys; preliminary candidate-space falsification only | 20 | 20 | -0.0161 | 0.01974 | -2.341 | 0.952 | 4.8 | -0.01614 | 0.02004 | -2.304 | 0.9481 | 5.2 |
| BCL2 | therapeutic_like_score | 160 | -0.02135 | 22 | score_available_candidate_space_degree_and_broad_shift_matched | thin_null_pool | 20-49 score-available matched decoys; preliminary candidate-space falsification only | 22 | 22 | -0.01544 | 0.0195 | -0.3033 | 0.7213 | 27.9 | -0.01641 | 0.0204 | -0.2419 | 0.7123 | 28.8 |
| BCL2 | amyloid_selectivity_score | 160 | -0.04358 | 22 | score_available_candidate_space_degree_and_broad_shift_matched | thin_null_pool | 20-49 score-available matched decoys; preliminary candidate-space falsification only | 22 | 22 | -0.02785 | 0.0258 | -0.6099 | 0.7692 | 23.1 | -0.0293 | 0.02743 | -0.5208 | 0.7542 | 24.6 |
| BCL2 | tau_selectivity_score | 160 | -0.04822 | 22 | score_available_candidate_space_degree_and_broad_shift_matched | thin_null_pool | 20-49 score-available matched decoys; preliminary candidate-space falsification only | 22 | 22 | -0.03156 | 0.02544 | -0.655 | 0.7682 | 23.2 | -0.03291 | 0.02697 | -0.5675 | 0.7612 | 23.9 |
| BCL2 | broad_shift_score | 160 | 0.01455 | 22 | score_available_candidate_space_degree_and_broad_shift_matched | thin_null_pool | 20-49 score-available matched decoys; preliminary candidate-space falsification only | 22 | 22 | 0.00957 | 0.006583 | 0.7571 | 0.8182 | 81.8 | 0.009887 | 0.006942 | 0.6722 | 0.8152 | 81.5 |
| BCL2 | gliosis_penalty | 160 | 0.04103 | 22 | score_available_candidate_space_degree_and_broad_shift_matched | thin_null_pool | 20-49 score-available matched decoys; preliminary candidate-space falsification only | 22 | 22 | 0.02563 | 0.02112 | 0.7291 | 0.8182 | 81.8 | 0.02681 | 0.02236 | 0.6361 | 0.8002 | 80 |
| BCL2 | discovery_sort_score | 160 | -0.02499 | 22 | score_available_candidate_space_degree_and_broad_shift_matched | thin_null_pool | 20-49 score-available matched decoys; preliminary candidate-space falsification only | 22 | 22 | -0.01783 | 0.02082 | -0.3439 | 0.7213 | 27.9 | -0.01889 | 0.02184 | -0.2795 | 0.7123 | 28.8 |
| CD4 | therapeutic_like_score | 89 | 0.007715 | 21 | score_available_candidate_space_degree_and_broad_shift_matched | thin_null_pool | 20-49 score-available matched decoys; preliminary candidate-space falsification only | 21 | 21 | -0.01713 | 0.01947 | 1.276 | 0.07892 | 92.2 | -0.01715 | 0.01931 | 1.287 | 0.08591 | 91.5 |
| CD4 | amyloid_selectivity_score | 89 | -0.009535 | 21 | score_available_candidate_space_degree_and_broad_shift_matched | thin_null_pool | 20-49 score-available matched decoys; preliminary candidate-space falsification only | 21 | 21 | -0.02962 | 0.02677 | 0.7502 | 0.2847 | 71.6 | -0.02916 | 0.02618 | 0.7495 | 0.2807 | 72 |

## Shuffled-Label Graph-Coherence Results

| candidate | observed_same_class_neighbors | observed_same_class_neighbor_fraction | n_scored_neighbors | shuffle_mean_same_class_neighbors | shuffle_sd_same_class_neighbors | shuffle_z | shuffle_empirical_p | label_shuffle_support | observed_graph_coherence_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| APOE | 2 | 0.5 | 4 | 0.79 | 0.8016 | 1.51 | 0.1808 | not_extreme_vs_shuffled_labels | no_graph_enrichment |
| APP | 4 | 0.6667 | 6 | 1.362 | 1.035 | 2.548 | 0.02298 | survives_label_shuffle | coherent_same_axis_neighborhood |
| BCL2 | 1 | 0.1667 | 6 | 1.194 | 0.9906 | -0.1958 | 0.7203 | not_extreme_vs_shuffled_labels | candidate_enriched_neighborhood |
| C1QA |  |  | 2 |  |  |  |  | not_testable_missing_fingerprint | not_available |
| C1QB |  |  | 2 |  |  |  |  | not_testable_missing_fingerprint | not_available |
| C1QC |  |  | 1 |  |  |  |  | not_testable_missing_fingerprint | not_available |
| C3 |  |  | 2 |  |  |  |  | not_testable_missing_fingerprint | not_available |
| CD4 | 0 | 0 | 6 | 1.317 | 1.039 | -1.268 | 1 | not_extreme_vs_shuffled_labels | no_graph_enrichment |
| CD74 | 1 | 1 | 1 | 0.206 | 0.4046 | 1.962 | 0.2068 | not_extreme_vs_shuffled_labels | no_graph_enrichment |
| CHI3L1 | 0 |  | 0 | 0 | 0 |  | 1 | not_testable_no_scored_neighbors | no_scored_candidate_neighbors |
| CSF1R | 1 | 0.1429 | 7 | 1.511 | 1.117 | -0.4576 | 0.7882 | not_extreme_vs_shuffled_labels | candidate_enriched_neighborhood |
| CTSD | 0 | 0 | 3 | 0.652 | 0.7412 | -0.8796 | 1 | not_extreme_vs_shuffled_labels | no_graph_enrichment |
| CX3CR1 | 1 | 0.25 | 4 | 0.886 | 0.8183 | 0.1393 | 0.6324 | not_extreme_vs_shuffled_labels | candidate_enriched_neighborhood |
| DRAM1 | 0 |  | 0 | 0 | 0 |  | 1 | not_testable_no_scored_neighbors | not_in_graph_or_isolated |
| F13A1 | 0 |  | 0 | 0 | 0 |  | 1 | not_testable_no_scored_neighbors | no_scored_candidate_neighbors |
| GRB2 | 2 | 0.3333 | 6 | 1.322 | 1.041 | 0.6514 | 0.4216 | not_extreme_vs_shuffled_labels | no_graph_enrichment |
| HIF1A | 3 | 0.6 | 5 | 1.079 | 0.9464 | 2.03 | 0.08292 | not_extreme_vs_shuffled_labels | coherent_same_axis_neighborhood |
| HLA-DRA |  |  | 2 |  |  |  |  | not_testable_missing_fingerprint | not_available |
| HSP90AA1 | 3 | 0.375 | 8 | 1.707 | 1.182 | 1.094 | 0.2747 | not_extreme_vs_shuffled_labels | coherent_same_axis_neighborhood |
| MAPK1 | 3 | 0.4286 | 7 | 1.504 | 1.135 | 1.318 | 0.1938 | not_extreme_vs_shuffled_labels | coherent_same_axis_neighborhood |
| P2RY12 | 0 | 0 | 2 | 0.439 | 0.6039 | -0.727 | 1 | not_extreme_vs_shuffled_labels | no_graph_enrichment |
| P2RY13 | 0 | 0 | 1 | 0.209 | 0.4068 | -0.5138 | 1 | not_extreme_vs_shuffled_labels | no_graph_enrichment |
| PLCG2 | 1 | 0.3333 | 3 | 0.627 | 0.7003 | 0.5327 | 0.5065 | not_extreme_vs_shuffled_labels | coherent_same_axis_neighborhood |
| PTPRG | 0 |  | 0 | 0 | 0 |  | 1 | not_testable_no_scored_neighbors | no_scored_candidate_neighbors |
| RHOA | 0 | 0 | 2 | 0.423 | 0.5731 | -0.7381 | 1 | not_extreme_vs_shuffled_labels | no_graph_enrichment |
| ROCK1 | 3 | 0.75 | 4 | 0.892 | 0.8655 | 2.436 | 0.03896 | survives_label_shuffle | coherent_same_axis_neighborhood |
| SPP1 |  |  | 0 |  |  |  |  | not_testable_missing_fingerprint | not_available |
| STAT3 | 3 | 0.3333 | 9 | 1.811 | 1.259 | 0.9445 | 0.3147 | not_extreme_vs_shuffled_labels | candidate_enriched_neighborhood |
| TLR2 | 0 | 0 | 4 | 0.852 | 0.8239 | -1.034 | 1 | not_extreme_vs_shuffled_labels | no_graph_enrichment |
| TREM2 |  |  | 6 |  |  |  |  | not_testable_missing_fingerprint | not_available |

## Housekeeping / High-Degree Hub Checks

| control_gene | control_type | degree | pathology_axis_class | pathology_axis_label_confidence | therapeutic_like_score | amyloid_selectivity_score | tau_selectivity_score | discovery_sort_score | appears_in_fingerprint_table |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ACTB | housekeeping_fallback | 130 |  |  |  |  |  |  | False |
| GAPDH | housekeeping_fallback | 80 |  |  |  |  |  |  | False |
| B2M | housekeeping_fallback | 34 |  |  |  |  |  |  | False |
| RPLP0 | housekeeping_fallback | 0 |  |  |  |  |  |  | False |
| RPL13A | housekeeping_fallback | 179 |  |  |  |  |  |  | False |
| RPS18 | housekeeping_fallback | 264 |  |  |  |  |  |  | False |
| HPRT1 | housekeeping_fallback | 0 |  |  |  |  |  |  | False |
| TBP | housekeeping_fallback | 0 |  |  |  |  |  |  | False |
| TUBB | housekeeping_fallback | 0 |  |  |  |  |  |  | False |
| EEF1A1 | housekeeping_fallback | 66 |  |  |  |  |  |  | False |
| BRAF | top_degree_hub | 692 |  |  |  |  |  |  | False |
| WAPL | top_degree_hub | 657 |  |  |  |  |  |  | False |
| DLG1 | top_degree_hub | 656 |  |  |  |  |  |  | False |
| SMG1 | top_degree_hub | 644 |  |  |  |  |  |  | False |
| PAFAH1B1 | top_degree_hub | 639 |  |  |  |  |  |  | False |
| ANKHD1 | top_degree_hub | 639 |  |  |  |  |  |  | False |
| RC3H1 | top_degree_hub | 623 |  |  |  |  |  |  | False |
| PHKB | top_degree_hub | 617 |  |  |  |  |  |  | False |
| PPP2R5E | top_degree_hub | 591 |  |  |  |  |  |  | False |
| TMEM131 | top_degree_hub | 550 |  |  |  |  |  |  | False |
| ERC1 | top_degree_hub | 534 |  |  |  |  |  |  | False |
| HELZ | top_degree_hub | 532 |  |  |  |  |  |  | False |
| XIAP | top_degree_hub | 486 |  |  |  |  |  |  | False |
| SFSWAP | top_degree_hub | 486 |  |  |  |  |  |  | False |
| HDAC8 | top_degree_hub | 481 |  |  |  |  |  |  | False |
| EXOC4 | top_degree_hub | 479 |  |  |  |  |  |  | False |
| AGO3 | top_degree_hub | 478 |  |  |  |  |  |  | False |
| WASL | top_degree_hub | 471 |  |  |  |  |  |  | False |
| PPIG | top_degree_hub | 466 |  |  |  |  |  |  | False |
| ZCCHC7 | top_degree_hub | 466 |  |  |  |  |  |  | False |

## Claim Boundary

These preliminary controls do not prove causality. They also do not prove a target is biologically irrelevant when it fails. They only test whether the current Discovery Atlas signal is stronger than simple matched expectations inside the score-available candidate space. Strong discovery-tier claims should wait until scorecard v2 and, ideally, expanded decoy perturbations.

## Next Steps

Build scorecard v2 by merging fingerprints, covariate audit, druggability, graph coherence, and negative controls into one candidate table.
