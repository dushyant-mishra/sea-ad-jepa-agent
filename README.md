# SEA-AD Graph-JEPA Agent

**A Graph-JEPA framework for Alzheimer disease microglia: pathology-grounded representation learning, donor-held-out validation, and model-implied counterfactual gene-network discovery.**

This repository is an end-to-end research prototype built around the Seattle Alzheimer Disease Brain Cell Atlas (SEA-AD). The current focus is Microglia-PVM nuclei from middle temporal gyrus (MTG), paired with quantitative neuropathology targets such as AT8/pTau, 6e10/A beta, GFAP, Iba1, and NeuN.

The central question is:

> Can a JEPA-style model learn a biological cell-state space that connects microglial gene programs to real Alzheimer pathology, and can that space be interrogated to generate testable gene-network hypotheses?

This is not a chatbot over a dataset. It is a representation-learning and hypothesis-generation system.

```text
single-nucleus expression
        -> pathology-grounded latent state
        -> donor-held-out prediction
        -> module/gene counterfactual screen
        -> ranked biological hypotheses
        -> external perturbation, spatial, or imaging validation
```

## Project Dashboard

The figures below are the GitHub-facing overview of the project. They are generated from lightweight result tables and schematics, so readers can understand the workflow and current evidence without downloading raw SEA-AD files or model checkpoints.

| Workflow | Why v2 Exists |
|---|---|
| ![Graph-JEPA v2 curriculum](results/figures/public_v2_curriculum_schematic.svg) | ![v1 problems and v2 responses](results/figures/public_v1_to_v2_problem_solution.svg) |
| **Figure legend:** Graph-JEPA v2 uses a staged curriculum: CELLxGENE normal microglia define a healthy/reference manifold, low-pathology SEA-AD nuclei calibrate that reference to aged postmortem tissue, and full SEA-AD Microglia-PVM training learns disease movement with anchor rehearsal. | **Figure legend:** v1 showed that flat-vector JEPA could learn pathology-linked representations, but also exposed limits: no gene topology, over-pinned anchors, and narrow disease-tube geometry. v2 responds with a gene graph, learnable gene identity embeddings, elastic rehearsal, and manifold telemetry. |

| Stage C Tuning | Donor-Level Pathology Geometry |
|---|---|
| ![Stage C sweep leaderboard](results/figures/public_stage_c_sweep_leaderboard.svg) | ![PCA vs JEPA pathology geometry](results/figures/public_pca_vs_jepa_pathology_geometry.svg) |
| **Figure legend:** Stage C configurations are ranked by a composite score balancing pathology predictivity, manifold geometry, and anchor preservation. The current best run is elastic: loose rehearsal plus a small disease covariance penalty keeps anchors near the reference state while allowing disease geometry to move. | **Figure legend:** Donor-level PCA and JEPA spaces are compared by asking whether local neighborhoods predict neuropathology targets. JEPA improves several pathology-neighborhood signals, especially GFAP and A beta/6e10, showing that the representation is more than a prettier UMAP. |

| Cell-Level Diagnostics | Multi-Target Held-Out Validation |
|---|---|
| ![Cell-level donor leakage and pathology mixing](results/figures/public_cell_level_mixing.svg) | ![Multi-target OOF validation](results/figures/public_multitarget_oof_validation.svg) |
| **Figure legend:** Cell-level diagnostics test whether the latent space is dominated by donor identity. JEPA shows lower donor leakage than PCA, while cell-level pathology separation remains difficult because donor pathology scores are broadcast to many individual cells. | **Figure legend:** Pooled donor-held-out validation compares JEPA against pseudobulk ridge across neuropathology targets. Positive values mark where JEPA outperforms the simpler baseline; negative values show where pseudobulk remains stronger. This plot intentionally shows both wins and limitations. |

Full-size figures and captions are collected in [docs/figure_gallery.md](docs/figure_gallery.md).

## Why This Project Exists

Single-cell RNA-seq often gives long gene lists. Neuropathology gives real tissue phenotypes, but it does not directly identify which cell-state programs explain those phenotypes. This project tries to connect those layers.

Instead of only asking:

```text
Which genes are differentially expressed?
```

we ask:

```text
Which learned microglial states predict measured Alzheimer pathology?
Which genes/modules define those states?
What does the model predict would happen if those genes/modules were perturbed?
Which hypotheses survive donor-held-out and confounder-adjusted checks?
```

## Why JEPA

Single-nucleus expression is sparse, noisy, and dropout-heavy. Reconstructing raw counts can force a model to learn technical artifacts. JEPA-style training predicts latent biological state from partial context instead of reconstructing every observed count.

For Alzheimer disease, the useful object is not one noisy count vector. The useful object is the underlying cell state: homeostatic microglia, plaque response, lysosomal/phagocytic activation, complement signaling, lipid handling, vascular/barrier myeloid biology, inflammatory signaling, and disease-associated microglial programs.

## What v1 Taught Us

The first version used a flat-vector snRNA JEPA:

```text
cell = vector of 2,957 genes
encoder = MLP-style expression encoder
objective = predict target latent state from masked/module-masked context
```

Important v1 improvements:

- EMA target encoder fixed a major target-network bug.
- Module-aware masking was better than purely random masking.
- Variance regularization reduced latent contraction.
- Donor-held-out pooled OOF validation showed JEPA could beat pseudobulk on some pathology axes.
- Digital knockouts, latent Jacobians, and confounder-adjusted effects produced useful SEA-AD hypotheses.

Key v1 results:

```text
Stabilized pooled donor-held-out AT8:
  pathology-aware EMA+variance JEPA: Spearman ~= 0.497
  pseudobulk ridge:                  Spearman ~= 0.422

PCA-vs-JEPA donor latent-space deltas:
  GFAP:        +0.220 kNN Spearman
  A beta/6e10: +0.071
  Iba1:        +0.025
  AT8/pTau:    +0.017
  NeuN:        -0.007
```

But v1 also exposed real limitations:

- **Flat-vector topology flaw:** genes were independent columns, so `CSF1R`, `TREM2`, `P2RY12`, and complement genes had no explicit network structure.
- **Over-pinning/fine-tuning issue:** early Stage C-like disease signal appeared, then later training compressed it.
- **Disease tube problem:** elastic rehearsal let disease cells move, but the model sometimes stretched one dominant latent axis instead of building a rich neighborhood geometry.
- **External perturbation mismatch:** K562 and Kampmann/iPSC-microglia tests were useful engineering diagnostics, but v1 was not a true dynamic causal model.
- **Causal boundary:** digital knockouts are model-implied counterfactual hypotheses, not experimental proof.

Those failures motivated v2.

## Graph-JEPA v2

v2 changes the representation from a flat expression vector to a gene graph.

```text
node = gene
edge = STRING gene/protein relationship
node features = expression scalar + learnable gene identity embedding
graph encoder = message-passing neural network
objective = JEPA latent prediction with anchor-preserving rehearsal
```

This directly addresses the v1 topology flaw. The model is no longer told that genes are just unrelated columns. It receives a prior graph so perturbing one gene can influence connected subgraphs.

The current graph input check:

```text
genes: 2,957
STRING t700 edge columns: 231,015
max edge node index: 2,956
HPA/FDA drug targets in graph annotations: 136
predicted membrane genes: 735
predicted secreted genes: 105
```

## v2 Training Curriculum

The v2 curriculum is designed to avoid two traps: learning only diseased SEA-AD biology, and forgetting healthy/reference biology during disease fine-tuning.

### Stage A: Healthy Anchor Pretraining

Train Graph-JEPA on normal-labeled human brain microglia nuclei from CELLxGENE.

Purpose:

```text
learn a broad healthy/reference microglial graph manifold
```

The successful CELLxGENE anchor:

```text
cells: 10,000
donors: 692
matched JEPA genes: 2,863 / 2,957
zero-padded missing genes: 94
dominant assay: 10x 3' v3
```

Current best Stage A checkpoint:

```text
results/models/graph_jepa_stage_a_string_t700_rawvar_e30/graph_jepa.pt
```

Stage A result:

```text
epoch 1:  loss 1.0529, alignment 0.0677, variance 0.9853
epoch 30: loss 0.3699, alignment 0.0024, variance 0.3675
```

### Stage B: SEA-AD Low-Pathology Calibration

Calibrate the Stage A model on low-pathology SEA-AD Microglia-PVM anchors while rehearsing CELLxGENE anchors.

Purpose:

```text
adapt from broad healthy/reference cells to SEA-AD's aged postmortem technical context
without erasing the Stage A reference manifold
```

Stage B anchors:

```text
relaxed low-pathology SEA-AD anchor: 4,467 cells, 10 donors
strict low-pathology SEA-AD anchor:  1,883 cells, 4 donors
```

Stage A-to-B drift audit:

```text
SEA-AD low-pathology anchor cosine: 0.9916
CELLxGENE anchor cosine:           0.9754
```

Interpretation: Stage B calibrated the model without catastrophic forgetting.

### Stage C: Disease-Vector Training With Rehearsal

Train on the full SEA-AD Microglia-PVM disease manifold while preserving both anchors.

Purpose:

```text
learn pathology-relevant disease movement
while retaining healthy/reference geometry
```

The Stage C trainer uses three streams:

```text
stream 1: full SEA-AD Microglia-PVM disease cells
stream 2: SEA-AD low-pathology anchor cells
stream 3: CELLxGENE normal microglia anchor cells
```

This avoids catastrophic forgetting more directly than a purely sequential curriculum.

## Problems We Faced in Stage C

The first Stage C run preserved anchors too well:

```text
SEA-AD anchor cosine:    0.9998
CELLxGENE anchor cosine: 0.9992
```

That looked safe, but it over-pinned the manifold. The disease cells could not reorganize enough to improve local pathology geometry.

We then tried elastic rehearsal:

```text
cosine softplus margin
margin: 0.95
temperature: 100
```

This let the disease manifold move, but telemetry found a new failure:

```text
effective dimensions fell to about 2.10
top singular value ratio rose to about 0.821
```

Interpretation: the model escaped the anchors by stretching into a narrow disease tube. Ridge could still find a pathology vector, but Euclidean kNN struggled because the local neighborhood geometry was poor.

We then added a small disease covariance penalty to reduce the tube effect. A large covariance weight over-damped disease movement, so we built a targeted sweep to tune the balance.

## Current Best Stage C Result

The reproducible sweep is implemented in:

```text
scripts/sweep_stage_c_finetuning.py
```

Sweep outputs:

```text
results/tables/stage_c_finetuning_sweep_summary.csv
results/tables/stage_c_finetuning_fine_tight_summary.csv
results/tables/stage_c_finetuning_fine_loose_summary.csv
results/tables/stage_c_finetuning_combined_leaderboard.csv
```

Best current configuration:

```text
run: fine_loose_01_r005_cov0005
checkpoint: epoch 5
SEA/CELLxGENE rehearsal weight: 0.005
disease covariance weight: 0.0005
composite score: 1.544
```

Key metrics:

```text
AT8 ridge Spearman:          0.356
NeuN ridge Spearman:         0.374
AT8 Euclidean kNN Spearman:  0.065
NeuN Euclidean kNN Spearman: 0.271
AT8 cosine kNN Spearman:     0.227
NeuN cosine kNN Spearman:    0.258
effective dimensions:        4.76
top singular value ratio:    0.481
SEA anchor cosine:           0.956
CELLxGENE anchor cosine:     0.952
```

Interpretation:

```text
The best current Stage C setting is elastic.
It allows disease movement while keeping both anchors just above the 0.95 cosine safety floor.
It improves over the over-pinned runs and reduces the narrow-tube failure mode.
It is still a tuning result, not a final biological validation claim.
```

## Current Biological Hypotheses

Early SEA-AD Microglia-PVM candidates from internal v1/v2 analyses include:

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

Important modules include:

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

These are model-prioritized hypotheses. They should be validated with independent cohorts, perturbation data, spatial transcriptomics, IHC/imaging, or wet-lab experiments.

## Dataset

Primary data source:

- Allen SEA-AD data page: https://brain-map.org/consortia/sea-ad/our-data

Public processed S3 buckets:

- Single-cell / single-nucleus profiling: `s3://sea-ad-single-cell-profiling/`
- Quantitative neuropathology: `s3://sea-ad-quantitative-neuropathology/`
- Spatial transcriptomics: `s3://sea-ad-spatial-transcriptomics/`

Main expression file used locally:

```text
s3://sea-ad-single-cell-profiling/MTG/RNAseq/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad
```

This file is large and is not committed to the repository.

## Repository Guide

Start here:

- [docs/current_status.md](docs/current_status.md): full completed-work log and results.
- [docs/figure_gallery.md](docs/figure_gallery.md): public schematics and result graphs with captions.
- [docs/runbook.md](docs/runbook.md): commands for reproducing the workflow.
- [docs/dataset_guide.md](docs/dataset_guide.md): dataset descriptions and abbreviation glossary.
- [docs/architecture.md](docs/architecture.md): system architecture.
- [docs/causal_discovery.md](docs/causal_discovery.md): counterfactual and causal-validation strategy.
- [docs/project_proposal.md](docs/project_proposal.md): scientific pitch.
- [docs/scientific_pitch.md](docs/scientific_pitch.md): concise reviewer-facing pitch.
- [docs/gpu_setup.md](docs/gpu_setup.md): CUDA/PyTorch setup.
- [docs/github_about.md](docs/github_about.md): GitHub About description and topics.

## Quick Setup

```powershell
conda env create -f environment.yml
conda activate sea-ad-jepa
python -m pip install -r requirements-gpu.txt
python scripts/check_gpu.py
```

If the environment already exists:

```powershell
conda activate sea-ad-jepa
```

Track training in TensorBoard:

```powershell
C:\Users\dushy\anaconda3\envs\sea-ad-jepa\Scripts\tensorboard.exe --logdir runs
```

## Reproduce the Current Stage C Sweep

Run the coarse sweep:

```powershell
$env:PYTHONPATH = "src"
python scripts/sweep_stage_c_finetuning.py `
  --preset coarse `
  --epochs 10 `
  --checkpoint-epochs 005 010 `
  --device auto `
  --out results/tables/stage_c_finetuning_sweep_summary.csv
```

Run the tight and loose refinements:

```powershell
$env:PYTHONPATH = "src"
python scripts/sweep_stage_c_finetuning.py `
  --preset fine_tight `
  --epochs 5 `
  --checkpoint-epochs 005 `
  --device auto `
  --out results/tables/stage_c_finetuning_fine_tight_summary.csv

python scripts/sweep_stage_c_finetuning.py `
  --preset fine_loose `
  --epochs 5 `
  --checkpoint-epochs 005 `
  --device auto `
  --out results/tables/stage_c_finetuning_fine_loose_summary.csv
```

The current best setting is:

```text
fine_loose_01_r005_cov0005
```

## Evidence Discipline

This project separates:

- **Association:** a gene/module correlates with pathology.
- **Prediction:** a representation predicts held-out donors.
- **Model-implied counterfactual:** a frozen model predicts a change after digital perturbation.
- **Causal validation:** external perturbation, spatial, imaging, or experimental evidence supports the mechanism.

This boundary matters. A useful model can prioritize hypotheses, but it does not turn observational single-cell data into proof of causality.
