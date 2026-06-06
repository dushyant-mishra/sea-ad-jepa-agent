# Technical Plan

This plan keeps the implementation tied to the scientific goal:

```text
learn pathology-grounded microglial state representations
        -> validate with donor-held-out pathology prediction
        -> diagnose representation geometry
        -> rank genes/modules with counterfactual screens
        -> prepare external validation
```

## Current Project Direction

The project has moved from v1 flat-vector snRNA JEPA to v2 Graph-JEPA.

v1 remains important because it established baselines, hypothesis candidates, and failure modes. v2 is the main architecture for future work because it represents cells as gene graphs instead of independent gene columns.

## Phase 0: Data and Environment

Status: complete.

Completed:

- SEA-AD metadata and quantitative neuropathology download.
- SEA-AD MTG final-nuclei H5AD download.
- CUDA-enabled PyTorch setup.
- Microglia-PVM streaming extraction from the full H5AD.
- Donor pathology target table with 84 donors and 17 pathology targets.
- Expanded-module Microglia-PVM pilot:

```text
data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad
40,000 cells x 2,957 genes
```

## Phase 1: v1 Flat-JEPA Baseline

Status: complete for the proof-of-concept.

Implemented:

- donor-level pseudobulk ridge baselines
- random and module-aware JEPA masking
- EMA target encoder
- variance regularization
- pathology-aware fine-tuning
- pooled donor-held-out validation
- PCA-vs-JEPA latent-space diagnostics
- cell-level donor leakage checks
- digital knockout screens
- latent Jacobian analysis
- confounder-adjusted gene/module effects

Representative result:

```text
percent AT8 positive area_Grey matter
  pathology-aware EMA+variance JEPA pooled OOF Spearman: ~= 0.497
  pseudobulk ridge pooled OOF Spearman:                  ~= 0.422
```

v1 limitations to carry forward:

- no gene topology
- perturbation alignment is weak for specific microglial regulators
- longer training can collapse or over-compress disease geometry
- observational counterfactuals are hypotheses, not causal proof

## Phase 2: Graph Construction

Status: complete for the current v2 graph.

Inputs:

```text
2,957 JEPA genes
STRING t700 edge graph
Human Protein Atlas / FDA actionability annotations
```

Current graph check:

```text
n_genes: 2,957
n_edge_index_columns: 231,015
max_edge_node_idx: 2,956
HPA/FDA drug target genes: 136
predicted membrane genes: 735
predicted secreted genes: 105
```

Key design decision:

```text
node feature = expression scalar + learnable gene identity embedding
```

This avoids scalar-node over-smoothing and gives the graph model gene identity.

## Phase 3: Stage A Healthy/Reference Pretraining

Status: complete for the first anchor.

Anchor:

```text
CELLxGENE normal-labeled human brain microglia nuclei
10,000 cells
692 donors
2,863 / 2,957 genes matched
94 genes zero-padded
```

Best current Stage A checkpoint:

```text
results/models/graph_jepa_stage_a_string_t700_rawvar_e30/graph_jepa.pt
```

Training summary:

```text
epoch 1:  loss 1.0529, alignment 0.0677, variance 0.9853
epoch 30: loss 0.3699, alignment 0.0024, variance 0.3675
```

Notes:

- Batch 64 was stable but less strong by raw variance at epoch 30.
- Scheduler/covariance Stage A experiment was informative but not the best checkpoint.
- The current Stage A default remains the raw-variance epoch-30 checkpoint.

## Phase 4: Stage B SEA-AD Low-Pathology Calibration

Status: complete.

Purpose:

```text
calibrate the healthy/reference graph model to SEA-AD's aged postmortem context
without catastrophic forgetting
```

Inputs:

```text
SEA-AD low-pathology relaxed anchor: 4,467 cells, 10 donors
SEA-AD low-pathology strict anchor:  1,883 cells, 4 donors
CELLxGENE rehearsal coordinates
```

Best Stage B checkpoint:

```text
results/models/graph_jepa_stage_b_low_pathology_rehearsal_e20/graph_jepa_stage_b.pt
```

Stage A-to-B drift:

```text
SEA-AD low-pathology anchor cosine: 0.9916
CELLxGENE anchor cosine:           0.9754
```

Interpretation: Stage B adapted to SEA-AD without erasing the healthy/reference manifold.

## Phase 5: Stage C Disease-Vector Training

Status: implemented and tuned.

Purpose:

```text
learn disease-relevant movement from the full SEA-AD Microglia-PVM cohort
while preserving SEA-AD low-pathology and CELLxGENE anchors
```

Trainer:

```text
scripts/train_graph_jepa_stage_c_disease.py
```

Batch streams:

```text
disease stream: full SEA-AD Microglia-PVM
SEA anchor stream: low-pathology SEA-AD Microglia-PVM
CELLxGENE stream: normal-labeled microglia nuclei
```

Loss components:

```text
disease JEPA loss
cosine-softplus rehearsal loss
disease covariance penalty
```

Telemetry:

```text
anchor cosine
disease-to-anchor centroid distance
disease variance spread
disease effective dimensions
top singular value ratio
```

## Phase 6: Stage C Tuning Sweep

Status: complete for the first coarse and fine sweeps.

Sweep script:

```text
scripts/sweep_stage_c_finetuning.py
```

Outputs:

```text
results/tables/stage_c_finetuning_sweep_summary.csv
results/tables/stage_c_finetuning_fine_tight_summary.csv
results/tables/stage_c_finetuning_fine_loose_summary.csv
results/tables/stage_c_finetuning_combined_leaderboard.csv
```

Best current setting:

```text
run: fine_loose_01_r005_cov0005
checkpoint: epoch 5
SEA/CELLxGENE rehearsal weight: 0.005
disease covariance weight: 0.0005
```

Metrics:

```text
composite score:             1.544
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
The useful Stage C regime is elastic, not tightly pinned.
The anchor cosines should remain above about 0.95.
The disease manifold should avoid both collapse and one-dimensional tube behavior.
```

## Phase 7: Hypothesis Generation

Status: implemented for first internal SEA-AD hypotheses.

Current evidence sources:

- pseudobulk gene/pathology rankings
- JEPA latent factor decoding
- digital module/gene knockouts
- fold-specific knockouts
- latent Jacobian edges
- confounder-adjusted module/gene effects

Candidate genes:

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

Candidate modules:

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

## Phase 8: External Validation

Status: partially implemented.

Completed:

- K562/Replogle streaming smoke test machinery.
- Kampmann/iPSC-microglia DEG-vector benchmark.

Interpretation:

```text
K562 is mainly an engineering smoke test.
Kampmann/iPSC-microglia is more relevant but still not a perfect cell-level guide-assignment validation.
```

Next validation targets:

- better iPSC-microglia or macrophage Perturb-seq with per-cell guide labels
- independent Alzheimer single-nucleus cohorts for zero-shot projection
- spatial transcriptomics validation near AT8/6e10 pathology fields

## Phase 9: Multimodal Expansion

Future work:

```text
gene graph JEPA
        -> cell embeddings
        -> spatial/tissue graph
        -> pathology image and IHC alignment
```

Important architecture boundary:

```text
gene graph: nodes are genes
tissue graph: nodes are cells or spatial regions
```

These should be connected hierarchically, not mixed into one graph without care.

## Modeling Rules

- Use donor-level splits for donor-level pathology targets.
- Treat digital knockouts as model-implied counterfactuals.
- Do not claim causality without perturbational or experimental support.
- Keep raw data, checkpoints, and coordinate banks out of git.
- Commit lightweight summaries, figures, and runbook commands.
