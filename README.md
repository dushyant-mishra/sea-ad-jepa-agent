# SEA-AD JEPA Agent

A research prototype for discovering Alzheimer disease gene-network hypotheses from SEA-AD single-nucleus transcriptomics, neuropathology, and eventually spatial/imaging data.

The core idea is to combine:

- JEPA-style representation learning for robust biological state embeddings from noisy molecular data.
- Donor-level and tissue-level pathology targets such as A beta, pTau/AT8, GFAP, Iba1, and NeuN.
- An agentic transformer layer that can turn model outputs into ranked, evidence-aware biological hypotheses.

This repository is currently in the first pilot stage: processed SEA-AD MTG snRNA-seq plus donor-level quantitative neuropathology.

## Research Goal

Build a multimodal JEPA-agent framework that learns latent Alzheimer disease cell states and uses those states to identify candidate gene modules, regulators, and validation experiments.

The first concrete question is:

> Can transcriptomic cell-state embeddings learned from SEA-AD MTG nuclei predict donor-level neuropathology burden and reveal candidate AD-associated gene networks?

The first target cell populations are microglia, astrocytes, and vulnerable excitatory neurons because they map naturally onto SEA-AD neuropathology readouts:

- Microglia: Iba1, activated Iba1, A beta plaque association.
- Astrocytes: GFAP/reactive gliosis.
- Neurons: NeuN density and disease vulnerability.
- Disease pathology: 6e10/A beta and AT8/pTau.

See:

- [docs/project_proposal.md](docs/project_proposal.md) for the full motivation.
- [docs/technical_plan.md](docs/technical_plan.md) for the implementation plan.
- [docs/architecture.md](docs/architecture.md) for the system design.
- [docs/gpu_setup.md](docs/gpu_setup.md) for CUDA/PyTorch setup.
- [docs/runbook.md](docs/runbook.md) for the next commands to run.
- [docs/current_status.md](docs/current_status.md) for what has been completed locally.
- [docs/github_repo_checklist.md](docs/github_repo_checklist.md) before publishing to GitHub.

## Current Status

Implemented so far:

- Conda environment: `sea-ad-jepa`
- SEA-AD donor metadata download script
- SEA-AD MTG quantitative neuropathology download script
- Donor/pathology target table builder
- Pathology target QC plotting
- Public S3 prefix lister
- AnnData inspection and pilot subsetting scripts

Local processed metadata output:

```text
data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv
```

This table contains 84 donors and 17 selected pathology targets.

## Data Sources

Primary SEA-AD index:

- Allen SEA-AD data page: https://brain-map.org/consortia/sea-ad/our-data

Public processed S3 buckets:

- Single-cell / single-nucleus profiling: `s3://sea-ad-single-cell-profiling/`
- Quantitative neuropathology: `s3://sea-ad-quantitative-neuropathology/`
- Spatial transcriptomics: `s3://sea-ad-spatial-transcriptomics/`

Current MTG processed AnnData file:

```text
s3://sea-ad-single-cell-profiling/MTG/RNAseq/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad
```

This file is about 33.8 GiB, or about 36.3 GB. It is large enough that downstream workflows should use backed AnnData loading and aggressive pilot subsetting before model training.

## Environment

Recommended setup:

```powershell
conda env create -f environment.yml
conda activate sea-ad-jepa
```

If the environment already exists:

```powershell
conda activate sea-ad-jepa
```

GPU check:

```powershell
python scripts/check_gpu.py
```

This project uses CUDA-enabled PyTorch when available. On this machine, the NVIDIA driver reports CUDA 12.8, so the intended PyTorch wheel index is:

```powershell
python -m pip install -r requirements-gpu.txt
```

Alternative venv setup:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Workflow

### 1. Download Metadata

```powershell
.\scripts\download_metadata.ps1
```

This downloads only the small donor metadata workbook and MTG quantitative neuropathology CSV into:

```text
data/raw/metadata/
```

### 2. Build Pathology Targets

```powershell
python scripts/build_metadata_targets.py
```

Outputs:

```text
data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv
data/processed/metadata/pathology_target_columns.csv
data/processed/metadata/pathology_target_summary.csv
data/processed/metadata/pathology_target_spearman_corr.csv
```

### 3. Plot Metadata QC

```powershell
python scripts/plot_metadata_targets.py
```

Outputs:

```text
results/figures/metadata/key_pathology_target_histograms.png
results/figures/metadata/pathology_target_spearman_corr.png
```

### 4. List SEA-AD S3 Objects Safely

The SEA-AD buckets are large. Prefer the page-limited Python lister:

```powershell
python scripts/list_s3_prefix.py --bucket single-cell --prefix "MTG/RNAseq/" --pattern "\.h5ad$" --max-pages 1
```

Expected MTG H5AD files include:

```text
Reference_MTG_RNAseq_all-nuclei.2022-06-07.h5ad
Reference_MTG_RNAseq_final-nuclei.2022-06-07.h5ad
SEAAD_MTG_RNAseq_all-nuclei.2024-02-13.h5ad
SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad
```

### 5. Download the Processed MTG AnnData File

```powershell
.\scripts\download_s3_file.ps1 `
  -Bucket sea-ad-single-cell-profiling `
  -Key "MTG/RNAseq/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad" `
  -OutFile "data/raw/snrna/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad"
```

Check download progress:

```powershell
.\scripts\check_download_progress.ps1
```

### 6. Inspect AnnData Metadata

Fast categorical metadata summary:

```powershell
python scripts/summarize_h5ad_obs.py `
  --h5ad data/raw/snrna/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad
```

Full AnnData-backed metadata inspection:

```powershell
python scripts/inspect_h5ad.py `
  --h5ad data/raw/snrna/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad `
  --out-dir results/inspection
```

This writes metadata previews so the exact donor, subclass, cell type, and region columns can be confirmed before subsetting.

### 7. Create a Pilot Subset

Fast first pilot, using 10,000 `Microglia-PVM` nuclei:

```powershell
python scripts/make_pilot_subset_fast.py `
  --h5ad data/raw/snrna/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad `
  --out data/processed/sea_ad_mtg_microglia_pvm_10k_hvg3k.h5ad `
  --filter-column Subclass `
  --filter-value Microglia-PVM `
  --max-cells 10000 `
  --n-top-genes 3000
```

Fast smoke-test pilot, using a contiguous 10,000-cell slice:

```powershell
python scripts/make_contiguous_pilot.py `
  --h5ad data/raw/snrna/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad `
  --out data/processed/sea_ad_mtg_contiguous_10k_hvg3k.h5ad `
  --start-row 316988 `
  --n-rows 10000 `
  --n-top-genes 3000
```

Generic AnnData-backed version:

```powershell
python scripts/make_pilot_subset.py `
  --h5ad data/raw/snrna/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad `
  --out data/processed/sea_ad_mtg_microglia_pilot.h5ad `
  --cell-type-column subclass `
  --cell-type-values Microglia `
  --max-cells 50000 `
  --n-top-genes 3000
```

The actual `--cell-type-column` may differ. Run `inspect_h5ad.py` first and adjust based on the observed `obs` columns.

## Repository Layout

```text
.
├── data/
│   ├── raw/
│   └── processed/
├── docs/
│   ├── project_proposal.md
│   ├── technical_plan.md
│   ├── architecture.md
│   └── github_repo_checklist.md
├── results/
│   └── figures/
├── scripts/
│   ├── build_metadata_targets.py
│   ├── download_metadata.ps1
│   ├── download_s3_file.ps1
│   ├── inspect_h5ad.py
│   ├── list_s3_prefix.py
│   ├── list_sea_ad_data.ps1
│   ├── make_pilot_subset.py
│   └── plot_metadata_targets.py
├── src/
│   └── sea_ad_jepa/
│       ├── baselines.py
│       ├── data.py
│       └── jepa.py
├── environment.yml
├── requirements.txt
└── README.md
```

## Planned Modeling Direction

The first model will be a simple snRNA-seq JEPA:

```text
partial gene expression context
        -> context encoder
        -> predictor
        -> predicted target embedding

held-out genes or gene modules
        -> target encoder
        -> target embedding
```

The model will optimize latent prediction rather than raw count reconstruction. Learned cell embeddings will be aggregated by donor and tested against pathology targets.

Baseline comparisons:

- PCA
- scVI or another variational single-cell latent baseline
- Masked autoencoder or masked expression reconstruction
- Ridge/elastic net models on highly variable genes

After creating a pilot AnnData subset, run the first donor-level baseline:

```powershell
$env:PYTHONPATH = "src"
python scripts/run_baseline_ridge.py `
  --h5ad data/processed/sea_ad_mtg_microglia_pilot.h5ad `
  --donor-column "Donor ID" `
  --out results/tables/microglia_ridge_pathology.csv
```

Minimal JEPA training entry point:

```powershell
$env:PYTHONPATH = "src"
python scripts/train_jepa_snrna.py `
  --h5ad data/processed/sea_ad_mtg_microglia_pilot.h5ad `
  --out-dir results/models/microglia_jepa `
  --epochs 20 `
  --device auto
```

Initial evaluation:

- Cell-type preservation
- Donor/pathology prediction
- Robustness to masking/dropout
- Gene module enrichment
- Candidate regulator recovery

## Important Scope Note

This is a discovery and hypothesis-generation framework, not a causal inference engine by default. Model outputs should be reported with evidence levels:

- Association: correlated with pathology or cell state.
- Predictive: predicts held-out donors/cells.
- Regulatory candidate: supported by gene-module or TF evidence.
- Perturbational support: supported by perturbation or time-course data.
- Validated: experimentally confirmed.

That distinction is central to the scientific framing of this project.
