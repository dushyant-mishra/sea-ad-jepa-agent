# Technical Plan

## Phase 0: Project Setup

Status: in progress.

Completed:

- Created `sea-ad-jepa` conda environment.
- Added scripts for SEA-AD metadata download.
- Added scripts for public S3 prefix listing.
- Added donor/pathology target table builder.
- Added metadata QC figure generation.
- Started download of the SEA-AD MTG final-nuclei AnnData file.
- Added donor-level ridge baseline scaffolding.
- Added minimal JEPA model skeleton.
- Downloaded the SEA-AD MTG H5AD file.
- Installed and verified CUDA-enabled PyTorch.
- Created a 10,000-cell contiguous smoke-test pilot.
- Ran the first donor-level ridge baseline.
- Ran a 2-epoch GPU JEPA smoke test.
- Built the real Microglia-PVM donor pseudobulk and 10k cell pilot with sequential CSR streaming.
- Ran Microglia-PVM pseudobulk pathology baselines.
- Trained JEPA on the Microglia-PVM 10k pilot.
- Extracted JEPA donor embeddings and compared them against pathology targets.
- Added first-pass AT8-associated Microglia-PVM gene ranking.

## Phase 1: Data Access and Metadata Targets

### Inputs

Small metadata files:

```text
data/raw/metadata/sea-ad_cohort_donor_metadata_072524.xlsx
data/raw/metadata/sea-ad_all_mtg_quant_neuropath_bydonorid_081122.csv
```

Main expression file:

```text
data/raw/snrna/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad
```

### Generated Metadata Outputs

```text
data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv
data/processed/metadata/pathology_target_columns.csv
data/processed/metadata/pathology_target_summary.csv
data/processed/metadata/pathology_target_spearman_corr.csv
```

### Selected Pathology Targets

The current target table includes 17 donor-level targets:

- `percent 6e10 positive area_Grey matter`
- `number of 6e10 positive objects per area_Grey matter`
- `percent AT8 positive area_Grey matter`
- `number of AT8 positive cells per area_Grey matter`
- `percent GFAP positive area_Grey matter`
- `percent Iba1 positive area_Grey matter`
- `number of activated Iba1 positive cells_Grey matter`
- `percent NeuN positive area_Grey matter`
- `number of NeuN positive cells per area_Grey matter`
- `guhcl abeta40_Grey matter`
- `guhcl abeta42_Grey matter`
- `guhcl pTau_Grey matter`
- `guhcl tTau_Grey matter`
- `ripa abeta40_Grey matter`
- `ripa abeta42_Grey matter`
- `ripa pTau_Grey matter`
- `ripa tTau_Grey matter`

## Phase 2: AnnData Inspection and Pilot Subsetting

### Goal

Create a manageable pilot AnnData file before training any model.

The raw processed MTG H5AD file is large, so workflows should use:

- backed AnnData loading for metadata inspection
- cell-type filtering before loading selected rows into memory
- maximum cell caps for pilot experiments
- highly variable gene selection

### Inspection Command

```powershell
python scripts/inspect_h5ad.py `
  --h5ad data/raw/snrna/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad `
  --out-dir results/inspection
```

### Pilot Subset Command

The exact column names must be confirmed by inspection first.

```powershell
python scripts/make_pilot_subset.py `
  --h5ad data/raw/snrna/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad `
  --out data/processed/sea_ad_mtg_microglia_pilot.h5ad `
  --cell-type-column subclass `
  --cell-type-values Microglia `
  --max-cells 50000 `
  --n-top-genes 3000
```

### Pilot Dataset Requirements

The pilot AnnData should retain:

- cell barcode/index
- donor ID
- cell class/subclass/type labels
- disease or progression metadata if present
- selected highly variable genes
- normalized/log-transformed matrix or clear preprocessing provenance

The donor ID column is essential because pathology labels are donor-level.

## Phase 3: Baselines

Before implementing JEPA, build simple baselines.

### Baseline 1: Donor-Level Gene Aggregation

For each donor and target cell population:

```text
cell expression
        -> mean expression by donor
        -> ridge/elastic net pathology prediction
```

This gives a simple reference for predicting pathology from gene expression.

Implemented entry point:

```powershell
$env:PYTHONPATH = "src"
python scripts/run_baseline_ridge.py `
  --h5ad data/processed/sea_ad_mtg_microglia_pilot.h5ad `
  --donor-column "Donor ID" `
  --out results/tables/microglia_ridge_pathology.csv
```

### Baseline 2: PCA Embeddings

```text
single-cell expression
        -> PCA
        -> donor-level aggregation
        -> pathology prediction
```

### Baseline 3: scVI or Similar Single-Cell Latent Model

If compute allows:

```text
single-cell expression
        -> scVI latent space
        -> donor-level aggregation
        -> pathology prediction
```

## Phase 4: snRNA-seq JEPA

### Model Concept

The first JEPA should be simple and interpretable.

```text
context genes
        -> context encoder
        -> predictor
        -> predicted target embedding

target genes
        -> target encoder
        -> target embedding
```

The loss compares predicted and target embeddings:

```text
loss = cosine_loss(predicted_target, stop_gradient(target_embedding))
```

or:

```text
loss = mean_squared_error(predicted_target, stop_gradient(target_embedding))
```

Implemented entry point:

```powershell
$env:PYTHONPATH = "src"
python scripts/train_jepa_snrna.py `
  --h5ad data/processed/sea_ad_mtg_microglia_pilot.h5ad `
  --out-dir results/models/microglia_jepa `
  --epochs 20 `
  --device auto
```

### Masking Strategies

Start with random gene masking, then move to biology-aware masking.

Options:

- random highly variable gene subsets
- pathway or gene-set masking
- AD-relevant modules such as immune activation, synaptic genes, mitochondrial genes, complement genes
- cell-type-specific marker modules

### Why Latent Prediction

Raw reconstruction can encourage the model to reproduce sparse count noise. JEPA-style latent prediction instead asks whether the model can predict biologically meaningful hidden state.

## Phase 5: Pathology Prediction

After training, compute embeddings for cells and aggregate by donor.

Aggregation options:

- mean embedding per donor and cell type
- attention-weighted donor embedding
- cluster/state proportions per donor
- distribution summaries such as mean, variance, and quantiles

Prediction targets:

- A beta burden
- pTau/AT8 burden
- GFAP burden
- Iba1 burden
- NeuN signal/density
- biochemical amyloid/tau measures

Metrics:

- Spearman correlation
- Pearson correlation
- R squared
- mean absolute error
- cross-validated performance by held-out donor

The main split should be donor-level, not cell-level, to avoid leakage.

## Phase 6: Gene Module and Regulator Discovery

For pathology-associated latent dimensions or clusters:

1. Rank genes associated with the latent factor.
2. Identify enriched pathways or gene sets.
3. Compare to known AD genes and pathways.
4. Infer candidate regulators where possible.
5. Generate candidate networks.

Potential methods:

- differential expression across latent states
- correlation of genes with latent dimensions
- pathway enrichment
- regulon enrichment
- SCENIC/pySCENIC, CellOracle, or GRNBoost2 for comparison

## Phase 7: Agentic Interpretation Layer

The agent should operate on structured outputs, not raw data alone.

Inputs:

- pathology prediction results
- latent factor summaries
- top genes/modules
- enrichment tables
- candidate regulators
- known marker and validation target tables

Agent outputs:

- ranked biological hypotheses
- evidence summaries
- suggested validation stains or perturbations
- figure captions
- caveats and confidence levels

Example output shape:

```text
Hypothesis:
  A microglial latent state associated with high 6e10 A beta burden reflects plaque-responsive immune activation.

Evidence:
  - Predicts held-out donor A beta target.
  - Enriched for complement and lipid-response genes.
  - Candidate regulators include APOE/TREM2/TYROBP-axis genes.

Validation:
  - Iba1 plus 6e10 co-localization.
  - APOE/TREM2/C1q staining near plaques.
  - Spatial enrichment analysis near plaque-heavy regions.
```

## Engineering Notes

### Large File Handling

Do not commit data files. The `.gitignore` excludes:

- `data/raw/`
- `data/processed/`
- large AnnData/HDF5 files
- generated figures and logs

### Reproducibility

Each generated output should be reproducible from:

- source scripts
- environment file
- command-line arguments
- downloaded public SEA-AD objects

### Modeling Safety

Avoid reporting cell-level cross-validation when the target is donor-level pathology. The split must be by donor.

Avoid causal language unless perturbational or longitudinal evidence supports it.
