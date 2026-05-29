# SEA-AD JEPA Agent

**A biological discovery system for turning Alzheimer disease single-cell and pathology data into testable gene-network hypotheses.**

This project asks a simple question:

> Can we learn cell-state representations that connect molecular programs in the brain to measurable Alzheimer pathology, then use those representations to propose candidate gene networks for follow-up?

The first version focuses on the Seattle Alzheimer Disease Brain Cell Atlas (SEA-AD), especially microglia in the middle temporal gyrus (MTG). Microglia are a natural first target because they sit at the intersection of plaque response, inflammation, lipid biology, complement signaling, and major Alzheimer risk genes such as `APOE` and `TREM2`.

## Why This Exists

Single-cell data is powerful, but by itself it often leaves us with long gene lists and unclear biological stories. Pathology and imaging data are biologically grounded, but they do not directly tell us which gene programs are active inside specific cell populations.

This project tries to bridge that gap.

Instead of asking only:

```text
Which genes differ between groups?
```

we ask:

```text
Which cell-state programs predict real tissue pathology?
Which genes and pathways explain those predictive states?
Which hypotheses are strong enough to justify spatial, imaging, or perturbational validation?
```

## Core Idea

The system has three parts:

1. **Biological state learning**

   Learn robust representations from noisy single-nucleus RNA-seq using JEPA-style latent prediction.

2. **Pathology-grounded evaluation**

   Test whether cell-state features predict donor-level neuropathology: AT8/pTau, 6e10/A beta, GFAP, Iba1, NeuN, and biochemical amyloid/tau.

3. **Hypothesis generation**

   Convert predictive signals into ranked gene-network hypotheses, with clear evidence levels and validation suggestions.

The aim is not to build a chatbot over a dataset. The aim is to build a discovery loop:

```text
cell molecular state
        -> pathology prediction
        -> gene/module ranking
        -> interpretable hypothesis
        -> validation plan
```

## Why JEPA

Single-cell expression is sparse and noisy. Reconstructing every raw count can force a model to learn technical noise. JEPA-style training instead asks the model to predict **latent biological state** from partial context.

For this project, the initial JEPA task is:

```text
masked/partial gene expression
        -> context encoder
        -> predictor
        -> target cell-state embedding
```

The long-term goal is to make this multimodal:

```text
transcriptomics + pathology + spatial + imaging
        -> shared latent disease-state space
```

## Current Wedge Result

The first real biological pilot is Microglia-PVM in SEA-AD MTG.

Completed locally:

- Built Microglia-PVM donor pseudobulk features from the full SEA-AD MTG H5AD.
- Created a 10,000-cell Microglia-PVM JEPA pilot.
- Ran donor-level pathology prediction baselines.
- Trained a GPU JEPA model on the microglia pilot.
- Ranked microglial genes associated with AT8/pTau pathology.

First baseline signal:

```text
Microglia-PVM pseudobulk -> AT8/pTau pathology
Spearman ~= 0.53 across held-out donor folds
```

Top AT8-associated genes in the first pass include:

```text
PTPRG
S100A4
CHI3L1
DRAM1
TNFRSF11B
IL27RA
CTSD
NFKBIA
```

These are not causal claims. They are pathology-linked candidate signals that should be tested through enrichment, spatial validation, literature review, and eventually perturbational evidence.

## Dataset

Primary data source:

- Allen SEA-AD data page: https://brain-map.org/consortia/sea-ad/our-data

Public processed S3 buckets:

- Single-cell / single-nucleus profiling: `s3://sea-ad-single-cell-profiling/`
- Quantitative neuropathology: `s3://sea-ad-quantitative-neuropathology/`
- Spatial transcriptomics: `s3://sea-ad-spatial-transcriptomics/`

Main expression file used in this pilot:

```text
s3://sea-ad-single-cell-profiling/MTG/RNAseq/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad
```

This is a large file, so it is not committed to the repository.

## Repository Guide

Start here:

- [docs/project_proposal.md](docs/project_proposal.md): the scientific pitch.
- [docs/scientific_pitch.md](docs/scientific_pitch.md): a concise reviewer-facing pitch.
- [docs/dataset_guide.md](docs/dataset_guide.md): dataset descriptions and abbreviation glossary.
- [docs/architecture.md](docs/architecture.md): the discovery system design.
- [docs/technical_plan.md](docs/technical_plan.md): implementation phases and modeling details.
- [docs/runbook.md](docs/runbook.md): commands for reproducing the local workflow.
- [docs/current_status.md](docs/current_status.md): what has been completed.
- [docs/gpu_setup.md](docs/gpu_setup.md): CUDA/PyTorch setup.

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

## Reproduce the First Microglia Pilot

Download metadata:

```powershell
.\scripts\download_metadata.ps1
python scripts/build_metadata_targets.py
```

Download the processed MTG AnnData:

```powershell
.\scripts\download_s3_file.ps1 `
  -Bucket sea-ad-single-cell-profiling `
  -Key "MTG/RNAseq/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad" `
  -OutFile "data/raw/snrna/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad"
```

Build Microglia-PVM pseudobulk and a 10k JEPA pilot:

```powershell
python scripts/build_microglia_streaming_pilot.py `
  --h5ad data/raw/snrna/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad `
  --cell-max 10000 `
  --n-top-genes 3000 `
  --pilot-out data/processed/sea_ad_mtg_microglia_pvm_10k_hvg3k.h5ad `
  --pseudobulk-out data/processed/sea_ad_mtg_microglia_pvm_pseudobulk.csv `
  --counts-out data/processed/sea_ad_mtg_microglia_pvm_counts.csv
```

Run the microglia pathology baseline:

```powershell
$env:PYTHONPATH = "src"
python scripts/run_pseudobulk_baseline.py `
  --features data/processed/sea_ad_mtg_microglia_pvm_pseudobulk.csv `
  --out results/tables/microglia_pvm_pseudobulk_ridge_1000genes.csv `
  --max-genes 1000
```

Train JEPA:

```powershell
$env:PYTHONPATH = "src"
python scripts/train_jepa_snrna.py `
  --h5ad data/processed/sea_ad_mtg_microglia_pvm_10k_hvg3k.h5ad `
  --out-dir results/models/microglia_pvm_jepa_10k `
  --epochs 20 `
  --device auto
```

Rank genes associated with AT8 pathology:

```powershell
$env:PYTHONPATH = "src"
python scripts/rank_pseudobulk_genes.py `
  --features data/processed/sea_ad_mtg_microglia_pvm_pseudobulk.csv `
  --target "percent AT8 positive area_Grey matter" `
  --out results/tables/microglia_pvm_percent_AT8_gene_rankings.csv `
  --gene-set-out results/tables/microglia_pvm_percent_AT8_gene_set_scores.csv
```

## Evidence Discipline

This project is for discovery and hypothesis generation. It separates:

- **Association**: a signal correlates with pathology.
- **Prediction**: a signal predicts held-out donors.
- **Mechanistic candidate**: genes/modules suggest a plausible pathway.
- **Validated biology**: supported by spatial, imaging, perturbational, or experimental evidence.

That separation is central. A model can help prioritize hypotheses, but it does not turn correlation into causation.
