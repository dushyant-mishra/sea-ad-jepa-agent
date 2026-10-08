# Architecture

## Discovery Loop

The project is organized around a discovery loop:

```text
SEA-AD Microglia-PVM expression
        |
        v
cell-state representation learning
        |
        v
donor-held-out pathology prediction
        |
        v
gene/module interpretation
        |
        v
model-implied counterfactuals
        |
        v
evidence-aware biological hypotheses
```

The model is only one part of the system. The full architecture includes data access, representation learning, validation, counterfactual analysis, and reporting.

## Data Layer

Primary dataset:

```text
SEA-AD MTG single-nucleus RNA-seq
Microglia-PVM subset
40,000 nuclei x 2,957 genes in the current expanded-module pilot
```

Pathology targets:

```text
AT8 / pTau
6e10 / A beta
GFAP
Iba1
NeuN
biochemical amyloid/tau readouts
```

External/reference anchors:

```text
CELLxGENE normal-labeled human brain microglia nuclei
SEA-AD low-pathology Microglia-PVM nuclei
```

Graph prior:

```text
STRING t700 gene graph
2,957 genes
231,015 edge-index columns
```

## v1 Flat-JEPA Layer

The first architecture represented each cell as a flat gene-expression vector.

```text
expression vector
        -> context encoder
        -> predictor
        -> predicted target latent

masked target expression
        -> EMA target encoder
        -> target latent
```

v1 improvements:

- EMA target encoder
- curated module-aware masking
- donor-balanced sampling
- variance regularization
- pathology-aware fine-tuning
- donor-held-out pooled OOF validation

v1 limitations:

- no explicit gene graph
- weak perturbation dynamics for specific regulators
- possible disease-tube collapse during fine-tuning
- observational counterfactuals remain hypotheses

v1 remains useful as a baseline and hypothesis generator, but v2 is the main architecture direction.

## v2 Graph-JEPA Layer

Graph-JEPA represents each cell as a gene graph.

```text
node = gene
edge = STRING relationship
node feature = [expression scalar, learnable gene identity embedding]
graph encoder = message-passing model
cell latent = pooled graph representation
```

Why gene identity embeddings matter:

```text
expression-only scalar node
        -> graph layers can over-smooth and forget which gene is which

expression + gene identity vector
        -> graph layers know both abundance and biological node identity
```

The JEPA objective remains latent predictive learning:

```text
masked context graph
        -> context graph encoder
        -> predictor
        -> predicted target latent

target graph
        -> EMA target graph encoder
        -> target latent
```

## Stage A/B/C Curriculum

### Stage A: Healthy/Reference Pretraining

Input:

```text
CELLxGENE normal-labeled brain microglia nuclei
```

Goal:

```text
learn a broad healthy/reference microglial graph manifold
```

Current best Stage A checkpoint:

```text
results/models/graph_jepa_stage_a_string_t700_rawvar_e30/graph_jepa.pt
```

### Stage B: SEA-AD Calibration

Input:

```text
SEA-AD low-pathology Microglia-PVM nuclei
CELLxGENE rehearsal anchors
```

Goal:

```text
adapt to SEA-AD aged postmortem technical context
without forgetting the Stage A healthy/reference manifold
```

Drift audit:

```text
SEA-AD low-pathology cosine: 0.9916
CELLxGENE cosine:           0.9754
```

### Stage C: Disease-Vector Training

Input streams:

```text
full SEA-AD Microglia-PVM disease stream
SEA-AD low-pathology anchor stream
CELLxGENE normal microglia anchor stream
```

Goal:

```text
learn pathology-linked movement while preserving anchors
```

This is a rehearsal curriculum, not a purely sequential curriculum. The model sees disease and anchors in the same training phase so healthy/reference geometry is not overwritten.

## Stage C Losses

The Stage C objective combines:

```text
disease JEPA loss
anchor rehearsal loss
disease covariance penalty
```

Rehearsal uses a cosine softplus margin:

```text
margin: 0.95
temperature: 100
```

This acts like an elastic safety boundary. Anchors may move slightly, but the penalty rises when they drift below the cosine margin.

The disease covariance penalty is used to reduce narrow-tube collapse, where one latent axis carries most of the disease signal.

## Telemetry

Stage C logs:

```text
disease JEPA loss
SEA anchor cosine
CELLxGENE anchor cosine
disease-to-CELLxGENE centroid L2
disease variance spread
disease effective dimensionality
disease top singular value ratio
```

Why this matters:

```text
Ridge can succeed on a 1D disease tube.
kNN needs useful local neighborhood geometry.
Effective dimensions and top singular value ratio tell us whether the manifold is broad or collapsed.
```

## Current Best Stage C Configuration

From the combined sweep leaderboard:

```text
run: upgrade_fine_08_r0045_cov0005_pc0075
checkpoint: epoch 5
SEA/CELLxGENE rehearsal weight: 0.0045
disease covariance weight: 0.0005
pathology contrastive weight: 0.075
architecture: projection-head disease space + pathology-neighborhood loss
composite score: 1.686
```

Key metrics:

```text
AT8 ridge Spearman:          0.213
NeuN ridge Spearman:         0.426
AT8 cosine kNN Spearman:     0.266
NeuN cosine kNN Spearman:    0.303
GFAP cosine kNN Spearman:    0.408
effective dimensions:        7.19
top singular value ratio:    0.430
SEA anchor cosine:           0.975
CELLxGENE anchor cosine:     0.961
```

## Interpretation Layer

The interpretation layer consumes structured outputs:

- donor-held-out prediction metrics
- latent geometry diagnostics
- gene/module digital knockout tables
- latent Jacobian edges
- confounder-adjusted gene/module effects
- external perturbation benchmark results

It produces:

- ranked biological hypotheses
- evidence summaries
- validation suggestions
- caveats and evidence levels

The agentic component should not invent evidence. It should summarize structured model outputs and literature/context with clear uncertainty.

## Future Multimodal Expansion

The graph architecture is gene-level. Spatial transcriptomics and pathology images require a higher-level tissue graph.

Planned hierarchy:

```text
gene graph JEPA
        -> cell/nucleus embeddings
        -> donor or spatial-region summaries
        -> cell/tissue graph model
        -> spatial and imaging alignment
```

This keeps gene-network structure and tissue-neighborhood structure conceptually separate.
