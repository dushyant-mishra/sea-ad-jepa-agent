# Stage56 target-gated state-programming ensemble report

Stage56 tested whether Stage55's near-miss can be converted into a legitimate target-aware improvement. For each outer fold and target, branch choice was made only by inner CV on training donors.

## Branch comparison

| model_variant | latent_dim | seed | mean_pooled_oof_spearman | delta_vs_stage27c_locked | delta_vs_stage55_best |
| --- | --- | --- | --- | --- | --- |
| nested_target_gated_programming_vs_state_module | 8 | 107 | 0.3225068340589248 | -0.0041956059532247125 | -0.0035233370456616564 |
| negative_control_nested_target_gated_programming_vs_shuffled_state_module | 8 | 107 | 0.32202895616077754 | -0.004673483851371951 | -0.004001214943808895 |

## Interpretation

- Best real nested gate: `0.322507`
- Best shuffled-control nested gate: `0.322029`
- Stage55 best: `0.326030`
- Stage27C locked benchmark: `0.326702`

This is an internal target-gated audit only. It does not establish external validation, causality, therapeutic targets, gene ablation, or new microglia subtype discovery.
