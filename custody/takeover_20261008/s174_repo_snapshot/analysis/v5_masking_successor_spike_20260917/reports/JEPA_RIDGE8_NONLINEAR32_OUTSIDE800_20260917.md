# RIDGE8 nonlinear outside-800 32-target check — 2026-09-17

**Status:** EXPLORATORY SUPPORTING EVIDENCE ONLY. NO MASKING AUTHORITY. TRAINING OFF.

This run tests whether the discovery-side RIDGE8 signal is limited to a linear/ridge attacker.

Design:
- 32 targets selected outcome-blind from outside the original 800-address nested target pool;
- 6,000-address visible universe;
- four source-stratified held-donor folds;
- identical base masks for TOP8 and RIDGE8;
- burden-preserving targeted swaps;
- HistGradientBoosting nonlinear attacker fit only on outer-training donors and evaluated only on held-out donors.

Results:
- RIDGE8 mean nonlinear shortcut-score drop: 0.007563
- RIDGE8 relative drop: 6.22%
- RIDGE8 positive target mean: 29/32
- RIDGE8 target-clustered 95% CI: [0.003711, 0.013552]

- TOP8 mean nonlinear shortcut-score drop: 0.005077
- TOP8 relative drop: 4.17%
- TOP8 positive target mean: 24/32
- TOP8 target-clustered 95% CI: [0.001872, 0.010354]

Paired RIDGE8 minus TOP8:
- mean advantage: 0.002486
- positive target mean: 20/32
- target-clustered 95% CI: [0.000726, 0.004316]

Interpretation:
RIDGE8's shortcut-suppression effect is not confined to the ridge attacker used to select/evaluate the earlier linear discovery runs. Its average advantage over TOP8 also remains positive under this nonlinear attacker, with target-clustered uncertainty above zero.

Scientific semantic boundary:
This remains an anti-shortcut diagnostic. The attacker predicts target expression only to test whether visible RNA exposes easy proxy information. The JEPA scientific target is the underlying biological/cellular state, including query-local state associated with the masked address. This result is not evidence of hidden-gene reconstruction success and is not evidence by itself of biological-state recovery.
