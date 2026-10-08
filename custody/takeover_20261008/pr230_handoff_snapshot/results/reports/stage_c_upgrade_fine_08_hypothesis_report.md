# Microglia-PVM Hypothesis Report

This report summarizes the selected v2.1 Graph-JEPA donor-level embedding model:

```text
run: upgrade_fine_08_r0045_cov0005_pc0075
checkpoint: epoch 5
architecture: projection-head Graph-JEPA + pathology-neighborhood loss
```

The results are predictive associations, not causal claims.

## Top Pathology Targets

- `percent NeuN positive area_Grey matter`: Spearman=0.426, R2=0.151, donors=84
- `number of NeuN positive cells per area_Grey matter`: Spearman=0.373, R2=0.105, donors=84
- `number of AT8 positive cells per area_Grey matter`: Spearman=0.319, R2=0.146, donors=84
- `percent GFAP positive area_Grey matter`: Spearman=0.295, R2=0.064, donors=84
- `ripa tTau_Grey matter`: Spearman=0.253, R2=-0.009, donors=84

## Initial Biological Interpretation

High-performing pathology targets should be followed by gene-level association analysis.
For Microglia-PVM, the first gene modules to inspect are plaque-response, complement/inflammation, interferon activation, and lipid metabolism.

## Top v2.1 Latent Factors

Latent factor weights were extracted with donor-held-out ridge models from:

```text
results/tables/stage_c_upgrade_fine_08_pathology_latent_weights.csv
```

Top AT8/pTau-associated dimensions:

- `z_120`: negative AT8 coefficient
- `z_26`: positive AT8 coefficient
- `z_30`: negative AT8 coefficient
- `z_94`: positive AT8 coefficient
- `z_71`: negative AT8 coefficient

Top NeuN-associated dimensions:

- `z_1`: positive NeuN coefficient
- `z_57`: negative NeuN coefficient
- `z_103`: negative NeuN coefficient
- `z_100`: positive NeuN coefficient
- `z_125`: negative NeuN coefficient

Top GFAP-associated dimensions:

- `z_63`: negative GFAP coefficient
- `z_38`: positive GFAP coefficient
- `z_120`: negative GFAP coefficient
- `z_107`: positive GFAP coefficient
- `z_71`: negative GFAP coefficient

Interpretation: the v2.1 model no longer concentrates the whole story into the old v1 `jepa_63` axis. AT8, NeuN, and GFAP now use partially overlapping but distinct latent dimensions, which is consistent with a more distributed disease manifold.

## Evidence Levels

- Association: pseudobulk expression correlates with donor-level pathology.
- Predictive: target is predicted in held-out donor folds.
- Regulatory candidate: requires gene/module ranking and enrichment.
- Validated: requires external spatial, IHC/IF, perturbational, or literature evidence.
