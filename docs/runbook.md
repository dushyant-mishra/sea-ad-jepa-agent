# Runbook

This runbook is the operational path for the first SEA-AD JEPA pilot.

## 1. Confirm Dataset Download

```powershell
.\scripts\check_download_progress.ps1
```

When the download completes, the final file should be:

```text
data/raw/snrna/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad
```

If the file still has a temporary suffix such as `.4FEB38ED`, wait for the AWS CLI process to finish.

## 2. Confirm GPU

Install GPU PyTorch:

```powershell
conda activate sea-ad-jepa
python -m pip install -r requirements-gpu.txt
```

Validate:

```powershell
python scripts/check_gpu.py
```

Expected:

```text
CUDA available: True
GPU: NVIDIA GeForce RTX 3080 Laptop GPU
Test matmul OK.
```

## 3. Inspect AnnData

```powershell
python scripts/inspect_h5ad.py `
  --h5ad data/raw/snrna/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad `
  --out-dir results/inspection
```

Then inspect:

```text
results/inspection/obs_columns.csv
results/inspection/obs_head.csv
```

Identify:

- donor ID column
- cell class/subclass/type columns
- disease/progression metadata columns if present

## 4. Create Pilot Subset

Example:

```powershell
python scripts/make_pilot_subset.py `
  --h5ad data/raw/snrna/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad `
  --out data/processed/sea_ad_mtg_microglia_pilot.h5ad `
  --cell-type-column subclass `
  --cell-type-values Microglia `
  --max-cells 50000 `
  --n-top-genes 3000
```

Adjust `--cell-type-column` and `--cell-type-values` based on the inspection output.

## 5. Run Baseline

```powershell
$env:PYTHONPATH = "src"
python scripts/run_baseline_ridge.py `
  --h5ad data/processed/sea_ad_mtg_microglia_pilot.h5ad `
  --donor-column "Donor ID" `
  --out results/tables/microglia_ridge_pathology.csv
```

For the real Microglia-PVM pilot, build donor pseudobulk and a 10k cell-level pilot:

```powershell
python scripts/build_microglia_streaming_pilot.py `
  --h5ad data/raw/snrna/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad `
  --cell-max 10000 `
  --n-top-genes 3000 `
  --pilot-out data/processed/sea_ad_mtg_microglia_pvm_10k_hvg3k.h5ad `
  --pseudobulk-out data/processed/sea_ad_mtg_microglia_pvm_pseudobulk.csv `
  --counts-out data/processed/sea_ad_mtg_microglia_pvm_counts.csv
```

Run the Microglia-PVM pseudobulk baseline:

```powershell
$env:PYTHONPATH = "src"
python scripts/run_pseudobulk_baseline.py `
  --features data/processed/sea_ad_mtg_microglia_pvm_pseudobulk.csv `
  --out results/tables/microglia_pvm_pseudobulk_ridge_1000genes.csv `
  --max-genes 1000
```

Adjust `--donor-column` based on inspection output.

## 6. Train Minimal JEPA

Random masking baseline:

```powershell
$env:PYTHONPATH = "src"
python scripts/train_jepa_snrna.py `
  --h5ad data/processed/sea_ad_mtg_microglia_pvm_10k_hvg3k.h5ad `
  --out-dir results/models/microglia_pvm_jepa_10k `
  --epochs 20 `
  --device auto
```

Biology-aware mixed masking:

```powershell
$env:PYTHONPATH = "src"
python scripts/train_jepa_snrna.py `
  --h5ad data/processed/sea_ad_mtg_microglia_pvm_10k_hvg3k.h5ad `
  --out-dir results/models/microglia_pvm_jepa_10k_mixed_masking `
  --epochs 20 `
  --mask-mode mixed `
  --device auto
```

Recommended module-preserved mixed-masking run:

```powershell
python scripts/build_microglia_streaming_pilot.py `
  --h5ad data/raw/snrna/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad `
  --cell-max 10000 `
  --n-top-genes 3000 `
  --pilot-out data/processed/sea_ad_mtg_microglia_pvm_10k_hvg3k_module_preserved.h5ad `
  --pseudobulk-out data/processed/sea_ad_mtg_microglia_pvm_pseudobulk_module_preserved_refresh.csv `
  --counts-out data/processed/sea_ad_mtg_microglia_pvm_counts_module_preserved_refresh.csv `
  --preserve-module-genes

$env:PYTHONPATH = "src"
python scripts/train_jepa_snrna.py `
  --h5ad data/processed/sea_ad_mtg_microglia_pvm_10k_hvg3k_module_preserved.h5ad `
  --out-dir results/models/microglia_pvm_jepa_10k_module_preserved_mixed `
  --log-dir runs/microglia_pvm_jepa_10k_module_preserved_mixed `
  --epochs 20 `
  --mask-mode mixed `
  --device auto
```

View training progress with TensorBoard:

```powershell
tensorboard --logdir runs
```

Then open the local TensorBoard URL printed in the terminal.

To continue training from an existing checkpoint:

```powershell
$env:PYTHONPATH = "src"
python scripts/train_jepa_snrna.py `
  --h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_module_preserved.h5ad `
  --resume-checkpoint results/models/microglia_pvm_jepa_all_module_preserved_mixed_e60/gene_jepa.pt `
  --out-dir results/models/microglia_pvm_jepa_all_module_preserved_mixed_e100 `
  --log-dir runs/microglia_pvm_jepa_all_module_preserved_mixed_e100 `
  --epochs 40 `
  --mask-mode mixed `
  --lr 0.0003 `
  --device auto
```

Embed cells and aggregate JEPA embeddings by donor:

```powershell
$env:PYTHONPATH = "src"
python scripts/embed_jepa_snrna.py `
  --h5ad data/processed/sea_ad_mtg_microglia_pvm_10k_hvg3k.h5ad `
  --checkpoint results/models/microglia_pvm_jepa_10k/gene_jepa.pt `
  --donor-out results/tables/microglia_pvm_jepa_donor_embeddings.csv
```

Compare JEPA donor embeddings to pathology:

```powershell
$env:PYTHONPATH = "src"
python scripts/run_pseudobulk_baseline.py `
  --features results/tables/microglia_pvm_jepa_donor_embeddings.csv `
  --out results/tables/microglia_pvm_jepa_embedding_ridge.csv `
  --max-genes 0
```

Compare pseudobulk, random-masking JEPA, and mixed-masking JEPA:

```powershell
$env:PYTHONPATH = "src"
python scripts/compare_pathology_results.py `
  --result pseudobulk results/tables/microglia_pvm_pseudobulk_ridge_1000genes.csv `
  --result jepa_random results/tables/microglia_pvm_jepa_embedding_ridge.csv `
  --result jepa_mixed results/tables/microglia_pvm_jepa_mixed_embedding_ridge.csv `
  --result jepa_module_preserved results/tables/microglia_pvm_jepa_module_preserved_embedding_ridge.csv `
  --out results/tables/microglia_pvm_model_comparison.csv
```

Rank genes associated with an AT8 pathology target:

```powershell
$env:PYTHONPATH = "src"
python scripts/rank_pseudobulk_genes.py `
  --features data/processed/sea_ad_mtg_microglia_pvm_pseudobulk.csv `
  --target "percent AT8 positive area_Grey matter" `
  --out results/tables/microglia_pvm_percent_AT8_gene_rankings.csv `
  --gene-set-out results/tables/microglia_pvm_percent_AT8_gene_set_scores.csv
```

Generate an integrated interpretation report:

```powershell
$env:PYTHONPATH = "src"
python scripts/generate_integrated_microglia_report.py `
  --out results/reports/microglia_pvm_integrated_report.md
```

## 7. Interpret First Results

The first useful comparison is:

```text
mean-expression ridge baseline
        vs
JEPA embedding pathology prediction
```

Do not claim causality. The first milestone is predictive association and interpretable hypothesis generation.
