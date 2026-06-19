# No-Graph Ablation Predictive Representation Comparison v1

## Evaluation setup

- Real-graph checkpoint: `results\models\v2_2_stage_b_adversarial\stage_b_adversarial.pt`
- No-graph checkpoint: `results\models\ablation_no_graph_stage_b_v1\stage_b_adversarial.pt`
- Real graph edge index: `results\tables\v2_graph_consensus_edge_index.csv`
- No-graph identity edge set: `results\tables\ablation_edge_sets\no_graph_identity_edges_v1.csv`
- Donor folds: identical five-fold shuffled KFold logic, seed `23`.
- Readout: fold-local StandardScaler followed by ridge regression with alpha 10 for both JEPA latents.
- Targets: AT8, 6e10 / Aβ, GFAP, Iba1, and NeuN.
- Simpler comparator rows are copied unchanged from the frozen baseline table.
- No model training occurred during this evaluation.

## Real graph vs no-graph mean performance

- `graph_jepa_real_graph_latent`: 0.2892 mean OOF Spearman
- `graph_jepa_no_graph_identity_latent`: 0.2514 mean OOF Spearman
- Real minus no-graph: 0.0378
- Small-difference threshold: 0.010
- Controlled conclusion: `real_graph_outperforms_no_graph`

All representation means:

- `module_mean_baseline`: 0.2999
- `graph_jepa_real_graph_latent`: 0.2892
- `raw_expression_regularized_baseline`: 0.2867
- `pca_expression_baseline`: 0.2844
- `graph_jepa_no_graph_identity_latent`: 0.2514

## Target-specific comparison

| target | graph_jepa_real_graph_latent | graph_jepa_no_graph_identity_latent | real_minus_no_graph_oof_spearman | target_specific_winner |
| --- | --- | --- | --- | --- |
| percent 6e10 positive area_Grey matter | 0.18222 | 0.14108 | 0.041146 | real_graph |
| percent AT8 positive area_Grey matter | 0.45726 | 0.41454 | 0.042726 | real_graph |
| percent GFAP positive area_Grey matter | 0.18621 | 0.14735 | 0.038858 | real_graph |
| percent Iba1 positive area_Grey matter | 0.12745 | 0.017009 | 0.11044 | real_graph |
| percent NeuN positive area_Grey matter | 0.49278 | 0.53678 | -0.044001 | no_graph_identity |

## Full predictive metrics

| representation | target | n_donors | r2_mean | oof_pearson | oof_spearman | mae_mean | rmse_mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| graph_jepa_real_graph_latent | percent AT8 positive area_Grey matter | 84 | 0.18323 | 0.48022 | 0.45726 | 1.0164 | 1.2789 |
| graph_jepa_real_graph_latent | percent 6e10 positive area_Grey matter | 84 | -0.65259 | 0.096007 | 0.18222 | 2.1797 | 2.8647 |
| graph_jepa_real_graph_latent | percent GFAP positive area_Grey matter | 84 | -0.18952 | 0.15771 | 0.18621 | 3.6741 | 4.6879 |
| graph_jepa_real_graph_latent | percent Iba1 positive area_Grey matter | 84 | -0.17149 | 0.10822 | 0.12745 | 1.6963 | 2.2122 |
| graph_jepa_real_graph_latent | percent NeuN positive area_Grey matter | 84 | 0.09622 | 0.43116 | 0.49278 | 1.3819 | 1.6924 |
| graph_jepa_no_graph_identity_latent | percent AT8 positive area_Grey matter | 84 | 0.17325 | 0.45182 | 0.41454 | 1.004 | 1.2892 |
| graph_jepa_no_graph_identity_latent | percent 6e10 positive area_Grey matter | 84 | -0.64933 | 0.019915 | 0.14108 | 2.2296 | 2.9154 |
| graph_jepa_no_graph_identity_latent | percent GFAP positive area_Grey matter | 84 | -0.18887 | 0.11794 | 0.14735 | 3.6707 | 4.6829 |
| graph_jepa_no_graph_identity_latent | percent Iba1 positive area_Grey matter | 84 | -0.30711 | -0.062178 | 0.017009 | 1.7928 | 2.3421 |
| graph_jepa_no_graph_identity_latent | percent NeuN positive area_Grey matter | 84 | 0.18883 | 0.50167 | 0.53678 | 1.34 | 1.6078 |
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

## Interpretation

This result isolates the predictive association contribution of informative graph propagation under the completed single-seed ablation. It does not yet test whether biological topology is superior to a degree-preserving shuffled graph.

## Boundary

- This is donor-level association, not a causal test.
- No evidence levels changed.
- No shuffled-graph result is available yet.
- No external validation was run.
- No claim is made about causality, druggability, spatial plaque proximity, or experimental therapeutic efficacy.
