# Scientific Pitch

## One-Liner

We are building a Graph-JEPA system that learns Alzheimer disease microglial state spaces from SEA-AD and uses pathology-grounded prediction plus model-implied counterfactuals to rank gene-network hypotheses.

## The Problem

Single-cell Alzheimer atlases are rich, but interpretation often stops at:

```text
clusters -> marker genes -> enrichment table
```

That is not enough. A disease discovery system needs to connect molecular state to measured tissue pathology.

The missing link is:

```text
cell-state program <-> pathology burden <-> testable mechanism
```

## The Bet

If a learned microglial state consistently predicts AT8/pTau, A beta/6e10, GFAP, Iba1, or NeuN pathology across held-out donors, then that state is more useful than a pathology-agnostic cluster or gene list.

If the model can then identify which genes/modules it relies on for that prediction, it becomes a hypothesis generator.

## What We Learned From v1

The first version used flat-vector JEPA over Microglia-PVM expression.

It worked well enough to be useful:

```text
pooled donor-held-out AT8 Spearman
  pathology-aware EMA+variance JEPA: ~= 0.497
  pseudobulk ridge:                  ~= 0.422
```

It also exposed important failure modes:

- genes were treated as unrelated columns
- random masking was weaker than biology-aware module masking
- longer training could compress useful disease variation
- elastic disease fine-tuning could escape into a narrow latent tube
- external perturbation alignment was weak for specific microglial regulators

That is exactly why v2 exists.

## Why Graph-JEPA v2 Is Different

v2 turns the cell into a graph instead of a flat vector.

```text
gene expression vector
        -> v1 flat JEPA

gene graph with expression + gene identity
        -> v2 Graph-JEPA
```

Each gene is a node. STRING relationships provide edges. Each node receives both an expression value and a learnable gene identity embedding.

This directly addresses a core biological issue: perturbing a microglial regulator should affect connected network neighborhoods, not just one independent column.

## The Training Curriculum

v2 uses a three-stage curriculum:

```text
Stage A: CELLxGENE normal microglia
  learn broad healthy/reference graph biology

Stage B: SEA-AD low-pathology Microglia-PVM
  calibrate to aged postmortem SEA-AD context

Stage C: full SEA-AD Microglia-PVM disease manifold
  learn pathology-relevant movement with anchor rehearsal
```

The curriculum is not purely sequential. Stage C uses rehearsal so the model does not forget healthy/reference anchors while learning disease movement.

## Current v2 Result

The first Stage C run over-pinned the anchors. It preserved reference geometry beautifully, but the disease manifold could not breathe.

The next elastic run let disease cells move, but telemetry showed a narrow tube:

```text
effective dimensions: about 2.10
top singular value ratio: about 0.821
```

A targeted sweep found a better setting:

```text
best run: fine_loose_01_r005_cov0005
checkpoint: epoch 5
rehearsal weight: 0.005
disease covariance weight: 0.0005
composite score: 1.544
```

Key readouts:

```text
AT8 ridge Spearman:          0.356
NeuN ridge Spearman:         0.374
AT8 cosine kNN Spearman:     0.227
NeuN cosine kNN Spearman:    0.258
effective dimensions:        4.76
top singular value ratio:    0.481
SEA anchor cosine:           0.956
CELLxGENE anchor cosine:     0.952
```

Interpretation: the current best model is not the most tightly anchored model. It is the most useful elastic compromise found so far.

## Why This Matters

This project is not claiming that Graph-JEPA already proves causal biology. The value is more precise:

```text
It builds a pathology-grounded state space.
It measures when that space is predictive.
It detects representation failure modes.
It ranks genes/modules for follow-up.
It creates a disciplined bridge to perturbation, spatial, and imaging validation.
```

## Current Hypothesis Shape

Example output:

```text
Hypothesis:
  A Microglia-PVM state involving homeostatic loss, lysosomal/phagocytic activation,
  and vascular/barrier myeloid biology is linked to tau pathology and neuronal-density changes.

Evidence:
  - The learned representation predicts AT8 and NeuN readouts.
  - Candidate genes include P2RY12, CX3CR1, F13A1, CHI3L1, CTSD, and PTPRG.
  - Module-level screens implicate homeostatic, vascular/barrier, complement, lipid,
    and lysosomal/phagocytic programs.

Validation:
  - Test spatial enrichment near AT8-positive tissue.
  - Compare to Iba1/GFAP/6e10 pathology fields.
  - Benchmark against microglia perturbation datasets.
```

## Evidence Discipline

We do not claim causality from observational SEA-AD data.

Evidence levels are explicit:

```text
association -> held-out prediction -> model-implied counterfactual -> external perturbation support -> experimental validation
```

That discipline is a core feature of the project.
