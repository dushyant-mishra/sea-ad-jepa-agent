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

Expanded-module donor-balanced training:

```powershell
$env:PYTHONPATH = "src"
python scripts/build_microglia_streaming_pilot.py `
  --h5ad data/raw/snrna/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad `
  --cell-max 40000 `
  --n-top-genes 3000 `
  --pilot-out data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad `
  --pseudobulk-out data/processed/sea_ad_mtg_microglia_pvm_pseudobulk_expanded_modules.csv `
  --counts-out data/processed/sea_ad_mtg_microglia_pvm_counts_expanded_modules.csv `
  --preserve-module-genes

python scripts/train_jepa_snrna.py `
  --h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad `
  --out-dir results/models/microglia_pvm_jepa_expanded_modules_balanced_e40 `
  --log-dir runs/microglia_pvm_jepa_expanded_modules_balanced_e40 `
  --epochs 40 `
  --batch-size 512 `
  --donor-balanced-sampling `
  --mask-mode mixed `
  --lr 0.0002 `
  --checkpoint-every 10 `
  --device auto
```

EMA-target JEPA training:

```powershell
$env:PYTHONPATH = "src"
python scripts/train_jepa_snrna.py `
  --h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad `
  --out-dir results/models/microglia_pvm_jepa_ema_expanded_balanced_e40 `
  --log-dir runs/microglia_pvm_jepa_ema_expanded_balanced_e40 `
  --epochs 40 `
  --batch-size 512 `
  --donor-balanced-sampling `
  --mask-mode mixed `
  --lr 0.0002 `
  --ema-decay 0.996 `
  --checkpoint-every 10 `
  --device auto
```

EMA-target JEPA with variance regularization:

```powershell
$env:PYTHONPATH = "src"
python scripts/train_jepa_snrna.py `
  --h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad `
  --out-dir results/models/microglia_pvm_jepa_ema_var_expanded_balanced_e40 `
  --log-dir runs/microglia_pvm_jepa_ema_var_expanded_balanced_e40 `
  --epochs 40 `
  --batch-size 512 `
  --donor-balanced-sampling `
  --mask-mode mixed `
  --lr 0.0002 `
  --ema-decay 0.996 `
  --variance-weight 0.05 `
  --variance-gamma 1.0 `
  --checkpoint-every 10 `
  --device auto
```

Pathology-aware fine-tuning with donor-held-out validation:

```powershell
$env:PYTHONPATH = "src"
python scripts/finetune_jepa_pathology.py `
  --h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad `
  --checkpoint results/models/microglia_pvm_jepa_expanded_modules_balanced_e40/gene_jepa.pt `
  --out-dir results/models/microglia_pvm_jepa_expanded_modules_at8_finetune `
  --log-dir runs/microglia_pvm_jepa_expanded_modules_at8_finetune `
  --target "percent AT8 positive area_Grey matter" `
  --epochs 30 `
  --batch-size 512 `
  --samples-per-epoch 40000 `
  --lr 0.00005 `
  --device auto
```

Donor-grouped 5-fold validation:

```powershell
$env:PYTHONPATH = "src"
python scripts/repeated_donor_groupkfold_validation.py `
  --target "percent AT8 positive area_Grey matter" `
  --feature-result pseudobulk data/processed/sea_ad_mtg_microglia_pvm_pseudobulk_expanded_modules.csv `
  --feature-result jepa_ema_e20 results/tables/microglia_pvm_jepa_ema_expanded_balanced_e20_donor_embeddings.csv `
  --feature-result jepa_ema_var_e30 results/tables/microglia_pvm_jepa_ema_var_expanded_balanced_e30_donor_embeddings.csv `
  --finetune-h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad `
  --finetune-checkpoint results/models/microglia_pvm_jepa_ema_var_expanded_balanced_e40/gene_jepa_epoch_030.pt `
  --finetune-label jepa_ema_var_pathology_finetune `
  --finetune-epochs 15 `
  --finetune-lr 0.00005 `
  --batch-size 512 `
  --samples-per-epoch 40000 `
  --n-splits 5 `
  --max-features 1000 `
  --out results/tables/donor_groupkfold_validation.csv `
  --summary-out results/tables/donor_groupkfold_validation_summary.csv `
  --device auto
```

Stabilized donor validation with stratified folds, log-transformed target, and pooled out-of-fold scoring:

```powershell
$env:PYTHONPATH = "src"
python scripts/repeated_donor_groupkfold_validation.py `
  --target "percent AT8 positive area_Grey matter" `
  --splitter stratified_groupkfold `
  --target-bins 5 `
  --target-transform log1p `
  --feature-result pseudobulk data/processed/sea_ad_mtg_microglia_pvm_pseudobulk_expanded_modules.csv `
  --feature-result jepa_ema_e20 results/tables/microglia_pvm_jepa_ema_expanded_balanced_e20_donor_embeddings.csv `
  --feature-result jepa_ema_var_e30 results/tables/microglia_pvm_jepa_ema_var_expanded_balanced_e30_donor_embeddings.csv `
  --finetune-h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad `
  --finetune-checkpoint results/models/microglia_pvm_jepa_ema_var_expanded_balanced_e40/gene_jepa_epoch_030.pt `
  --finetune-label jepa_ema_var_pathology_finetune `
  --finetune-epochs 15 `
  --finetune-lr 0.00005 `
  --batch-size 512 `
  --samples-per-epoch 40000 `
  --n-splits 5 `
  --max-features 1000 `
  --out results/tables/donor_stratified_groupkfold_validation_log1p.csv `
  --summary-out results/tables/donor_stratified_groupkfold_validation_log1p_summary.csv `
  --oof-out results/tables/donor_stratified_groupkfold_oof_log1p.csv `
  --oof-summary-out results/tables/donor_stratified_groupkfold_oof_log1p_summary.csv `
  --device auto
```

Run the same stabilized validation across multiple neuropathology targets:

```powershell
$env:PYTHONPATH = "src"
python scripts/repeated_donor_groupkfold_validation.py `
  --splitter stratified_groupkfold `
  --target-bins 5 `
  --target-transform log1p `
  --targets "percent AT8 positive area_Grey matter" "percent 6e10 positive area_Grey matter" "percent GFAP positive area_Grey matter" "percent Iba1 positive area_Grey matter" "percent NeuN positive area_Grey matter" "guhcl pTau_Grey matter" "guhcl abeta42_Grey matter" "ripa pTau_Grey matter" "ripa abeta42_Grey matter" `
  --feature-result pseudobulk data/processed/sea_ad_mtg_microglia_pvm_pseudobulk_expanded_modules.csv `
  --feature-result jepa_ema_e20 results/tables/microglia_pvm_jepa_ema_expanded_balanced_e20_donor_embeddings.csv `
  --feature-result jepa_ema_var_e30 results/tables/microglia_pvm_jepa_ema_var_expanded_balanced_e30_donor_embeddings.csv `
  --n-splits 5 `
  --max-features 1000 `
  --out results/tables/multitarget_stratified_groupkfold_validation_log1p_ridge.csv `
  --summary-out results/tables/multitarget_stratified_groupkfold_validation_log1p_ridge_summary.csv `
  --oof-out results/tables/multitarget_stratified_groupkfold_oof_log1p_ridge.csv `
  --oof-summary-out results/tables/multitarget_stratified_groupkfold_oof_log1p_ridge_summary.csv `
  --device auto
```

Run the first in-silico causal module screen:

```powershell
$env:PYTHONPATH = "src"
python scripts/causal_in_silico_knockout.py `
  --h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad `
  --checkpoint results/models/microglia_pvm_jepa_ema_expanded_at8_finetune/jepa_pathology_finetuned.pt `
  --mode module `
  --intervention global_mean `
  --out results/tables/causal_module_knockouts_at8_global_mean.csv `
  --donor-out results/tables/causal_module_knockouts_at8_global_mean_by_donor.csv `
  --batch-size 1024 `
  --device auto
```

Run single-gene follow-up in top modules:

```powershell
$env:PYTHONPATH = "src"
python scripts/causal_in_silico_knockout.py `
  --h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad `
  --checkpoint results/models/microglia_pvm_jepa_ema_expanded_at8_finetune/jepa_pathology_finetuned.pt `
  --mode gene `
  --modules at8_associated_first_pass homeostatic_microglia vascular_barrier_myeloid complement antigen_presentation inflammatory_signaling `
  --intervention global_mean `
  --out results/tables/causal_gene_knockouts_top_modules_at8_global_mean.csv `
  --donor-out results/tables/causal_gene_knockouts_top_modules_at8_global_mean_by_donor.csv `
  --batch-size 1024 `
  --device auto
```

Run fold-specific donor-held-out causal module knockouts:

```powershell
$env:PYTHONPATH = "src"
python scripts/causal_fold_specific_knockout.py `
  --h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad `
  --checkpoint results/models/microglia_pvm_jepa_ema_var_expanded_balanced_e40/gene_jepa_epoch_030.pt `
  --target "percent AT8 positive area_Grey matter" `
  --target-transform log1p `
  --splitter stratified_groupkfold `
  --target-bins 5 `
  --n-splits 5 `
  --mode module `
  --intervention global_mean `
  --epochs 15 `
  --batch-size 512 `
  --samples-per-epoch 40000 `
  --lr 0.00005 `
  --freeze-encoder `
  --out results/tables/causal_fold_specific_module_knockouts_at8_global_mean.csv `
  --donor-out results/tables/causal_fold_specific_module_knockouts_at8_global_mean_by_donor.csv `
  --fold-out results/tables/causal_fold_specific_module_knockouts_at8_global_mean_by_fold.csv `
  --device auto
```

Repeat with `--intervention donor_mean` and `--intervention zero` to distinguish conservative replacement effects from aggressive knockout stress-test effects.

Run latent Jacobian analysis:

```powershell
$env:PYTHONPATH = "src"
python scripts/causal_latent_jacobian.py `
  --h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad `
  --checkpoint results/models/microglia_pvm_jepa_ema_var_expanded_balanced_e40/gene_jepa_epoch_030.pt `
  --max-cells 2048 `
  --batch-size 512 `
  --jacobian-batch-size 128 `
  --top-edges 500 `
  --matrix-out results/tables/latent_jacobian_ema_var_e30_matrix.csv `
  --edges-out results/tables/latent_jacobian_ema_var_e30_top_edges.csv `
  --annotations-out results/tables/latent_jacobian_ema_var_e30_module_annotations.csv `
  --device auto
```

Run confounder-adjusted module effects:

```powershell
$env:PYTHONPATH = "src"
python scripts/causal_confounder_adjusted_effects.py `
  --pseudobulk data/processed/sea_ad_mtg_microglia_pvm_pseudobulk_expanded_modules.csv `
  --embeddings results/tables/microglia_pvm_jepa_ema_var_expanded_balanced_e30_donor_embeddings.csv `
  --target "percent AT8 positive area_Grey matter" `
  --mode module `
  --out results/tables/confounder_adjusted_module_effects_at8.csv `
  --device auto
```

Run confounder-adjusted top-gene effects:

```powershell
$env:PYTHONPATH = "src"
python scripts/causal_confounder_adjusted_effects.py `
  --pseudobulk data/processed/sea_ad_mtg_microglia_pvm_pseudobulk_expanded_modules.csv `
  --embeddings results/tables/microglia_pvm_jepa_ema_var_expanded_balanced_e30_donor_embeddings.csv `
  --target "percent AT8 positive area_Grey matter" `
  --mode gene `
  --genes PTPRG CHI3L1 MRC1 CTSD DRAM1 P2RY12 S100A4 MSR1 TNFRSF11B NFKBIA `
  --out results/tables/confounder_adjusted_top_gene_effects_at8.csv `
  --device auto
```

Evaluate donor-level PCA-vs-JEPA latent-space geometry for the dimensionality-reduction comparison:

```powershell
$env:PYTHONPATH = "src"
python scripts/evaluate_latent_spaces.py `
  --pseudobulk data/processed/sea_ad_mtg_microglia_pvm_pseudobulk_expanded_modules.csv `
  --jepa results/tables/microglia_pvm_jepa_ema_var_expanded_balanced_e30_donor_embeddings.csv `
  --metrics-out results/tables/latent_space_evaluation_metrics.csv `
  --embedding-out results/tables/latent_space_umap_coordinates.csv `
  --figure-out results/figures/latent_space_pca_vs_jepa_umap_at8_neun.svg `
  --html-out results/figures/latent_space_pca_vs_jepa_umap_at8_neun.html
```

Evaluate cell-level donor leakage and pathology mixing:

```powershell
$env:PYTHONPATH = "src"
python scripts/evaluate_cell_level_mixing.py `
  --sample-size 10000 `
  --n-permutations 5 `
  --chunk-size 512 `
  --device auto `
  --out results/tables/cell_level_mixing_metrics.csv `
  --sample-out results/tables/cell_level_mixing_sample_metadata.csv
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
