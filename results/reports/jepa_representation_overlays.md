# JEPA Representation Overlay Summary

This figure maps donor-level JEPA embeddings in one shared 2D UMAP coordinate system and overlays latent dimensions or pathology labels as colors.

The goal is visualization with guardrails: dominant UMAP axes are not automatically causal axes, and pathology-colored structure is not proof of perturbational causality.

## Panels

| Panel | What it shows | Quantitative note |
|---|---|---|
| `jepa_34` | jepa_34: dominant homeostatic / vascular axis | rank 1/128, R2=0.867 |
| `jepa_46` | jepa_46: complement / synapse-pruning axis | rank 2/128, R2=0.826 |
| `jepa_108` | jepa_108: homeostatic / synapse-pruning axis | rank 3/128, R2=0.779 |
| `jepa_63` | jepa_63: AT8-linked complement axis | rank 83/128, R2=0.263 |
| `percent AT8 positive area_Grey matter` | AT8 / pTau pathology | R2=0.079, rho_y=+0.281 |
| `percent NeuN positive area_Grey matter` | NeuN neuronal marker | R2=0.182, rho_y=-0.427 |

## Interpretation

- The visible JEPA UMAP is driven mainly by broad microglial state axes such as homeostatic, vascular/barrier, complement, and synapse-pruning programs.
- `jepa_63` is included as an AT8-linked complement/antigen-presentation/synapse-pruning hypothesis axis, but it is not the main UMAP-shaping axis.
- AT8 and NeuN overlays test whether observed pathology labels occupy coherent regions of the learned manifold; they should be interpreted together with the quantitative R2 and Spearman metrics.

Donors plotted: 89
