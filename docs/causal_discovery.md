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

1. Run fold-specific knockouts using models trained inside the donor-held-out validation folds.
2. Add single-gene screens for all genes in robust modules.
3. Compare predicted perturbation effects with public CRISPR or drug perturbation datasets.
4. Add latent Jacobian analysis to infer directed latent-state dependencies.
5. Add confounder-adjusted causal estimates using JEPA donor embeddings plus donor covariates.
