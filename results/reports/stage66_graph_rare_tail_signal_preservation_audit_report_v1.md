# Stage66 graph rare-tail signal preservation audit

## Bottom line

Stage66 tests whether graph biology may have been present but diluted by broad graph smoothing. It is diagnostic only and does not run a new graph-JEPA rescue model.

## Graph input audit

| graph_edges | graph_nodes | mean_degree | hub_degree_cutoff | n_hubs | graph_source |
| --- | --- | --- | --- | --- | --- |
| 14565 | 2311 | 12.604932929467763 | 49.0 | 113 | results/tables/v2_graph_string_edges_t700.csv |

## Rare-signature graph proximity

| signature | n_genes | induced_edges | density | mean_pair_shortest_path | mean_degree | null_density_mean | observed_density | density_empirical_p | null_path_mean | observed_path | path_empirical_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dam_lipid_trem2_apoe | 8 | 8 | 0.2857142857142857 | 2.0357142857142856 | 22.625 | 0.012440476190476191 | 0.2857142857142857 | 0.0 | 3.2648214285714285 | 2.0357142857142856 | 0.0 |
| lysosomal_endolysosomal | 7 | 8 | 0.38095238095238093 | 1.9047619047619047 | 13.714285714285714 | 0.002476190476190476 | 0.38095238095238093 | 0.0 | 3.509404761904762 | 1.9047619047619047 | 0.0 |
| complement_phagocytosis | 5 | 9 | 0.9 | 1.1 | 20.8 | 0.008 | 0.9 | 0.0 | 3.187 | 1.1 | 0.0 |
| antigen_presentation | 6 | 15 | 1.0 | 1.0 | 30.166666666666668 | 0.014666666666666666 | 1.0 | 0.0 | 3.014 | 1.0 | 0.0 |
| interferon_inflammatory | 6 | 3 | 0.2 | 2.466666666666667 | 33.166666666666664 | 0.004 | 0.2 | 0.0 | 3.487 | 2.466666666666667 | 0.005 |
| oxidative_stress_gene_preserved | 7 | 11 | 0.5238095238095238 | 1.4761904761904763 | 16.571428571428573 | 0.009142857142857142 | 0.5238095238095238 | 0.0 | 3.276047619047619 | 1.4761904761904763 | 0.0 |
| all_stage64_rare_tail_signature_genes | 36 | 73 | 0.11587301587301588 | 2.5365079365079364 | 22.055555555555557 | 0.010042094501534728 | 0.11587301587301588 | 0.0 | 3.3260818679133433 | 2.5365079365079364 | 0.0 |

## Graph smoothing delta summary

| graph_variant | alpha | mean_abs_delta_vs_raw | fraction_preserved_or_improved | n_tests |
| --- | --- | --- | --- | --- |
| hub_capped | 0.05 | 0.003325795594938832 | 0.6527777777777778 | 360 |
| hub_capped | 0.1 | 0.005962824246546826 | 0.6833333333333333 | 360 |
| hub_capped | 0.25 | 0.014369565493707446 | 0.6861111111111111 | 360 |
| hub_capped | 0.5 | 0.030591024037210094 | 0.6611111111111111 | 360 |
| hub_capped | 1.0 | 0.004858594044840344 | 0.525 | 360 |
| hub_removed | 0.05 | -0.010520602430075571 | 0.5361111111111111 | 360 |
| hub_removed | 0.1 | -0.007914885874199694 | 0.5833333333333334 | 360 |
| hub_removed | 0.25 | 0.00033897886398845986 | 0.5888888888888889 | 360 |
| hub_removed | 0.5 | 0.013815657852952912 | 0.6111111111111112 | 360 |
| hub_removed | 1.0 | -0.007336745258852827 | 0.4638888888888889 | 360 |
| signature_subgraph | 0.05 | -0.012610932520206092 | 0.3611111111111111 | 360 |
| signature_subgraph | 0.1 | -0.012939773424937257 | 0.31666666666666665 | 360 |
| signature_subgraph | 0.25 | -0.01518520370228629 | 0.3111111111111111 | 360 |
| signature_subgraph | 0.5 | -0.022998760183411307 | 0.25833333333333336 | 360 |
| signature_subgraph | 1.0 | -0.03529972966231576 | 0.25555555555555554 | 360 |
| uncapped | 0.05 | 0.0035487230509275375 | 0.6805555555555556 | 360 |
| uncapped | 0.1 | 0.006673205662412646 | 0.7055555555555556 | 360 |
| uncapped | 0.25 | 0.016757427511780883 | 0.7166666666666667 | 360 |
| uncapped | 0.5 | 0.03373822616225132 | 0.6972222222222222 | 360 |
| uncapped | 1.0 | 0.019035117542707765 | 0.5361111111111111 | 360 |

## Hub-capping / graph variant summary

| graph_variant | alpha | mean_abs_delta_vs_raw | fraction_preserved_or_improved | n_tests |
| --- | --- | --- | --- | --- |
| hub_capped | 0.05 | 0.003325795594938832 | 0.6527777777777778 | 360 |
| hub_capped | 0.1 | 0.005962824246546826 | 0.6833333333333333 | 360 |
| hub_capped | 0.25 | 0.014369565493707446 | 0.6861111111111111 | 360 |
| hub_capped | 0.5 | 0.030591024037210094 | 0.6611111111111111 | 360 |
| hub_capped | 1.0 | 0.004858594044840344 | 0.525 | 360 |
| hub_removed | 0.05 | -0.010520602430075571 | 0.5361111111111111 | 360 |
| hub_removed | 0.1 | -0.007914885874199694 | 0.5833333333333334 | 360 |
| hub_removed | 0.25 | 0.00033897886398845986 | 0.5888888888888889 | 360 |
| hub_removed | 0.5 | 0.013815657852952912 | 0.6111111111111112 | 360 |
| hub_removed | 1.0 | -0.007336745258852827 | 0.4638888888888889 | 360 |
| signature_subgraph | 0.05 | -0.012610932520206092 | 0.3611111111111111 | 360 |
| signature_subgraph | 0.1 | -0.012939773424937257 | 0.31666666666666665 | 360 |
| signature_subgraph | 0.25 | -0.01518520370228629 | 0.3111111111111111 | 360 |
| signature_subgraph | 0.5 | -0.022998760183411307 | 0.25833333333333336 | 360 |
| signature_subgraph | 1.0 | -0.03529972966231576 | 0.25555555555555554 | 360 |
| uncapped | 0.05 | 0.0035487230509275375 | 0.6805555555555556 | 360 |
| uncapped | 0.1 | 0.006673205662412646 | 0.7055555555555556 | 360 |
| uncapped | 0.25 | 0.016757427511780883 | 0.7166666666666667 | 360 |
| uncapped | 0.5 | 0.03373822616225132 | 0.6972222222222222 | 360 |
| uncapped | 1.0 | 0.019035117542707765 | 0.5361111111111111 | 360 |

## Decision

| graph_contains_rare_tail_structure | graph_smoothing_washout_supported | weak_graph_preserves_better_than_strong_graph | hub_capping_test_completed | stage66_interpretation |
| --- | --- | --- | --- | --- |
| True | False | False | True | graph topology contains/organizes rare-tail genes, but fixed graph smoothing did not show a simple global washout pattern; prior graph-JEPA failure is not explained by smoothing alone |
