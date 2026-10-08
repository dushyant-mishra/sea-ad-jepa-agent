# Stage C v2.1 Upgrade Experiments

Last updated: 2026-06-07

## Question

Can we build a more flexible model than `fine_bridge_06` without losing the healthy and low-pathology anchors?

The three tested upgrades were:

1. Projection-head decoupling.
2. Pathology-aware neighborhood organization.
3. Pathway-specific elasticity.

## Implementation

Projection-head decoupling adds an optional trainable projection head after the Graph-JEPA encoder. The encoder can remain the anchor-preserving biological graph representation, while the projection space can stretch during disease fine-tuning.

Pathology-aware neighborhood organization adds a gentle donor-pathology similarity loss. It pulls cells from similar AT8/NeuN donor contexts toward similar latent directions, but does not add a hard repulsive contrastive objective.

Pathway-specific elasticity adds a latent-dimension policy file:

```text
results/tables/latent_elasticity_policy_v1.csv
```

The first policy uses module annotations from:

```text
results/tables/all_jepa_umap_variance_rankings.csv
```

It assigns stricter bungee margins to homeostatic dimensions and looser margins to reactive/pathology-linked dimensions.

## Five-Epoch Comparison

Summary table:

```text
results/tables/stage_c_upgrade_sweep_summary.csv
```

| Run | Main change | Composite | AT8 ridge | NeuN ridge | AT8 cosine kNN | NeuN cosine kNN | SEA anchor | CELLxGENE anchor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `upgrade_02_projector_pathology` | projector + pathology loss | 1.634 | 0.265 | 0.428 | 0.277 | 0.306 | 0.975 | 0.961 |
| `upgrade_01_projector` | projector only | 1.576 | 0.219 | 0.450 | 0.203 | 0.319 | 0.974 | 0.960 |
| `upgrade_03_projector_pathology_elasticity` | projector + pathology + elasticity | 1.516 | 0.226 | 0.418 | 0.247 | 0.313 | 0.977 | 0.964 |

## Interpretation

Projection-head decoupling works technically and gives the model much more anchor safety than `fine_bridge_06`.

The pathology-aware term improves the projector run overall. It raises AT8 cosine kNN and keeps NeuN neighborhood quality high while preserving both anchors above 0.95.

The first pathway-specific elasticity policy is not ready as a default. It preserves anchors well, but the current policy is too blunt and lowers the composite score. The idea remains biologically sensible, but it needs a better latent-to-module mapping or a lower weight before becoming part of the main model.

## Decision

The initial screen supported `upgrade_02_projector_pathology`, so we ran a focused v2.1 sweep:

```text
results/tables/stage_c_upgrade_fine_summary.csv
```

Best focused run:

| Run | Composite | AT8 ridge | NeuN ridge | AT8 cosine kNN | NeuN cosine kNN | GFAP cosine kNN | SEA anchor | CELLxGENE anchor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `upgrade_fine_08_r0045_cov0005_pc0075` | 1.686 | 0.213 | 0.426 | 0.266 | 0.303 | 0.408 | 0.975 | 0.961 |

This now replaces `fine_bridge_06` as the balanced active v2.1 baseline.

Important caveat: `fine_bridge_06` still has stronger AT8 ridge performance and remains an important comparator for AT8-heavy analyses. The v2.1 default is better when we require both anchor safety and balanced pathology-neighborhood behavior.

## Next Experiments

The next sweep should tune around `upgrade_fine_08` rather than return to the coarse search:

```text
rehearsal weights: 0.0040, 0.0045, 0.0050
disease covariance: 0.0005
pathology contrastive weight: 0.06, 0.075, 0.09
```

Keep pathway-specific elasticity off during that sweep. Reintroduce it only after we build a better policy from explicit latent-to-module attribution instead of coarse UMAP module annotations.
