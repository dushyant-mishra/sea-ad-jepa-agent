# Stage54 state-specific microglia/PVM programming report

Stage54 tested whether within-state module activity adds signal beyond donor-average pseudobulk and Stage53 abundance-only heterogeneity. It used predeclared module genes and donor-linked Microglia/PVM `Supertype` labels from the local processed H5AD.

## Branch comparison

| model_variant | latent_dim | seed | mean_pooled_oof_spearman | delta_vs_stage27c_locked |
| --- | --- | --- | --- | --- |
| programming_plus_state_specific_module_programming | 8 | 107 | 0.3250906145590767 | -0.0016118254530728127 |
| programming_only_pca_jepa | 8 | 107 | 0.3182423812898653 | -0.00846005872228417 |
| negative_control_programming_plus_donor_shuffled_state_programming | 8 | 107 | 0.31447200566973776 | -0.012230434342411722 |
| state_specific_module_programming_only | 8 | 107 | 0.28798623063683304 | -0.038716209375316446 |

## Interpretation

- Programming-only best: `0.318242`
- State-specific module branch best: `0.287986`
- Programming plus state-specific module branch best: `0.325091`
- Stage27C locked benchmark remains `0.326702`.

These are internal donor-held-out frozen-probe results. They do not establish causality, therapeutic targets, new microglia types, external validation, or validated gene ablation.
