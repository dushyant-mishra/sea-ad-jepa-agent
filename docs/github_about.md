# GitHub About

Use this text for the GitHub repository About panel.

## Description

```text
Graph-JEPA framework for SEA-AD Alzheimer microglia: pathology-grounded representation learning, graph-mediated counterfactual screens, artifact-audited targets, and translational triage.
```

## Website

Leave blank unless a dashboard is deployed publicly.

## Topics

```text
alzheimer-disease
single-cell-rna-seq
jepa
graph-neural-network
causal-discovery
bioinformatics
pytorch
sea-ad
microglia
computational-biology
```

## Short Project Thesis

This project builds a Graph-JEPA biological state space for SEA-AD Alzheimer disease microglia. It asks whether learned cell-state representations can connect Microglia-PVM transcriptomic programs to measured neuropathology and support counterfactual gene-network hypothesis generation.

The current v2 direction addresses limitations found in v1 flat-vector JEPA:

```text
v1 problem: genes were independent columns
v2 response: genes are graph nodes with STRING edges and learnable gene identity embeddings

v1 problem: disease fine-tuning could over-pin or collapse geometry
v2 response: Stage A/B/C curriculum with anchor rehearsal, covariance diagnostics, projection-head disease geometry, and sweep-based tuning
```

Current best Stage C setting:

```text
run: upgrade_fine_08_r0045_cov0005_pc0075
rehearsal weight: 0.0045
disease covariance weight: 0.0005
pathology contrastive weight: 0.075
checkpoint: epoch 5
composite score: 1.686
anchor cosines: SEA 0.975, CELLxGENE 0.961
```

Current biological extraction layer:

```text
active readout:
  frozen Graph-JEPA Stage B backbone + linear pathology heads

clean first-pass translational target set:
  TLR2
  APP
  APOE

downgraded target:
  CD4, flagged for technical count-depth correlation

latest triage:
  TLR2: membrane-accessible immunomodulatory target
  APP: membrane/secreted AD pathway and biomarker node
  APOE: secreted lipid-transport / biomarker target
```

Amyloid/6e10 boundary:

```text
frozen ElasticNet axis:
  weak but reproducible donor-level 6e10 signal

gated-attention MIL:
  did not generalize in donor-held-out evaluation

claim boundary:
  exploratory amyloid-associated readout, not validated plaque-proximal microglia
```

## Evidence Boundary

The repository should describe digital knockouts and latent causal analyses as model-implied hypotheses. True causal validation requires external perturbation, spatial, imaging, or experimental evidence.
