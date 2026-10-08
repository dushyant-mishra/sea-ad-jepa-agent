# Discovery Baseline Comparison Gate

## Gate conclusion

Graph-JEPA remains a useful hypothesis-generation framework, but superiority over simpler baselines was not established.

## Predictive representation comparison

All tested representations use identical donor-level five-fold splits and a ridge readout. PCA is fit within each training fold. Cells are never split across train/test because the modeling unit is donor.

| representation | target | n_donors | r2_mean | oof_pearson | oof_spearman | mae_mean | rmse_mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| graph_jepa_real_graph_latent | percent AT8 positive area_Grey matter | 84 | 0.18334 | 0.48029 | 0.4583 | 1.0163 | 1.2789 |
| graph_jepa_real_graph_latent | percent 6e10 positive area_Grey matter | 84 | -0.65251 | 0.096037 | 0.18222 | 2.1797 | 2.8646 |
| graph_jepa_real_graph_latent | percent GFAP positive area_Grey matter | 84 | -0.18943 | 0.1578 | 0.18621 | 3.6739 | 4.6878 |
| graph_jepa_real_graph_latent | percent Iba1 positive area_Grey matter | 84 | -0.17151 | 0.10818 | 0.12745 | 1.6963 | 2.2123 |
| graph_jepa_real_graph_latent | percent NeuN positive area_Grey matter | 84 | 0.096185 | 0.43112 | 0.49278 | 1.3819 | 1.6925 |
| pca_expression_baseline | percent AT8 positive area_Grey matter | 84 | 0.16954 | 0.54916 | 0.39874 | 0.95463 | 1.2598 |
| pca_expression_baseline | percent 6e10 positive area_Grey matter | 84 | -1.0219 | 0.22306 | 0.30888 | 2.3355 | 3.0006 |
| pca_expression_baseline | percent GFAP positive area_Grey matter | 84 | -0.35045 | 0.16892 | 0.16355 | 3.8395 | 4.9572 |
| pca_expression_baseline | percent Iba1 positive area_Grey matter | 84 | -0.30103 | 0.11044 | 0.1558 | 1.814 | 2.3228 |
| pca_expression_baseline | percent NeuN positive area_Grey matter | 84 | 0.020844 | 0.37924 | 0.39488 | 1.4573 | 1.7774 |
| module_mean_baseline | percent AT8 positive area_Grey matter | 84 | 0.4369 | 0.69999 | 0.49015 | 0.81924 | 1.0261 |
| module_mean_baseline | percent 6e10 positive area_Grey matter | 84 | -0.57658 | 0.19405 | 0.32249 | 2.1448 | 2.7782 |
| module_mean_baseline | percent GFAP positive area_Grey matter | 84 | -0.095589 | 0.21971 | 0.22375 | 3.4459 | 4.5013 |
| module_mean_baseline | percent Iba1 positive area_Grey matter | 84 | -0.29212 | 0.013402 | 0.062043 | 1.7441 | 2.2946 |
| module_mean_baseline | percent NeuN positive area_Grey matter | 84 | 0.043258 | 0.3632 | 0.40099 | 1.4238 | 1.7712 |
| raw_expression_regularized_baseline | percent AT8 positive area_Grey matter | 84 | 0.1921 | 0.55236 | 0.40413 | 0.94481 | 1.245 |
| raw_expression_regularized_baseline | percent 6e10 positive area_Grey matter | 84 | -0.93258 | 0.21814 | 0.31252 | 2.2911 | 2.9541 |
| raw_expression_regularized_baseline | percent GFAP positive area_Grey matter | 84 | -0.30882 | 0.17241 | 0.16147 | 3.7903 | 4.8904 |
| raw_expression_regularized_baseline | percent Iba1 positive area_Grey matter | 84 | -0.26916 | 0.11034 | 0.14764 | 1.7807 | 2.2961 |
| raw_expression_regularized_baseline | percent NeuN positive area_Grey matter | 84 | 0.042457 | 0.38838 | 0.4079 | 1.4436 | 1.7585 |

Mean out-of-fold Spearman across pathology targets:

- `module_mean_baseline`: 0.2999
- `graph_jepa_real_graph_latent`: 0.2894
- `raw_expression_regularized_baseline`: 0.2867
- `pca_expression_baseline`: 0.2844

## Discovery ranking calibration

| ranking_method | top_k | overlap_promoted_tier1 | overlap_broad_state_caution | overlap_prior_anchors | cleaner_vs_broad_separation_metric |
| --- | --- | --- | --- | --- | --- |
| graph_jepa_therapeutic_like_percentile | 20 | 2 | 5 | 1 | 96.263 |
| graph_jepa_therapeutic_like_percentile | 50 | 20 | 5 | 2 | 96.263 |
| gene_pathology_correlation | 20 | 0 | 0 | 1 | -2.5037 |
| gene_pathology_correlation | 50 | 0 | 0 | 1 | -2.5037 |
| high_vs_low_pathology_differential_expression | 20 | 0 | 0 | 1 | 3.5127 |
| high_vs_low_pathology_differential_expression | 50 | 0 | 0 | 1 | 3.5127 |
| graph_degree_hubness | 20 | 0 | 14 | 0 | -46.898 |
| graph_degree_hubness | 50 | 0 | 17 | 0 | -46.898 |
| module_membership_or_module_score | 20 | 1 | 2 | 9 | 0 |
| module_membership_or_module_score | 50 | 1 | 2 | 11 | 0 |
| random_baseline | 20 | 0 | 0 | 0 | 1.1584 |
| random_baseline | 50 | 0 | 0 | 0 | 1.1584 |

Cleaner/broad classes are derived from Graph-JEPA scorecard axes. This ranking analysis is calibration, not independent biological validation.

## Ablation artifacts found

- Real-graph Stage B Graph-JEPA: `results\models\v2_2_stage_b_adversarial\stage_b_adversarial.pt`

## Ablation artifacts requiring future training

- `shuffled_graph_jepa`: `not_available_existing_artifact`
- `no_graph_jepa`: `not_available_existing_artifact`
- `expression_only_autoencoder`: `not_available_existing_artifact`

No ablation model was trained for this gate.

## Boundaries

- Predictive comparison evaluates donor-level association, not causal discovery.
- Discovery-ranking comparison is not independent because the cleaner/broad labels originate from Graph-JEPA score axes.
- No result proves causal mechanism, druggability, spatial plaque proximity, or therapeutic efficacy.
