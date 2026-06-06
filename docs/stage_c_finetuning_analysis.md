# Stage C Fine-Tuning Analysis

This report uses the current Stage C fine-tuning sweep as the active v2 baseline. It is generated from:

```text
results\tables\stage_c_finetuning_combined_leaderboard.csv
```

## Current Best Configuration

```text
run: fine_loose_01_r005_cov0005
checkpoint epoch: 5
SEA/CELLxGENE rehearsal weight: 0.0050
disease covariance weight: 0.0005
composite score: 1.544
```

Key readouts:

```text
AT8 ridge Spearman:          0.356
NeuN ridge Spearman:         0.374
AT8 cosine kNN Spearman:     0.227
NeuN cosine kNN Spearman:    0.258
GFAP cosine kNN Spearman:    0.205
Iba1 cosine kNN Spearman:    0.034
effective dimensions:        4.760
top singular value ratio:    0.481
SEA anchor cosine:           0.956
CELLxGENE anchor cosine:     0.952
```

Interpretation: the best run is deliberately elastic. It keeps both anchors just above the 0.95 cosine safety boundary while allowing more disease movement than the earlier over-pinned Stage C runs.

![Stage C fine-tuning diagnostics](../results/figures/public_stage_c_finetuning_parameter_sensitivity.svg)

**Figure legend:** The diagnostics summarize which Stage C parameter settings worked best. The current leader uses low rehearsal weight and a very small disease covariance penalty. This supports the idea that the disease manifold needs room to move, while the anchor cosines prevent catastrophic forgetting.

## Top Fine-Tuned Runs

| rank | run | epoch | rehearsal | covariance | composite | AT8 ridge | NeuN ridge | AT8 cosine kNN | anchor cosines |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | fine_loose_01_r005_cov0005 | 5 | 0.0050 | 0.0005 | 1.544 | 0.356 | 0.374 | 0.227 | 0.956 / 0.952 |
| 2 | fine_loose_05_r020_cov001 | 5 | 0.0200 | 0.0010 | 1.515 | 0.278 | 0.427 | 0.209 | 0.974 / 0.970 |
| 3 | fine_loose_04_r010_cov002 | 5 | 0.0100 | 0.0020 | 1.448 | 0.240 | 0.459 | 0.120 | 0.963 / 0.961 |
| 4 | fine_loose_03_r010_cov0005 | 5 | 0.0100 | 0.0005 | 1.394 | 0.241 | 0.365 | 0.260 | 0.969 / 0.964 |
| 5 | sweep_05_tight_anchor | 5 | 0.1000 | 0.0010 | 1.389 | 0.339 | 0.438 | 0.017 | 0.987 / 0.985 |
| 6 | sweep_04_loose_anchor | 5 | 0.0100 | 0.0010 | 1.370 | 0.285 | 0.367 | 0.148 | 0.967 / 0.964 |
| 7 | sweep_04_loose_anchor | 10 | 0.0100 | 0.0010 | 1.368 | 0.301 | 0.348 | 0.125 | 0.972 / 0.962 |
| 8 | fine_02_r007_cov001 | 5 | 0.0750 | 0.0010 | 1.335 | 0.350 | 0.417 | 0.162 | 0.985 / 0.983 |

## Parameter Takeaways

- The best current regime is not the tightest anchor regime. Earlier runs with anchor cosines near 0.999 preserved the reference space too strongly and limited disease geometry.
- Very loose rehearsal can help, but the anchor safety boundary still matters. The current winner sits just above the 0.95 cosine floor for both SEA-AD and CELLxGENE anchors.
- A small covariance penalty helps reduce the narrow disease-tube failure mode without fully over-damping the disease manifold.
- Cosine kNN is more informative than Euclidean kNN in the current 128D space, suggesting that disease direction/profile is more stable than raw Euclidean neighborhood distance.

## Current Default for Next Runs

Use the current best setting as the next default unless a new sweep beats it:

```text
--weight-sea 0.005
--weight-cx 0.005
--disease-cov-weight 0.0005
--epochs 5
```

Recommended next diagnostic:

```text
Run a narrow sweep around rehearsal 0.003-0.008 and covariance 0.00025-0.00075,
then evaluate the best checkpoint with donor-held-out pathology prediction and module attribution.
```

## Evidence Boundary

These are fine-tuning diagnostics, not biological causal validation. The best checkpoint should be treated as the current representation baseline for downstream hypothesis generation and external validation.
