# Causal Discovery and Counterfactual Hypothesis Plan

This project uses causal language carefully. SEA-AD is observational postmortem data, so model perturbations are not proof of biological causality. They are **model-implied counterfactual hypotheses**.

The causal-discovery layer is useful because it asks:

```text
Which genes/modules does the trained model rely on when predicting pathology?
Which predicted effects survive donor-held-out or confounder-adjusted checks?
Which hypotheses are worth testing in external perturbation, spatial, or imaging data?
```

## Evidence Levels

```text
Association
  a gene/module correlates with pathology

Prediction
  a feature predicts held-out donor pathology

Model-implied counterfactual
  perturbing a gene/module changes a frozen model's prediction or latent state

External perturbation support
  an interventional dataset shows a matching transcriptomic or imaging response

Experimental validation
  wet-lab perturbation confirms the effect
```

## v1 Causal Layer: Flat-JEPA Hypothesis Generation

The first causal tools were built on the v1 flat-vector JEPA family.

Implemented:

```text
scripts/causal_in_silico_knockout.py
scripts/causal_fold_specific_knockout.py
scripts/causal_latent_jacobian.py
scripts/causal_confounder_adjusted_effects.py
```

These workflows produced useful SEA-AD hypotheses, but they inherit the v1 limitation: genes are treated as columns rather than graph-connected biological nodes.

## Digital Knockouts

Digital knockout workflow:

```text
baseline expression
        -> frozen model
        -> baseline prediction

perturbed expression
        -> frozen model
        -> counterfactual prediction

delta = perturbed prediction - baseline prediction
```

Intervention modes:

```text
global_mean
  replace selected genes with global mean expression
  conservative default

donor_mean
  replace selected genes with donor-specific mean expression
  tests within-donor cell-state variation

zero
  set selected genes to zero
  stress test, more out-of-distribution
```

Interpretation:

```text
negative delta
  model predicts lower pathology after perturbation

positive delta
  model predicts higher pathology after perturbation

near-zero delta
  model is not sensitive to that perturbation
```

These are model sensitivities, not biological causal effects.

## Fold-Specific Knockouts

The stricter leakage-resistant workflow:

```text
1. split donors with GroupKFold or StratifiedGroupKFold
2. train pathology head on training donors
3. run digital knockouts only on held-out donors
4. pool donor-level deltas across folds
```

This is more conservative than one all-data pathology model.

Key v1 pattern:

```text
at8_associated_first_pass
  negative under global_mean, donor_mean, and zero interventions

vascular_barrier_myeloid, complement, lipid_metabolism
  important to prediction
  direction depends on intervention type
```

## Latent Jacobian Analysis

The latent Jacobian asks how the JEPA predictor transforms one latent state into another.

```text
J[i, j] = d predicted_target_latent_i / d context_latent_j
```

It is implemented in:

```text
scripts/causal_latent_jacobian.py
```

It identifies directed sensitivities inside the learned latent transition function. These are not gene-to-gene causal edges, but they help prioritize latent programs for gene/module decoding.

Early annotations involved:

```text
homeostatic microglia
lysosome/phagocytosis
vascular/barrier myeloid
complement
antigen presentation
synapse pruning
```

## Confounder-Adjusted Effects

Confounder-adjusted donor-level estimates are implemented in:

```text
scripts/causal_confounder_adjusted_effects.py
```

Adjustment set:

```text
JEPA donor embeddings
Age at Death
Sex
APOE Genotype
```

This uses residualization:

```text
residualize treatment against confounders
residualize outcome against confounders
estimate association between residuals
```

This is still observational, but it asks whether a gene/module carries pathology signal beyond broad donor state and major covariates.

Candidate genes appearing in early screens:

```text
CHI3L1
PTPRG
NFKBIA
S100A4
TNFRSF11B
DRAM1
P2RY12
CX3CR1
F13A1
```

## Why v2 Matters for Causal Discovery

v1 can rank hypotheses, but it is not a true graph-aware perturbation model.

The core v1 limitation:

```text
gene perturbation = changing one column in a vector
```

The v2 goal:

```text
gene perturbation = changing a node in a graph and observing downstream subgraph/state movement
```

Graph-JEPA v2 is therefore the right place to continue causal-discovery work.

## v2 Counterfactual Plan

For Graph-JEPA, counterfactuals should operate at multiple levels.

### 1. Node-Level Perturbation

Perturb a gene node:

```text
set expression to mean
scale expression down for CRISPRi-like knockdown
zero expression for stress-test knockout
```

Measure:

```text
latent shift
pathology-head shift
subgraph activation shift
```

### 2. Module/Subgraph Perturbation

Perturb a full module or graph neighborhood:

```text
homeostatic microglia
complement
lysosome/phagocytosis
vascular/barrier myeloid
lipid metabolism
plaque response
```

This is more biologically realistic than single-gene perturbation when pathways are redundant.

### 3. Predictive-Mode Perturbation

Use the JEPA predictor, not just input erasure:

```text
masked/perturbed context graph
        -> context encoder
        -> predictor
        -> predicted downstream latent state
```

This tests whether JEPA's learned transition function contributes beyond local input sensitivity.

### 4. Donor-Held-Out Counterfactuals

Counterfactual effects should be evaluated on held-out donors:

```text
train or fit head on donor folds
run perturbations on held-out donors
pool effects across folds
```

## External Validation

External datasets are needed to move from model-implied hypotheses toward causal support.

Current benchmark status:

```text
K562/Replogle
  useful engineering smoke test
  not Alzheimer's microglia biology

Kampmann/iPSC-microglia DEG benchmark
  more biologically relevant
  not yet ideal for per-cell guide-level validation
```

Desired next benchmark:

```text
iPSC-microglia or macrophage Perturb-seq
with per-cell perturbation labels
and AD-relevant targets such as TREM2, APOE, CSF1R, CX3CR1, P2RY12, complement, lysosomal, and lipid genes
```

Independent observational validation is also useful:

```text
project external AD microglia into frozen Graph-JEPA
test whether candidate latent axes or modules track Braak/tau/AD labels
without retraining
```

## Current Evidence Boundary

Current outputs should be described as:

```text
pathology-grounded representation learning
model-implied counterfactual prioritization
candidate gene-network hypotheses
```

They should not be described as:

```text
validated causal drivers
therapeutic targets proven by the model
experimental perturbation results
```

That boundary is essential for scientific credibility.
