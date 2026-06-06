# Project Proposal

## Title

SEA-AD Graph-JEPA Agent: Pathology-Grounded Microglial State Learning and Counterfactual Gene-Network Discovery in Alzheimer Disease

## Short Pitch

This project builds a Graph-JEPA framework for learning Alzheimer disease-relevant microglial cell states from SEA-AD single-nucleus transcriptomics and quantitative neuropathology.

The goal is not simply to make attractive UMAPs or classify cell types. The goal is to learn a biological state space that can be evaluated against measured pathology, interrogated with model-implied counterfactuals, and used to prioritize gene-network hypotheses for external validation.

```text
SEA-AD Microglia-PVM expression
        -> JEPA / Graph-JEPA latent state
        -> donor-held-out pathology prediction
        -> gene/module counterfactual screens
        -> ranked hypotheses for spatial, perturbational, or imaging validation
```

## Biological Motivation

Alzheimer disease datasets increasingly combine single-cell transcriptomics, spatial assays, imaging, quantitative pathology, and donor clinical metadata. The bottleneck is no longer only data access. The bottleneck is turning these layers into testable biological hypotheses.

Microglia are the first focus because they sit at the intersection of:

- plaque response
- complement signaling
- lipid handling
- lysosomal/phagocytic activation
- inflammatory signaling
- vascular/barrier myeloid biology
- known Alzheimer risk pathways such as `APOE`, `TREM2`, `TYROBP`, and `PLCG2`

SEA-AD is a strong first dataset because it links human brain single-nucleus data to quantitative neuropathology targets including AT8/pTau, 6e10/A beta, GFAP, Iba1, NeuN, and biochemical amyloid/tau measures.

## Why Cell-State Representations Matter

A raw single-nucleus count vector is a noisy measurement. A useful learned representation should capture the underlying biological program active in the cell.

```text
raw expression counts
        -> sparse and technical

cell-state representation
        -> compact biological program
```

If the representation is meaningful, it should help answer:

```text
Which microglial states track tau pathology?
Which states track neuronal density loss?
Which modules define those states?
Which hypotheses should be tested outside SEA-AD?
```

## v1 Lessons

The first model family used flat-vector snRNA JEPA:

```text
cell = vector of genes
model = expression encoder + EMA target encoder + predictor
training = masked/module-masked latent prediction
```

v1 taught us several useful things:

- EMA target updates were essential; a static target encoder bottlenecked learning.
- Module-aware masking was more biologically meaningful than purely random masking.
- Variance regularization reduced latent contraction.
- Donor-held-out pooled OOF validation showed JEPA could beat pseudobulk on AT8 in one stabilized comparison.
- Digital knockouts, latent Jacobians, and confounder-adjusted effects produced plausible SEA-AD hypotheses.

Representative v1 result:

```text
percent AT8 positive area_Grey matter
  pathology-aware EMA+variance JEPA pooled OOF Spearman: ~= 0.497
  pseudobulk ridge pooled OOF Spearman:                  ~= 0.422
```

v1 also exposed the limitations that motivate v2:

- genes were treated as independent columns rather than a regulatory graph
- disease fine-tuning could over-pin anchors or collapse into a narrow disease tube
- K562 and iPSC-microglia perturbation checks showed that flat-vector JEPA is not enough for true perturbation dynamics
- observational SEA-AD results must remain hypothesis-generating, not causal proof

## Graph-JEPA v2

v2 moves from a flat expression vector to a gene graph.

```text
node = gene
node features = expression scalar + learnable gene identity embedding
edge = STRING relationship
encoder = graph neural network
objective = JEPA latent prediction
```

This matters because biology is not a bag of independent genes. If a gene is perturbed, the relevant signal should propagate through a structured network neighborhood.

Current graph input:

```text
genes: 2,957
STRING t700 edge columns: 231,015
HPA/FDA drug targets: 136
predicted membrane genes: 735
predicted secreted genes: 105
```

## v2 Curriculum

The training curriculum has three stages.

### Stage A: Healthy/Normal Microglia Anchor

Use CELLxGENE normal-labeled human brain microglia nuclei to learn a broad reference manifold.

Purpose:

```text
learn healthy/reference microglial graph structure
```

### Stage B: SEA-AD Low-Pathology Calibration

Use low-pathology SEA-AD Microglia-PVM donors to adapt the model to aged postmortem SEA-AD technical context while rehearsing the CELLxGENE anchor.

Purpose:

```text
calibrate to SEA-AD without catastrophic forgetting
```

### Stage C: Disease-Vector Training

Train on full SEA-AD Microglia-PVM while preserving both anchors with three-stream rehearsal.

Purpose:

```text
learn disease-relevant movement while retaining reference geometry
```

## Current v2 Result

The first Stage C settings over-preserved the anchors. Anchor cosine values near 0.999 looked safe, but the disease manifold was too pinned to reorganize.

Elastic rehearsal helped, but initially produced a narrow disease tube:

```text
effective dimensions: about 2.10
top singular value ratio: about 0.821
```

A targeted sweep found a better balance.

```text
best current Stage C run: fine_loose_01_r005_cov0005
checkpoint: epoch 5
SEA/CELLxGENE rehearsal weight: 0.005
disease covariance weight: 0.0005
composite score: 1.544
```

Key metrics:

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

Interpretation: the current best v2 Stage C setting is intentionally elastic. It allows pathology-related movement while keeping both anchors just above the 0.95 cosine safety boundary.

## Hypothesis Layer

Current SEA-AD Microglia-PVM candidates include:

```text
PTPRG
S100A4
CHI3L1
DRAM1
TNFRSF11B
IL27RA
CTSD
NFKBIA
P2RY12
CX3CR1
F13A1
```

Important candidate modules include:

```text
homeostatic microglia
vascular/barrier myeloid
lysosome/phagocytosis
complement
lipid metabolism
plaque response
disease-associated microglia
AT8-associated first-pass genes
```

These are model-prioritized hypotheses. They require external validation.

## Evidence Boundary

The project separates:

```text
association
prediction
model-implied counterfactual
external perturbation support
experimental validation
```

Digital knockouts and latent Jacobians are useful for prioritization, but they do not prove causality in observational SEA-AD data.

## Long-Term Vision

The long-term system should combine:

- Graph-JEPA over gene regulatory structure
- CELLxGENE-scale pretraining
- SEA-AD pathology fine-tuning
- external perturbation validation
- spatial transcriptomics and pathology image alignment
- agent-generated biological reports with explicit evidence grading

The final goal is a discovery system that can say:

```text
Here is the disease-linked microglial state.
Here are the genes/modules defining it.
Here is the counterfactual prediction.
Here is the validation experiment that would test it.
```
