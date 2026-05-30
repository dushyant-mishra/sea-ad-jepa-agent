# Causal Discovery Plan

This project uses causal language carefully. The current SEA-AD models are trained on observational data, so in-silico perturbations are not proof of biological causality. They are **model-implied counterfactual effects**: hypotheses about which genes or modules the trained model relies on when predicting pathology.

## Evidence Levels

```text
Association
  a gene/module correlates with pathology

Prediction
  a feature predicts held-out donor pathology

Model-implied counterfactual
  perturbing a gene/module changes the frozen model's pathology prediction

External perturbation support
  an interventional dataset shows a matching transcriptomic or imaging response

Experimental validation
  wet-lab perturbation confirms the effect
```

## Strategy 1: In-Silico Knockouts

The first causal layer is implemented in:

```text
scripts/causal_in_silico_knockout.py
```

The script loads a trained JEPA pathology model, predicts baseline AT8 pathology, perturbs a gene module or individual gene, predicts AT8 again, and reports:

```text
delta = perturbed prediction - baseline prediction
```

Interpretation:

```text
negative delta
  replacing the module lowers predicted AT8
  the model treats that module as supporting higher AT8 prediction

positive delta
  replacing the module raises predicted AT8
  the model treats that module as suppressing predicted AT8 or as a resilience-associated signal

near-zero delta
  the model does not rely strongly on that module for AT8 prediction
```

## Intervention Types

The script supports three intervention modes:

```text
global_mean
  replace selected genes with their global mean expression
  safest default; less out-of-distribution than zeroing

donor_mean
  replace selected genes with each donor's own mean expression
  tests whether within-donor cell-state variation matters

zero
  set selected genes to zero
  useful as a stress test, but more out-of-distribution
```

## First AT8 Module Screen

Model:

```text
results/models/microglia_pvm_jepa_ema_expanded_at8_finetune/jepa_pathology_finetuned.pt
```

Input:

```text
data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad
```

Primary target:

```text
percent AT8 positive area_Grey matter
```

Global-mean module replacement ranked the largest model-implied effects as:

```text
module                         mean donor delta
at8_associated_first_pass       -0.0195
homeostatic_microglia           -0.0038
vascular_barrier_myeloid        -0.0036
complement                      +0.0035
antigen_presentation            +0.0030
inflammatory_signaling          -0.0028
```

The most robust negative-delta modules across intervention checks were:

```text
at8_associated_first_pass
inflammatory_signaling
```

These are candidate driver-like modules in the model's learned AT8 prediction function.

## First Gene-Level Follow-Up

Single-gene perturbations were run inside the top module hits. The strongest negative-delta genes under global-mean replacement included:

```text
PTPRG
CHI3L1
MRC1
CTSD
DRAM1
P2RY12
S100A4
MSR1
TNFRSF11B
NFKBIA
```

These are not causal claims. They are prioritized hypotheses for literature review, external perturbation benchmarking, and possible experimental validation.

## Next Causal Steps

## Strategy 2: Latent Jacobian Analysis

The second causal layer is implemented in:

```text
scripts/causal_latent_jacobian.py
```

This script examines the JEPA predictor directly. It asks:

```text
If latent state j changes slightly, how much does the predictor change latent state i?
```

Mathematically:

```text
J[i, j] = d predicted_target_latent_i / d context_latent_j
```

The script:

1. Samples cells from the AnnData pilot.
2. Encodes cells into JEPA context latents.
3. Computes the predictor Jacobian with PyTorch autograd.
4. Averages the Jacobian across cells.
5. Annotates latent dimensions by correlation with curated microglia module scores.
6. Exports the full matrix and top directed latent edges.

First run:

```text
checkpoint: results/models/microglia_pvm_jepa_ema_var_expanded_balanced_e40/gene_jepa_epoch_030.pt
sample: 2,048 Microglia-PVM cells
```

Outputs:

```text
results/tables/latent_jacobian_ema_var_e30_matrix.csv
results/tables/latent_jacobian_ema_var_e30_top_edges.csv
results/tables/latent_jacobian_ema_var_e30_module_annotations.csv
```

Top directed latent edges were enriched for module annotations involving:

```text
homeostatic microglia
lysosome/phagocytosis
vascular/barrier myeloid
complement
antigen presentation
synapse pruning
```

These edges are not gene-to-gene causal proof. They are directed sensitivities inside the learned JEPA latent transition function. They help prioritize which latent programs to map back to genes and test with perturbation evidence.

## Next Causal Steps

## Strategy 3: Confounder-Adjusted Donor Effects

The third causal layer is implemented in:

```text
scripts/causal_confounder_adjusted_effects.py
```

This script estimates donor-level gene or module effects after adjusting for:

```text
JEPA donor embeddings
Age at Death
Sex
APOE Genotype
```

It uses a residualization strategy:

```text
1. residualize outcome against confounders
2. residualize treatment against confounders
3. estimate association between residual treatment and residual outcome
```

This is a confounder-adjusted observational estimate, not causal proof. It asks whether a candidate gene or module still carries AT8 signal after accounting for donor-level latent state and major donor covariates.

First module-level AT8 result:

```text
treatment                     partial Spearman
at8_associated_first_pass      +0.441
lipid_metabolism               -0.314
vascular_barrier_myeloid       -0.282
complement                     -0.201
inflammatory_signaling         +0.198
```

First gene-level AT8 result for top knockout candidates:

```text
treatment     partial Spearman
CHI3L1         +0.416
PTPRG          +0.355
NFKBIA         +0.349
S100A4         +0.333
TNFRSF11B      +0.306
DRAM1          +0.281
```

Genes that appear in both the in-silico knockout screen and confounder-adjusted screen are stronger candidates for follow-up.

## Next Causal Steps

1. Run fold-specific knockouts using models trained inside the donor-held-out validation folds.
2. Add single-gene screens for all genes in robust modules.
3. Compare predicted perturbation effects with public CRISPR or drug perturbation datasets.
4. Map high-Jacobian latent dimensions back to genes/modules more deeply.
5. Add donor covariate sensitivity checks and alternative adjustment sets.
