# Stage C Fine-Tuning Analysis

This report uses the current Stage C fine-tuning sweep as the active v2 baseline. It is generated from:

```text
results\tables\stage_c_finetuning_combined_leaderboard.csv
```

## Current Best Configuration

```text
run: upgrade_fine_08_r0045_cov0005_pc0075
checkpoint epoch: 5
SEA/CELLxGENE rehearsal weight: 0.0045
disease covariance weight: 0.0005
composite score: 1.686
```

Key readouts:

```text
AT8 ridge Spearman:          0.213
NeuN ridge Spearman:         0.426
AT8 cosine kNN Spearman:     0.266
NeuN cosine kNN Spearman:    0.303
GFAP cosine kNN Spearman:    0.408
Iba1 cosine kNN Spearman:    0.001
effective dimensions:        7.193
top singular value ratio:    0.430
SEA anchor cosine:           0.975
CELLxGENE anchor cosine:     0.961
```

Interpretation: the best run is anchor-safe by the current 0.95 cosine rule. It keeps both reference anchors comfortably above the safety boundary while allowing more disease movement than the earlier over-pinned Stage C runs.

![Stage C fine-tuning diagnostics](../results/figures/public_stage_c_finetuning_parameter_sensitivity.svg)

**Figure legend:** The diagnostics summarize which Stage C parameter settings worked best. The current performance leader uses low rehearsal weight and a very small disease covariance penalty. This supports the idea that the disease manifold needs room to move, while the anchor cosines provide a safety check against catastrophic forgetting.

## Top Fine-Tuned Runs

| rank | run | epoch | rehearsal | covariance | composite | AT8 ridge | NeuN ridge | AT8 cosine kNN | anchor cosines |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | upgrade_fine_08_r0045_cov0005_pc0075 | 5 | 0.0045 | 0.0005 | 1.686 | 0.213 | 0.426 | 0.266 | 0.975 / 0.961 |
| 2 | fine_bridge_06_r0045_cov0005 | 5 | 0.0045 | 0.0005 | 1.660 | 0.390 | 0.336 | 0.299 | 0.954 / 0.949 |
| 3 | upgrade_fine_02_r004_cov0005_pc005 | 5 | 0.0040 | 0.0005 | 1.651 | 0.272 | 0.434 | 0.289 | 0.973 / 0.959 |
| 4 | upgrade_02_projector_pathology | 5 | 0.0045 | 0.0005 | 1.634 | 0.265 | 0.428 | 0.277 | 0.975 / 0.961 |
| 5 | upgrade_fine_07_r0045_cov0005_pc0025 | 5 | 0.0045 | 0.0005 | 1.633 | 0.294 | 0.454 | 0.262 | 0.974 / 0.961 |
| 6 | fine_bridge_02_r0035_cov0005 | 5 | 0.0035 | 0.0005 | 1.620 | 0.404 | 0.361 | 0.370 | 0.948 / 0.944 |
| 7 | upgrade_fine_04_r0045_cov0005_pc005 | 5 | 0.0045 | 0.0005 | 1.613 | 0.282 | 0.427 | 0.263 | 0.975 / 0.961 |
| 8 | upgrade_fine_06_r005_cov0005_pc005 | 5 | 0.0050 | 0.0005 | 1.607 | 0.254 | 0.423 | 0.273 | 0.976 / 0.963 |

## Parameter Takeaways

- The best current regime is not the tightest anchor regime. Earlier runs with anchor cosines near 0.999 preserved the reference space too strongly and limited disease geometry.
- Very loose rehearsal can help, but the anchor safety boundary still matters. The current winner sits just above the 0.95 cosine floor for both SEA-AD and CELLxGENE anchors.
- A small covariance penalty helps reduce the narrow disease-tube failure mode without fully over-damping the disease manifold.
- Cosine kNN is more informative than Euclidean kNN in the current 128D space, suggesting that disease direction/profile is more stable than raw Euclidean neighborhood distance.

## Current Default for Next Runs

Use the current performance leader for exploratory downstream analyses:

```text
--weight-sea 0.0045
--weight-cx 0.0045
--disease-cov-weight 0.0005
--epochs 5
```

This is also the best strict anchor-safe setting under the 0.95 cosine rule:

```text
run: upgrade_fine_08_r0045_cov0005_pc0075
--weight-sea 0.0045
--weight-cx 0.0045
--disease-cov-weight 0.0005
--epochs 5
```

Recommended next diagnostic:

```text
Use upgrade_fine_08 for module/gene attribution and counterfactual screens,
then compare its biological hypotheses against fine_bridge_06 where AT8 ridge performance is important.
```

## Evidence Boundary

These are fine-tuning diagnostics, not biological causal validation. The best checkpoint should be treated as the current representation baseline for downstream hypothesis generation and external validation.
