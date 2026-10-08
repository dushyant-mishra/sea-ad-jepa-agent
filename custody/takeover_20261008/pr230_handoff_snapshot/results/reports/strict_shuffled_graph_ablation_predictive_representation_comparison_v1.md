# Strict-Shuffled Graph Ablation Predictive Representation Comparison v1

## Evaluation setup

- No model training was run.
- Donor folds: same five-fold shuffled KFold logic as the baseline gate, seed `23`.
- Readout: fold-local StandardScaler plus Ridge; JEPA latents use alpha 10.
- Targets: AT8, 6e10 / Aβ, GFAP, Iba1, and NeuN.
- Simple baseline rows are copied unchanged from the frozen baseline comparison table.

## Models/checkpoints evaluated

- Real graph: `results\models\v2_2_stage_b_adversarial\stage_b_adversarial.pt`
- Identity/no-graph: `results\models\ablation_no_graph_stage_b_v1\stage_b_adversarial.pt`
- Strict shuffled graph: `results\models\ablation_strict_shuffled_graph_stage_b_v1\stage_b_adversarial.pt`

## Edge definitions

- Real graph edges: `results\tables\v2_graph_consensus_edge_index.csv`
- Identity/no-graph edges: `results\tables\ablation_edge_sets\no_graph_identity_edges_v1.csv`
- Strict shuffled edges: `results\tables\ablation_edge_sets\strict_shuffled_graph_edges_v1.csv`
- Strict shuffled graph is degree-preserving with zero original-edge overlap.

## Mean OOF Spearman ranking

- `module_mean_baseline`: 0.2999
- `graph_jepa_real_graph_latent`: 0.2892
- `raw_expression_regularized_baseline`: 0.2867
- `pca_expression_baseline`: 0.2844
- `graph_jepa_no_graph_identity_latent`: 0.2514
- `graph_jepa_strict_shuffled_graph_latent`: 0.2470

## Target-specific winners

| target | target_specific_winner | target_specific_graph_winner | graph_jepa_real_graph_latent | graph_jepa_no_graph_identity_latent | graph_jepa_strict_shuffled_graph_latent | module_mean_baseline | pca_expression_baseline | raw_expression_regularized_baseline |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| percent 6e10 positive area_Grey matter | inconclusive_small_difference | inconclusive_small_difference | 0.18222 | 0.14108 | 0.17461 | 0.32249 | 0.30888 | 0.31252 |
| percent AT8 positive area_Grey matter | module_mean_baseline | graph_jepa_real_graph_latent | 0.45726 | 0.41454 | 0.35369 | 0.49015 | 0.39874 | 0.40413 |
| percent GFAP positive area_Grey matter | module_mean_baseline | graph_jepa_real_graph_latent | 0.18621 | 0.14735 | 0.13626 | 0.22375 | 0.16355 | 0.16147 |
| percent Iba1 positive area_Grey matter | inconclusive_small_difference | graph_jepa_real_graph_latent | 0.12745 | 0.017009 | 0.069394 | 0.062043 | 0.1558 | 0.14764 |
| percent NeuN positive area_Grey matter | graph_jepa_no_graph_identity_latent | graph_jepa_no_graph_identity_latent | 0.49278 | 0.53678 | 0.50116 | 0.40099 | 0.39488 | 0.4079 |

## Real graph vs no graph

- Mean delta: 0.0378
- Label: `real_graph_outperforms_no_graph`

## Real graph vs strict shuffled

- Mean delta: 0.0422
- Label: `real_graph_outperforms_strict_shuffled`

## Strict shuffled vs no graph

- Mean delta: -0.0043

## Baseline context

- Module mean minus real graph: 0.0107
- Module mean remains strongest absolute predictor: `True`
- PCA expression mean OOF Spearman: 0.2844
- Raw expression regularized mean OOF Spearman: 0.2867

## Controlled conclusion labels

- `real_graph_outperforms_no_graph`
- `real_graph_outperforms_strict_shuffled`
- `graph_specific_benefit_supported`
- `module_mean_remains_best_absolute_predictor`

## Full predictive metrics

| representation | target | n_donors | r2_mean | oof_pearson | oof_spearman | mae_mean | rmse_mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| graph_jepa_real_graph_latent | percent AT8 positive area_Grey matter | 84 | 0.1833 | 0.48025 | 0.45726 | 1.0164 | 1.2789 |
| graph_jepa_real_graph_latent | percent 6e10 positive area_Grey matter | 84 | -0.65245 | 0.09609 | 0.18222 | 2.1797 | 2.8646 |
| graph_jepa_real_graph_latent | percent GFAP positive area_Grey matter | 84 | -0.18949 | 0.15773 | 0.18621 | 3.674 | 4.6879 |
| graph_jepa_real_graph_latent | percent Iba1 positive area_Grey matter | 84 | -0.17138 | 0.1083 | 0.12745 | 1.6961 | 2.2121 |
| graph_jepa_real_graph_latent | percent NeuN positive area_Grey matter | 84 | 0.096174 | 0.4311 | 0.49278 | 1.3819 | 1.6925 |
| graph_jepa_no_graph_identity_latent | percent AT8 positive area_Grey matter | 84 | 0.17325 | 0.45182 | 0.41454 | 1.004 | 1.2892 |
| graph_jepa_no_graph_identity_latent | percent 6e10 positive area_Grey matter | 84 | -0.64933 | 0.019915 | 0.14108 | 2.2296 | 2.9154 |
| graph_jepa_no_graph_identity_latent | percent GFAP positive area_Grey matter | 84 | -0.18887 | 0.11794 | 0.14735 | 3.6707 | 4.6829 |
| graph_jepa_no_graph_identity_latent | percent Iba1 positive area_Grey matter | 84 | -0.30711 | -0.062178 | 0.017009 | 1.7928 | 2.3421 |
| graph_jepa_no_graph_identity_latent | percent NeuN positive area_Grey matter | 84 | 0.18883 | 0.50167 | 0.53678 | 1.34 | 1.6078 |
| graph_jepa_strict_shuffled_graph_latent | percent AT8 positive area_Grey matter | 84 | 0.094054 | 0.36301 | 0.35369 | 1.0214 | 1.3471 |
| graph_jepa_strict_shuffled_graph_latent | percent 6e10 positive area_Grey matter | 84 | -0.60135 | 0.069725 | 0.17461 | 2.1857 | 2.84 |
| graph_jepa_strict_shuffled_graph_latent | percent GFAP positive area_Grey matter | 84 | -0.14536 | 0.098272 | 0.13626 | 3.5832 | 4.6283 |
| graph_jepa_strict_shuffled_graph_latent | percent Iba1 positive area_Grey matter | 84 | -0.17746 | 0.062337 | 0.069394 | 1.6868 | 2.2207 |
| graph_jepa_strict_shuffled_graph_latent | percent NeuN positive area_Grey matter | 84 | 0.11531 | 0.44648 | 0.50116 | 1.3914 | 1.6771 |
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

## Interpretation boundaries

- Donor-level association only.
- No causal claims.
- No target validation.
- No external validation.
- No evidence level changes.
