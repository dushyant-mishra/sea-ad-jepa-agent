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

Run the K562 Perturb-seq engineering smoke test:

```powershell
$env:PYTHONPATH = "src"
python scripts/benchmark_perturbseq_streaming.py `
  --url data/raw/ReplogleWeissman2022_K562_gwps.h5ad `
  --checkpoint results/models/microglia_pvm_jepa_ema_var_expanded_balanced_e40/gene_jepa_epoch_030.pt `
  --target-genes HSP90B1 SOD1 BRD4 `
  --control-label control `
  --perturbation-col perturbation `
  --n-shuffles 5 `
  --max-ntc 100 `
  --max-ko-cells 50 `
  --shuffle-cells 10 `
  --counterfactual-mode input_erasure `
  --max-retries 3 `
  --retry-wait-seconds 2 `
  --out results/tables/perturbseq_streaming_validation.csv `
  --device auto
```

This is an engineering smoke test for the benchmark machinery. It should not be interpreted as Alzheimer's microglia validation.

Two counterfactual modes are available:

- `input_erasure`: mean-replace the target gene in control cells, then compare the context-encoder latent shift to the real CRISPR latent shift.
- `predictive`: mean-replace the target gene in control cells, pass the masked controls through the JEPA predictor, then compare that predictor-space shift to the real CRISPR latent shift.

The `predictive` mode is useful for testing whether the learned JEPA predictor contributes beyond local input sensitivity. The `--max-retries` and `--retry-wait-seconds` flags are mainly for remote HTTP-backed H5AD reads.

Run the Dräger/Kampmann iPSC-microglia DEG-vector benchmark:

```powershell
$env:PYTHONPATH = "src"
python scripts/benchmark_kampmann_deg_alignment.py `
  --counterfactual-mode input_erasure `
  --out results/tables/kampmann_deg_jepa_alignment_input_erasure.csv `
  --device auto

python scripts/benchmark_kampmann_deg_alignment.py `
  --counterfactual-mode predictive `
  --out results/tables/kampmann_deg_jepa_alignment_predictive.csv `
  --device auto
```

This benchmark uses `GSE178317` and the Dräger/Kampmann supplementary DEG table. It is more biologically relevant than K562, but it is not the same as a cell-level guide-assignment benchmark because GEO does not provide final per-cell sgRNA labels as a simple metadata table.

Generate the v1 internal SEA-AD biological hypothesis report:

```powershell
$env:PYTHONPATH = "src"
python scripts/generate_v1_biological_hypothesis_report.py
```

Outputs:

```text
results/reports/v1_microglia_biological_hypotheses.md
results/tables/v1_hypothesis_candidate_genes.csv
results/tables/v1_hypothesis_candidate_modules.csv
results/tables/v1_jepa_63_decode.csv
```

This report decodes `jepa_63`, joins gene/module digital knockouts with confounder-adjusted effects, and writes three concrete SEA-AD Microglia-PVM hypotheses. Treat these as model-implied hypotheses. They are useful for prioritization, but they are not experimental proof of causality.

Test whether `jepa_63` aligns with the donor-level UMAP geometry:

```powershell
$env:PYTHONPATH = "src"
python scripts/evaluate_jepa63_umap_alignment.py
```

Outputs:

```text
results/tables/jepa63_umap_alignment_metrics.csv
results/figures/jepa63_umap_alignment.svg
```

This answers whether the `jepa_63` latent axis is visible in the 2D JEPA UMAP projection. A strong association supports the interpretation that `jepa_63` contributes to the observed manifold geometry. It should not be read as proof that UMAP discovered a causal axis by itself.

Rank all JEPA latent dimensions by UMAP alignment:

```powershell
$env:PYTHONPATH = "src"
python scripts/rank_all_latent_umap_alignment.py
```

Outputs:

```text
results/tables/all_jepa_umap_variance_rankings.csv
results/reports/all_jepa_umap_variance_rankings.md
```

This gives the ceiling for the `jepa_63` result. If only a few latents have high R2, UMAP is dominated by those axes. If many latents have similar R2 values, the manifold is more distributed. The report joins each latent to its top module annotations so the geometry can be interpreted biologically.

Create the multi-panel JEPA representation overlay figure:

```powershell
$env:PYTHONPATH = "src"
python scripts/plot_jepa_representation_overlays.py
```

Outputs:

```text
results/figures/jepa_representation_overlays.svg
results/reports/jepa_representation_overlays.md
results/tables/jepa_representation_overlay_plot_data.csv
```

This figure uses one shared donor-level JEPA UMAP coordinate system and colors it by dominant latent axes, `jepa_63`, AT8/pTau, and NeuN. It is intended as a representation map with quantitative guardrails, not as causal proof.

Run the Grubman/GSE138852 zero-shot external cohort projection:

```powershell
$env:PYTHONPATH = "src"
python scripts/project_grubman_zero_shot.py `
  --mex-root data/external/grubman_gse138852 `
  --metadata data/external/grubman_gse138852/cell_metadata.csv `
  --cell-type-col cell_type `
  --donor-col patient_id `
  --condition-col condition `
  --checkpoint results/models/microglia_pvm_jepa_ema_var_expanded_balanced_e40/gene_jepa_epoch_030.pt `
  --local-h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad `
  --out-donor results/tables/grubman_zero_shot_donor_embeddings.csv `
  --out-summary results/tables/grubman_zero_shot_generalization.csv `
  --device auto
```

This freezes the SEA-AD JEPA encoder, aligns the public Grubman/GSE138852 genes to the SEA-AD JEPA input order, projects external cells, aggregates donor-level `jepa_63`, `jepa_34`, `jepa_46`, and `jepa_108`, then tests disease/control separation. It is an independent observational-cohort generalization test, not causal validation.

If a cell-type metadata file is not available yet, the script can be run with `--allow-all-cells` as a plumbing smoke test. Do not present that fallback as microglia-specific validation.

For the public GEO files downloaded from GSE138852, use the strict microglia labels in the covariates table:

```powershell
$env:PYTHONPATH = "src"
python scripts/project_grubman_zero_shot.py `
  --cell-type-col "oupSample.cellType" `
  --microglia-pattern "^mg$" `
  --donor-col sample_pool `
  --condition-col condition `
  --out-donor results/tables/grubman_zero_shot_sample_pool_embeddings.csv `
  --out-summary results/tables/grubman_zero_shot_generalization.csv `
  --device auto
```

The public Grubman covariates expose sample pools such as `AD1_AD2` and `Ct1_Ct2`, not clean individual donor IDs. Treat this as a zero-shot transfer smoke test.

Build JEPA v2 graph foundations:

```powershell
$env:PYTHONPATH = "src"
python scripts/build_string_graph.py

python scripts/build_wgcna_tom_graph.py `
  --top-edges 100000 `
  --power 6

python scripts/build_consensus_graph.py
```

Outputs:

```text
results/tables/v2_graph_string_*.csv
results/tables/v2_graph_wgcna_*.csv
results/tables/v2_graph_consensus_*.csv
results/reports/v2_graph_foundation.md
```

The recommended first v2 message-passing graph is the consensus union graph:

```text
results/tables/v2_graph_consensus_edge_index.csv
```

The strict both-supported graph is useful for interpretation and ablation, but it is too small to use as the main GNN topology:

```text
results/tables/v2_graph_consensus_both_edges.csv
```

Interpretation boundary: STRING is an external protein/functional association prior, and WGCNA/TOM is empirical co-expression topology. Neither graph is causal by itself.

Build the strict CELLxGENE healthy microglia Stage A anchor:

```powershell
conda activate sea-ad-jepa
conda install -n sea-ad-jepa -c conda-forge cellxgene-census

$env:PYTHONPATH = "src"
python scripts/build_cellxgene_healthy_anchor_strict.py `
  --max-cells 10000
```

Outputs:

```text
data/processed/v2_pretraining/cellxgene_normal_microglia_strict_jepa_aligned.h5ad
results/tables/cellxgene_normal_microglia_anchor_qc.csv
results/tables/cellxgene_normal_microglia_matched_genes.csv
results/tables/cellxgene_normal_microglia_missing_genes.csv
results/tables/cellxgene_normal_microglia_*_counts.csv
```

Default filter:

```text
disease == 'normal'
cell_type == 'microglial cell'
tissue_general == 'brain'
is_primary_data == True
suspension_type == 'nucleus'
assay == "10x 3' v3 transcription profiling"
```

This is intentionally strict. It sacrifices cell count to reduce the CELLxGENE batch-effect problem before v2 graph pretraining. If the strict query returns too few cells, relax one technical constraint at a time and record the changed filter in the QC table.

Audit JEPA v2 translational actionability:

```powershell
$env:PYTHONPATH = "src"
python scripts/audit_druggability_biomarkers.py
```

Outputs:

```text
results/tables/jepa_v2_translational_actionability_matrix.csv
results/tables/jepa_v2_translational_actionability_summary.csv
results/reports/jepa_v2_translational_actionability.md
```

This joins the JEPA gene space to Human Protein Atlas FDA-target, predicted membrane, and predicted secreted protein classes. Use these annotations after biological inference to prioritize practical interventions and biomarkers. Do not use them as a loss term during representation learning.

Validate Graph-JEPA v2 inputs:

```powershell
$env:PYTHONPATH = "src"
python scripts/check_graph_jepa_v2_inputs.py
```

After the CELLxGENE anchor is built, validate that its gene order matches the SEA-AD graph feature order:

```powershell
$env:PYTHONPATH = "src"
python scripts/check_graph_jepa_v2_inputs.py `
  --anchor-h5ad data/processed/v2_pretraining/cellxgene_normal_microglia_strict_jepa_aligned.h5ad
```

Graph-JEPA v2 optional training dependency:

```powershell
conda activate sea-ad-jepa
python -m pip install torch-geometric
```

The v2 model code keeps `torch_geometric` as an optional import so the rest of the repository can still run without it. Install it only before training the graph model.

Train Stage A Graph-JEPA on the CELLxGENE healthy microglia anchor:

```powershell
$env:PYTHONPATH = "src"
python scripts/train_graph_jepa_stage_a.py `
  --h5ad data/processed/v2_pretraining/cellxgene_normal_microglia_nucleus_relaxed_assay_jepa_aligned.h5ad `
  --edge-csv results/tables/v2_graph_string_edges_t700.csv `
  --epochs 5 `
  --batch-size 16 `
  --hidden-dim 128 `
  --gene-embed-dim 32 `
  --latent-dim 128 `
  --n-layers 2 `
  --variance-weight 1.0 `
  --lr 0.0001 `
  --mask-fraction 0.5 `
  --checkpoint-every 5 `
  --out-dir results/models/graph_jepa_stage_a_string_t700_rawvar_e5 `
  --log-dir runs/graph_jepa_stage_a_string_t700_rawvar_e5 `
  --device auto
```

This first Stage A run uses the lighter STRING t700 graph for development speed. The full STRING/WGCNA consensus graph is available for scale-up after the training loop is stable.

Expected corrected-loss behavior:

```text
variance loss should decrease over epochs
alignment should not instantly collapse to exactly zero
```

If variance stays near `~0.99` while alignment collapses near zero, verify that `jepa_loss` computes variance on raw latent vectors, not L2-normalized vectors.

### v2.2 Topology and Feature Dropout Smoke Test

Build external missing-gene masks from local public validation files:

```powershell
$env:PYTHONPATH = "src"
python scripts/build_external_gene_masks.py
```

Current masks:

```text
GSE174367 / Morabito: 33 missing Graph-JEPA genes
GSE138852 / Grubman: 331 missing Graph-JEPA genes
```

Run the v2.2 robustness smoke test on SEA-AD Microglia-PVM:

```powershell
$env:PYTHONPATH = "src"
python scripts/train_graph_jepa_stage_a.py `
  --h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad `
  --epochs 5 `
  --checkpoint-every 5 `
  --max-cells 2000 `
  --batch-size 8 `
  --random-gene-dropout 0.15 `
  --module-dropout-prob 0.10 `
  --external-mask-files `
      results/tables/external_gene_masks/gse174367_morabito_missing_genes.txt `
      results/tables/external_gene_masks/gse138852_grubman_missing_genes.txt `
  --external-mask-prob 0.25 `
  --edge-dropout 0.10 `
  --variance-gamma 0.02 `
  --variance-weight 0.20 `
  --covariance-weight 0.05 `
  --out-dir results/models/v2_2_topology_dropout_test `
  --log-dir runs/v2_2_topology_dropout_test `
  --history-csv results/tables/v2_2_topology_dropout_test_history.csv `
  --log-file results/logs/v2_2_topology_dropout_test.log `
  --device auto
```

Interpretation of the current smoke run:

```text
loss: 0.0988 -> 0.0063
effective dimensions: 9.4 -> 62.0
top singular-value ratio: 0.381 -> 0.117
```

This means the augmented run completed and the latent geometry expanded rather than collapsing into a single tube. The earlier default `variance_gamma = 1.0` was too high for raw graph-pooled latent scale and tripped the collapse guard.

Fast shared-topology Phase 1 pretraining:

The original PyG Stage A trainer is useful for architecture validation, but it is too slow for full-cohort topology-dropout pretraining because it materializes one graph per cell. Use the fast trainer for full Phase 1 runs. It batches expression as `[batch, genes]` and reuses one shared sparse gene adjacency.

Hydra-configured full run:

```powershell
$env:PYTHONPATH = "src"
python scripts/train_graph_jepa_stage_a_fast_hydra.py
```

Default config:

```text
configs/train/graph_jepa_stage_a_fast.yaml
```

The config preserves the successful gentle v2.2 augmentation recipe:

```text
random gene scalar dropout: 0.15
module scalar dropout probability: 0.10
external missing-gene mask probability: 0.25
DropEdge: 0.10
variance_gamma: 0.02
variance_weight: 0.20
covariance_weight: 0.05
batch_size: 256
epochs: 50
```

Useful Hydra overrides:

```powershell
python scripts/train_graph_jepa_stage_a_fast_hydra.py `
  epochs=1 `
  max_cells=2000 `
  batch_size=256 `
  out_dir=results/models/fast_smoke `
  log_dir=runs/fast_smoke `
  history_csv=results/tables/fast_smoke_history.csv `
  log_file=results/logs/fast_smoke.log
```

Current benchmark:

```text
2,000-cell smoke, batch 256:
  epoch time: 8.6 seconds
  throughput: 231.5 cells/sec

40,000-cell full epoch, batch 256:
  epoch time: 171-175 seconds
  throughput: 228-234 cells/sec

40,000-cell full epoch, batch 512:
  epoch time: 187.5 seconds
  throughput: 213.3 cells/sec
```

Use batch 256 as the current default. It is faster than batch 512 on the RTX 3080 Laptop GPU, likely because the larger graph-tensor batch increases memory pressure without improving throughput.

Run Stage B domain-adversarial alignment:

```powershell
$env:PYTHONPATH = "src"
python scripts/train_graph_jepa_stage_b_adversarial.py
```

Default config:

```text
configs/train/stage_b_adversarial.yaml
```

Purpose:

```text
SEA-AD + Rexach + Olah
  -> state-aware, balanced deterministic batches
  -> FastGraphGeneJEPA encoder
  -> JEPA loss preserves microglial structure
  -> Gradient Reversal Layer removes cohort/domain identity within comparable biology
```

Default Stage B alignment is intentionally conservative:

```text
alignment_state:
  reference_like

reference_like means:
  SEA-AD low / Not AD / reference-like cells
  Rexach normal cells
  Olah temporal-lobe-epilepsy / non-AD reference cells
```

This avoids the "forced overlap" failure mode. Do not globally adversarially
align all disease-loaded and non-disease cohorts unless the experiment is
explicitly designed to test that failure mode.

The Stage B script supports:

```text
freeze_mode:
  frozen
  partial_encoder
  full

alignment_state:
  reference_like
  disease_like
  unknown
  all

domain_loss_weight:
  default 0.1

GRL lambda:
  DANN warmup schedule
  lambda_p = 2 / (1 + exp(-10p)) - 1
```

Tiny smoke test:

```powershell
python scripts/train_graph_jepa_stage_b_adversarial.py `
  epochs=1 `
  max_steps_per_epoch=2 `
  per_domain_batch_size=8 `
  checkpoint_every=0 `
  out_dir=results/models/v2_2_stage_b_adversarial_smoke `
  log_dir=runs/v2_2_stage_b_adversarial_smoke `
  history_csv=results/tables/v2_2_stage_b_adversarial_smoke_history.csv `
  log_file=results/logs/v2_2_stage_b_adversarial_smoke.log
```

Interpretation guardrails:

```text
domain_accuracy:
  should move toward ~0.33 during successful three-domain alignment within the selected state

jepa_loss:
  should remain stable, otherwise alignment is erasing biology

effective_dims / top_sv_ratio:
  should stay healthy; do not accept a domain-confused collapsed manifold

centroid_l2_*:
  domain centroids should shrink gradually, not snap to zero
```

Do not treat Stage B as biological discovery. It is an adapter that should reduce cohort identity before Stage C pathology-aware disease-vector training.

Optional scheduler/covariance experiment inspired by foundation-scale GeneJEPA training:

```powershell
$env:PYTHONPATH = "src"
python scripts/train_graph_jepa_stage_a.py `
  --h5ad data/processed/v2_pretraining/cellxgene_normal_microglia_nucleus_relaxed_assay_jepa_aligned.h5ad `
  --edge-csv results/tables/v2_graph_string_edges_t700.csv `
  --epochs 30 `
  --batch-size 64 `
  --hidden-dim 128 `
  --gene-embed-dim 32 `
  --latent-dim 128 `
  --n-layers 2 `
  --variance-weight 1.0 `
  --covariance-weight 0.01 `
  --lr 0.0001 `
  --mask-start-fraction 0.2 `
  --mask-fraction 0.5 `
  --mask-warmup-epochs 10 `
  --ema-start-decay 0.992 `
  --ema-decay 0.9995 `
  --ema-warmup-epochs 10 `
  --gradient-clip-val 1.0 `
  --checkpoint-every 5 `
  --out-dir results/models/graph_jepa_stage_a_string_t700_sched_e30_b64 `
  --log-dir runs/graph_jepa_stage_a_string_t700_sched_e30_b64 `
  --device auto
```

Interpret this run cautiously. A good scheduled run should improve variance without letting covariance rise unchecked.

Build SEA-AD low-pathology Stage B anchor subsets:

```powershell
$env:PYTHONPATH = "src"
python scripts/build_sea_ad_low_pathology_anchor_subset.py `
  --anchor-column internal_low_pathology_anchor_relaxed `
  --out data/processed/v2_pretraining/sea_ad_low_pathology_microglia_pvm_relaxed_jepa_aligned.h5ad `
  --summary-out results/tables/sea_ad_low_pathology_microglia_pvm_relaxed_subset_summary.csv

python scripts/build_sea_ad_low_pathology_anchor_subset.py `
  --anchor-column internal_low_pathology_anchor_strict `
  --out data/processed/v2_pretraining/sea_ad_low_pathology_microglia_pvm_strict_jepa_aligned.h5ad `
  --summary-out results/tables/sea_ad_low_pathology_microglia_pvm_strict_subset_summary.csv
```

Extract frozen Stage A anchor coordinates:

```powershell
$env:PYTHONPATH = "src"
python scripts/extract_stage_a_frozen_anchors.py `
  --h5ad data/processed/v2_pretraining/cellxgene_normal_microglia_nucleus_relaxed_assay_jepa_aligned.h5ad `
  --anchor-type cellxgene_normal_microglia `
  --out-csv results/tables/stage_a_frozen_cellxgene_normal_microglia_coordinates.csv `
  --edge-csv results/tables/v2_graph_string_edges_t700.csv `
  --batch-size 64 `
  --device auto

python scripts/extract_stage_a_frozen_anchors.py `
  --h5ad data/processed/v2_pretraining/sea_ad_low_pathology_microglia_pvm_relaxed_jepa_aligned.h5ad `
  --anchor-type sea_ad_low_pathology_relaxed `
  --out-csv results/tables/stage_a_frozen_sea_ad_low_pathology_relaxed_coordinates.csv `
  --edge-csv results/tables/v2_graph_string_edges_t700.csv `
  --batch-size 64 `
  --device auto

python scripts/extract_stage_a_frozen_anchors.py `
  --h5ad data/processed/v2_pretraining/sea_ad_low_pathology_microglia_pvm_strict_jepa_aligned.h5ad `
  --anchor-type sea_ad_low_pathology_strict `
  --out-csv results/tables/stage_a_frozen_sea_ad_low_pathology_strict_coordinates.csv `
  --edge-csv results/tables/v2_graph_string_edges_t700.csv `
  --batch-size 64 `
  --device auto
```

Use the same edge graph that was used during Stage A training. For the current best checkpoint, that is:

```text
results/tables/v2_graph_string_edges_t700.csv
```

Run Stage B Graph-JEPA calibration with low-pathology SEA-AD anchors and CELLxGENE rehearsal:

```powershell
$env:PYTHONPATH = "src"
python scripts/train_graph_jepa_stage_b_rehearsal.py `
  --checkpoint results/models/graph_jepa_stage_a_string_t700_rawvar_e30/graph_jepa.pt `
  --primary-h5ad data/processed/v2_pretraining/sea_ad_low_pathology_microglia_pvm_relaxed_jepa_aligned.h5ad `
  --primary-coordinates results/tables/stage_a_frozen_sea_ad_low_pathology_relaxed_coordinates.csv `
  --rehearsal-h5ad data/processed/v2_pretraining/cellxgene_normal_microglia_nucleus_relaxed_assay_jepa_aligned.h5ad `
  --rehearsal-coordinates results/tables/stage_a_frozen_cellxgene_normal_microglia_coordinates.csv `
  --edge-csv results/tables/v2_graph_string_edges_t700.csv `
  --epochs 20 `
  --batch-size 16 `
  --rehearsal-batch-size 16 `
  --primary-rehearsal-weight 0.25 `
  --external-rehearsal-weight 0.25 `
  --lr 0.00005 `
  --checkpoint-every 5 `
  --out-dir results/models/graph_jepa_stage_b_low_pathology_rehearsal_e20 `
  --log-dir runs/graph_jepa_stage_b_low_pathology_rehearsal_e20 `
  --device auto
```

This is Stage B calibration, not disease fine-tuning. The goal is to adapt the Stage A healthy/reference geometry to SEA-AD's aged postmortem technical context while using CELLxGENE rehearsal to reduce catastrophic forgetting.

Extract Stage B coordinates and audit Stage A-to-B drift:

```powershell
$env:PYTHONPATH = "src"
python scripts/extract_stage_a_frozen_anchors.py `
  --checkpoint results/models/graph_jepa_stage_b_low_pathology_rehearsal_e20/graph_jepa_stage_b.pt `
  --h5ad data/processed/v2_pretraining/sea_ad_low_pathology_microglia_pvm_relaxed_jepa_aligned.h5ad `
  --anchor-type sea_ad_low_pathology_relaxed_stage_b `
  --out-csv results/tables/stage_b_rehearsal_sea_ad_low_pathology_relaxed_coordinates.csv `
  --edge-csv results/tables/v2_graph_string_edges_t700.csv `
  --batch-size 64 `
  --device auto

python scripts/extract_stage_a_frozen_anchors.py `
  --checkpoint results/models/graph_jepa_stage_b_low_pathology_rehearsal_e20/graph_jepa_stage_b.pt `
  --h5ad data/processed/v2_pretraining/cellxgene_normal_microglia_nucleus_relaxed_assay_jepa_aligned.h5ad `
  --anchor-type cellxgene_normal_microglia_stage_b `
  --out-csv results/tables/stage_b_rehearsal_cellxgene_normal_microglia_coordinates.csv `
  --edge-csv results/tables/v2_graph_string_edges_t700.csv `
  --batch-size 64 `
  --device auto

python scripts/audit_latent_coordinate_drift.py `
  --before results/tables/stage_a_frozen_sea_ad_low_pathology_relaxed_coordinates.csv `
  --after results/tables/stage_b_rehearsal_sea_ad_low_pathology_relaxed_coordinates.csv `
  --label sea_ad_low_pathology_relaxed_stage_a_to_b `
  --summary-out results/tables/stage_b_rehearsal_anchor_drift_summary.csv `
  --cell-out results/tables/stage_b_rehearsal_sea_ad_low_pathology_relaxed_drift.csv

python scripts/audit_latent_coordinate_drift.py `
  --before results/tables/stage_a_frozen_cellxgene_normal_microglia_coordinates.csv `
  --after results/tables/stage_b_rehearsal_cellxgene_normal_microglia_coordinates.csv `
  --label cellxgene_normal_microglia_stage_a_to_b `
  --summary-out results/tables/stage_b_rehearsal_anchor_drift_summary.csv `
  --cell-out results/tables/stage_b_rehearsal_cellxgene_normal_microglia_drift.csv
```

High cosine similarity between Stage A and Stage B coordinates means calibration preserved the healthy/reference anchor geometry. Low similarity would indicate catastrophic forgetting or overly aggressive calibration.

Run Stage C Graph-JEPA disease-vector training with three-stream rehearsal:

```powershell
$env:PYTHONPATH = "src"
python scripts/train_graph_jepa_stage_c_disease.py `
  --checkpoint results/models/graph_jepa_stage_b_low_pathology_rehearsal_e20/graph_jepa_stage_b.pt `
  --disease-h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad `
  --sea-anchor-h5ad data/processed/v2_pretraining/sea_ad_low_pathology_microglia_pvm_relaxed_jepa_aligned.h5ad `
  --sea-anchor-coordinates results/tables/stage_b_rehearsal_sea_ad_low_pathology_relaxed_coordinates.csv `
  --cellxgene-anchor-h5ad data/processed/v2_pretraining/cellxgene_normal_microglia_nucleus_relaxed_assay_jepa_aligned.h5ad `
  --cellxgene-anchor-coordinates results/tables/stage_b_rehearsal_cellxgene_normal_microglia_coordinates.csv `
  --edge-csv results/tables/v2_graph_string_edges_t700.csv `
  --epochs 20 `
  --disease-batch-size 16 `
  --sea-anchor-batch-size 8 `
  --cellxgene-anchor-batch-size 8 `
  --sea-rehearsal-weight 0.5 `
  --cellxgene-rehearsal-weight 0.5 `
  --lr 0.00002 `
  --checkpoint-every 5 `
  --out-dir results/models/graph_jepa_stage_c_disease_rehearsal_e20 `
  --log-dir runs/graph_jepa_stage_c_disease_rehearsal_e20 `
  --history-out results/tables/graph_jepa_stage_c_disease_rehearsal_history.csv `
  --device auto
```

For a quick mechanics check, cap each epoch:

```powershell
$env:PYTHONPATH = "src"
python scripts/train_graph_jepa_stage_c_disease.py `
  --epochs 2 `
  --max-steps-per-epoch 8 `
  --checkpoint-every 0 `
  --out-dir results/models/graph_jepa_stage_c_disease_rehearsal_smoke `
  --log-dir runs/graph_jepa_stage_c_disease_rehearsal_smoke `
  --history-out results/tables/graph_jepa_stage_c_disease_rehearsal_smoke_history.csv `
  --device auto
```

Stage C is where the disease manifold is allowed to move. Do not interpret a Stage C run until both anchors are re-extracted and audited for Stage B-to-C drift.

After Stage C, extract anchors, audit drift, and evaluate donor-level pathology:

```powershell
$env:PYTHONPATH = "src"
python scripts/extract_stage_a_frozen_anchors.py `
  --checkpoint results/models/graph_jepa_stage_c_disease_rehearsal_e20/graph_jepa_stage_c.pt `
  --h5ad data/processed/v2_pretraining/sea_ad_low_pathology_microglia_pvm_relaxed_jepa_aligned.h5ad `
  --anchor-type sea_ad_low_pathology_relaxed_stage_c `
  --out-csv results/tables/stage_c_rehearsal_sea_ad_low_pathology_relaxed_coordinates.csv `
  --edge-csv results/tables/v2_graph_string_edges_t700.csv `
  --batch-size 64 `
  --device auto

python scripts/extract_stage_a_frozen_anchors.py `
  --checkpoint results/models/graph_jepa_stage_c_disease_rehearsal_e20/graph_jepa_stage_c.pt `
  --h5ad data/processed/v2_pretraining/cellxgene_normal_microglia_nucleus_relaxed_assay_jepa_aligned.h5ad `
  --anchor-type cellxgene_normal_microglia_stage_c `
  --out-csv results/tables/stage_c_rehearsal_cellxgene_normal_microglia_coordinates.csv `
  --edge-csv results/tables/v2_graph_string_edges_t700.csv `
  --batch-size 64 `
  --device auto

python scripts/audit_latent_coordinate_drift.py `
  --before results/tables/stage_b_rehearsal_sea_ad_low_pathology_relaxed_coordinates.csv `
  --after results/tables/stage_c_rehearsal_sea_ad_low_pathology_relaxed_coordinates.csv `
  --label sea_ad_low_pathology_relaxed_stage_b_to_c `
  --summary-out results/tables/stage_c_rehearsal_anchor_drift_summary.csv `
  --cell-out results/tables/stage_c_rehearsal_sea_ad_low_pathology_relaxed_drift.csv

python scripts/audit_latent_coordinate_drift.py `
  --before results/tables/stage_b_rehearsal_cellxgene_normal_microglia_coordinates.csv `
  --after results/tables/stage_c_rehearsal_cellxgene_normal_microglia_coordinates.csv `
  --label cellxgene_normal_microglia_stage_b_to_c `
  --summary-out results/tables/stage_c_rehearsal_anchor_drift_summary.csv `
  --cell-out results/tables/stage_c_rehearsal_cellxgene_normal_microglia_drift.csv
```

Extract full SEA-AD Stage C coordinates and aggregate them to donor embeddings:

```powershell
$env:PYTHONPATH = "src"
python scripts/extract_stage_a_frozen_anchors.py `
  --checkpoint results/models/graph_jepa_stage_c_disease_rehearsal_e20/graph_jepa_stage_c.pt `
  --h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad `
  --anchor-type sea_ad_microglia_pvm_stage_c_all `
  --out-csv results/tables/stage_c_rehearsal_sea_ad_microglia_pvm_all_coordinates.csv `
  --edge-csv results/tables/v2_graph_string_edges_t700.csv `
  --batch-size 64 `
  --device auto

python scripts/aggregate_latent_coordinates_by_donor.py `
  --coordinates results/tables/stage_c_rehearsal_sea_ad_microglia_pvm_all_coordinates.csv `
  --out results/tables/stage_c_rehearsal_sea_ad_microglia_pvm_donor_embeddings.csv
```

Evaluate Stage C donor embeddings:

```powershell
$env:PYTHONPATH = "src"
python scripts/run_pseudobulk_baseline.py `
  --features results/tables/stage_c_rehearsal_sea_ad_microglia_pvm_donor_embeddings.csv `
  --out results/tables/stage_c_rehearsal_donor_embedding_ridge_pathology.csv `
  --max-genes 0 `
  --device auto

python scripts/evaluate_latent_spaces.py `
  --jepa results/tables/stage_c_rehearsal_sea_ad_microglia_pvm_donor_embeddings.csv `
  --metrics-out results/tables/stage_c_latent_space_evaluation_metrics.csv `
  --embedding-out results/tables/stage_c_latent_space_umap_coordinates.csv `
  --figure-out results/figures/stage_c_latent_space_pca_vs_jepa_umap_at8_neun.svg `
  --html-out results/figures/stage_c_latent_space_pca_vs_jepa_umap_at8_neun.html
```

Evaluate intermediate Stage C checkpoints:

```powershell
$env:PYTHONPATH = "src"
foreach ($e in 5,10,15) {
  $epoch = "{0:D3}" -f $e
  python scripts/extract_stage_a_frozen_anchors.py `
    --checkpoint results/models/graph_jepa_stage_c_disease_rehearsal_e20/graph_jepa_stage_c_epoch_$epoch.pt `
    --h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad `
    --anchor-type sea_ad_microglia_pvm_stage_c_epoch_$epoch `
    --out-csv results/tables/stage_c_epoch_${epoch}_sea_ad_microglia_pvm_all_coordinates.csv `
    --edge-csv results/tables/v2_graph_string_edges_t700.csv `
    --batch-size 64 `
    --device auto

  python scripts/aggregate_latent_coordinates_by_donor.py `
    --coordinates results/tables/stage_c_epoch_${epoch}_sea_ad_microglia_pvm_all_coordinates.csv `
    --out results/tables/stage_c_epoch_${epoch}_sea_ad_microglia_pvm_donor_embeddings.csv

  python scripts/run_pseudobulk_baseline.py `
    --features results/tables/stage_c_epoch_${epoch}_sea_ad_microglia_pvm_donor_embeddings.csv `
    --out results/tables/stage_c_epoch_${epoch}_donor_embedding_ridge_pathology.csv `
    --max-genes 0 `
    --device auto

  python scripts/evaluate_latent_spaces.py `
    --jepa results/tables/stage_c_epoch_${epoch}_sea_ad_microglia_pvm_donor_embeddings.csv `
    --metrics-out results/tables/stage_c_epoch_${epoch}_latent_space_evaluation_metrics.csv `
    --embedding-out results/tables/stage_c_epoch_${epoch}_latent_space_umap_coordinates.csv `
    --figure-out results/figures/stage_c_epoch_${epoch}_latent_space_pca_vs_jepa_umap_at8_neun.svg `
    --html-out results/figures/stage_c_epoch_${epoch}_latent_space_pca_vs_jepa_umap_at8_neun.html
}

python scripts/summarize_stage_c_checkpoint_evaluation.py
```

Use this before launching another Stage C run. If an early checkpoint beats the final checkpoint, disease geometry is being learned early and then washed out by the current objective.

Run elastic Stage C rehearsal with bungee-style anchor preservation:

```powershell
$env:PYTHONPATH = "src"
python scripts/train_graph_jepa_stage_c_disease.py `
  --checkpoint results/models/graph_jepa_stage_b_low_pathology_rehearsal_e20/graph_jepa_stage_b.pt `
  --disease-h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad `
  --sea-anchor-h5ad data/processed/v2_pretraining/sea_ad_low_pathology_microglia_pvm_relaxed_jepa_aligned.h5ad `
  --sea-anchor-coordinates results/tables/stage_b_rehearsal_sea_ad_low_pathology_relaxed_coordinates.csv `
  --cellxgene-anchor-h5ad data/processed/v2_pretraining/cellxgene_normal_microglia_nucleus_relaxed_assay_jepa_aligned.h5ad `
  --cellxgene-anchor-coordinates results/tables/stage_b_rehearsal_cellxgene_normal_microglia_coordinates.csv `
  --edge-csv results/tables/v2_graph_string_edges_t700.csv `
  --epochs 10 `
  --disease-batch-size 16 `
  --sea-anchor-batch-size 8 `
  --cellxgene-anchor-batch-size 8 `
  --sea-rehearsal-weight 0.05 `
  --cellxgene-rehearsal-weight 0.05 `
  --rehearsal-loss-mode cosine_softplus_margin `
  --rehearsal-margin 0.95 `
  --rehearsal-temperature 100 `
  --lr 0.00002 `
  --checkpoint-every 5 `
  --out-dir results/models/graph_jepa_stage_c_elastic_w005_e10 `
  --log-dir runs/graph_jepa_stage_c_elastic_w005_e10 `
  --history-out results/tables/graph_jepa_stage_c_elastic_w005_e10_history.csv `
  --device auto
```

The elastic run logs additional telemetry:

```text
sea_anchor_cosine
cellxgene_anchor_cosine
disease_to_cellxgene_centroid_l2
disease_variance_spread
disease_effective_dims
disease_top_sv_ratio
```

Interpretation guardrail: increasing disease-to-anchor distance without increasing effective dimensionality indicates a narrow disease tube, not a rich local pathology manifold.

Run elastic Stage C with a small disease-covariance tube-busting diagnostic:

```powershell
$env:PYTHONPATH = "src"
python scripts/train_graph_jepa_stage_c_disease.py `
  --checkpoint results/models/graph_jepa_stage_b_low_pathology_rehearsal_e20/graph_jepa_stage_b.pt `
  --disease-h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad `
  --sea-anchor-h5ad data/processed/v2_pretraining/sea_ad_low_pathology_microglia_pvm_relaxed_jepa_aligned.h5ad `
  --sea-anchor-coordinates results/tables/stage_b_rehearsal_sea_ad_low_pathology_relaxed_coordinates.csv `
  --cellxgene-anchor-h5ad data/processed/v2_pretraining/cellxgene_normal_microglia_nucleus_relaxed_assay_jepa_aligned.h5ad `
  --cellxgene-anchor-coordinates results/tables/stage_b_rehearsal_cellxgene_normal_microglia_coordinates.csv `
  --edge-csv results/tables/v2_graph_string_edges_t700.csv `
  --epochs 10 `
  --disease-batch-size 16 `
  --sea-anchor-batch-size 8 `
  --cellxgene-anchor-batch-size 8 `
  --sea-rehearsal-weight 0.05 `
  --cellxgene-rehearsal-weight 0.05 `
  --rehearsal-loss-mode cosine_softplus_margin `
  --rehearsal-margin 0.95 `
  --rehearsal-temperature 100 `
  --disease-covariance-weight 0.01 `
  --lr 0.00002 `
  --checkpoint-every 5 `
  --out-dir results/models/graph_jepa_stage_c_elastic_cov001_e10 `
  --log-dir runs/graph_jepa_stage_c_elastic_cov001_e10 `
  --history-out results/tables/graph_jepa_stage_c_elastic_cov001_e10_history.csv `
  --device auto
```

This is a diagnostic, not a default training recipe. If disease covariance lowers `disease_top_sv_ratio` but also collapses `disease_to_cellxgene_centroid_l2` and `disease_variance_spread`, the covariance pressure is too blunt or too early.

Run the Stage C fine-tuning sweep:

```powershell
$env:PYTHONPATH = "src"
python scripts/sweep_stage_c_finetuning.py `
  --preset coarse `
  --epochs 10 `
  --checkpoint-epochs 005 010 `
  --device auto `
  --out results/tables/stage_c_finetuning_sweep_summary.csv

python scripts/sweep_stage_c_finetuning.py `
  --preset fine_tight `
  --epochs 5 `
  --checkpoint-epochs 005 `
  --device auto `
  --out results/tables/stage_c_finetuning_fine_tight_summary.csv

python scripts/sweep_stage_c_finetuning.py `
  --preset upgrade_fine `
  --epochs 5 `
  --checkpoint-epochs 005 `
  --device auto `
  --out results/tables/stage_c_upgrade_fine_summary.csv
```

Combine and inspect the leaderboards:

```powershell
$files = @(
  "results/tables/stage_c_finetuning_sweep_summary.csv",
  "results/tables/stage_c_finetuning_fine_tight_summary.csv",
  "results/tables/stage_c_finetuning_fine_loose_summary.csv",
  "results/tables/stage_c_finetuning_fine_narrow_summary.csv",
  "results/tables/stage_c_finetuning_fine_bridge_summary.csv",
  "results/tables/stage_c_finetuning_fine_safety_summary.csv",
  "results/tables/stage_c_upgrade_sweep_summary.csv",
  "results/tables/stage_c_upgrade_fine_summary.csv"
)
$frames = foreach ($f in $files) { if (Test-Path $f) { Import-Csv $f } }
$frames |
  Sort-Object {[double]$_.composite_score} -Descending |
  Export-Csv -NoTypeInformation results/tables/stage_c_finetuning_combined_leaderboard.csv
Import-Csv results/tables/stage_c_finetuning_combined_leaderboard.csv |
  Select-Object -First 12 |
  Format-Table -AutoSize
```

Current recommended Stage C candidate:

```text
run: upgrade_fine_08_r0045_cov0005_pc0075
checkpoint: epoch 5
SEA/CELLxGENE rehearsal weight: 0.0045
disease covariance weight: 0.0005
pathology contrastive weight: 0.075
```

This setting is intentionally elastic and anchor-safe. It uses projection-head disease geometry and pathology-neighborhood organization while preserving both anchors above the 0.95 cosine safety boundary.

Decode v2.1 biology from the selected checkpoint:

```powershell
$env:PYTHONPATH = "src"

python scripts/decode_graph_latent_gene_weights.py `
  --checkpoint results/models/stage_c_upgrade_fine_08_r0045_cov0005_pc0075/graph_jepa_stage_c_epoch_005.pt `
  --model-label upgrade_fine_08 `
  --latent-dims 120 26 30 94 71 63 1 57 103 100 125 38 107 `
  --max-cells 2048 `
  --batch-size 16 `
  --out results/tables/v2_1_upgrade_fine_08_latent_gene_attributions.csv `
  --device auto

python scripts/decode_graph_latent_gene_weights.py `
  --checkpoint results/models/stage_c_fine_bridge_06_r0045_cov0005/graph_jepa_stage_c_epoch_005.pt `
  --model-label fine_bridge_06 `
  --latent-dims 120 26 30 94 71 63 1 57 103 100 125 38 107 `
  --max-cells 2048 `
  --batch-size 16 `
  --out results/tables/v2_1_fine_bridge_06_latent_gene_attributions.csv `
  --device auto
```

Run Graph-JEPA predictor Jacobian maps:

```powershell
$env:PYTHONPATH = "src"

python scripts/causal_graph_latent_jacobian.py `
  --checkpoint results/models/stage_c_upgrade_fine_08_r0045_cov0005_pc0075/graph_jepa_stage_c_epoch_005.pt `
  --model-label upgrade_fine_08 `
  --max-cells 4096 `
  --batch-size 32 `
  --jacobian-batch-size 128 `
  --matrix-out results/tables/v2_1_upgrade_fine_08_latent_jacobian_matrix.csv `
  --edges-out results/tables/v2_1_upgrade_fine_08_latent_jacobian_top_edges.csv `
  --annotations-out results/tables/v2_1_upgrade_fine_08_latent_jacobian_module_annotations.csv `
  --device auto

python scripts/causal_graph_latent_jacobian.py `
  --checkpoint results/models/stage_c_fine_bridge_06_r0045_cov0005/graph_jepa_stage_c_epoch_005.pt `
  --model-label fine_bridge_06 `
  --max-cells 4096 `
  --batch-size 32 `
  --jacobian-batch-size 128 `
  --matrix-out results/tables/v2_1_fine_bridge_06_latent_jacobian_matrix.csv `
  --edges-out results/tables/v2_1_fine_bridge_06_latent_jacobian_top_edges.csv `
  --annotations-out results/tables/v2_1_fine_bridge_06_latent_jacobian_module_annotations.csv `
  --device auto
```

Run the v2.1 AT8 counterfactual screen and build the hypothesis report:

```powershell
$env:PYTHONPATH = "src"

python scripts/graph_counterfactual_knockout.py `
  --checkpoint results/models/stage_c_upgrade_fine_08_r0045_cov0005_pc0075/graph_jepa_stage_c_epoch_005.pt `
  --model-label upgrade_fine_08 `
  --mode module `
  --modules complement lipid_metabolism lysosome_phagocytosis homeostatic_microglia vascular_barrier_myeloid plaque_response disease_associated_microglia inflammatory_signaling antigen_presentation senescence_stress `
  --intervention global_mean `
  --perturbation-direction suppressor `
  --target "percent AT8 positive area_Grey matter" `
  --max-cells 12000 `
  --batch-size 64 `
  --out results/tables/v2_1_upgrade_fine_08_module_counterfactual_at8.csv `
  --donor-out results/tables/v2_1_upgrade_fine_08_module_counterfactual_at8_by_donor.csv `
  --device auto

python scripts/graph_counterfactual_knockout.py `
  --checkpoint results/models/stage_c_upgrade_fine_08_r0045_cov0005_pc0075/graph_jepa_stage_c_epoch_005.pt `
  --model-label upgrade_fine_08 `
  --mode gene `
  --genes CSF1R TLR2 BCL2 CD4 P2RY12 APP APOE CD74 PLCG2 MAPK1 ROCK1 HSP90AA1 UGCG STAT3 HIF1A GRB2 RHOA CTSD P2RY13 CX3CR1 F13A1 CHI3L1 DRAM1 PTPRG `
  --intervention global_mean `
  --perturbation-direction suppressor `
  --target "percent AT8 positive area_Grey matter" `
  --max-cells 12000 `
  --batch-size 64 `
  --out results/tables/v2_1_upgrade_fine_08_gene_counterfactual_at8.csv `
  --donor-out results/tables/v2_1_upgrade_fine_08_gene_counterfactual_at8_by_donor.csv `
  --device auto

python scripts/build_v21_hypothesis_report.py
```

Graph counterfactual scoring now includes disease-axis projection metrics:

```text
disease_axis_reversal:
  positive means the perturbation moves cells backward along the selected
  pathology axis

orthogonal_shift:
  off-axis movement, useful for flagging nonspecific coordinate scrambling

orthogonal_to_axis_ratio:
  high values mean the perturbation moves mostly somewhere else, not cleanly
  backward along disease
```

Run an agonist/rescue stress test by switching the intervention:

```powershell
python scripts/graph_counterfactual_knockout.py `
  --checkpoint results/models/stage_c_upgrade_fine_08_r0045_cov0005_pc0075/graph_jepa_stage_c_epoch_005.pt `
  --model-label upgrade_fine_08 `
  --mode gene `
  --genes P2RY12 CX3CR1 TREM2 APOE `
  --intervention p99 `
  --perturbation-direction agonist `
  --target "percent AT8 positive area_Grey matter" `
  --max-cells 12000 `
  --batch-size 64 `
  --out results/tables/v2_1_upgrade_fine_08_gene_counterfactual_at8_agonist_p99.csv `
  --donor-out results/tables/v2_1_upgrade_fine_08_gene_counterfactual_at8_agonist_p99_by_donor.csv `
  --axis-cell-out results/tables/v2_1_upgrade_fine_08_gene_counterfactual_at8_agonist_p99_cells.csv `
  --device auto
```

Interpretation:

```text
suppressor hits:
  CRISPRi, shRNA, inhibitors, antibody blockade

agonist hits:
  overexpression, rescue plasmids, activating therapeutics
```

Outputs:

```text
results/tables/v2_1_ranked_target_matrix.csv
results/reports/v2_1_microglia_biological_hypotheses.md
```

Extend the same counterfactual screen across the remaining major targets by reusing the commands above and changing:

```text
target -> output suffix

"percent 6e10 positive area_Grey matter" -> 6e10
"percent GFAP positive area_Grey matter" -> gfap
"percent Iba1 positive area_Grey matter" -> iba1
"percent NeuN positive area_Grey matter" -> neun
```

Then summarize multi-target stability:

```powershell
$env:PYTHONPATH = "src"
python scripts/summarize_v21_multitarget_counterfactuals.py
```

Outputs:

```text
results/tables/v2_1_multitarget_module_counterfactual_long.csv
results/tables/v2_1_multitarget_gene_counterfactual_long.csv
results/tables/v2_1_multitarget_module_counterfactual_summary.csv
results/tables/v2_1_multitarget_gene_counterfactual_summary.csv
results/reports/v2_1_multitarget_counterfactual_stability.md
results/reports/v2_1_named_biological_programs.md
```

Run artifact-control validation before accepting ranked targets:

```powershell
$env:PYTHONPATH = "src"
python scripts/validate_v21_target_matrix.py `
  --top-n 10 `
  --within-state-top-n 5 `
  --max-cells 12000 `
  --batch-size 64 `
  --device auto
```

Outputs:

```text
results/tables/v2_1_target_validation_alien_cell_check.csv
results/tables/v2_1_target_validation_covariate_correlations.csv
results/tables/v2_1_target_validation_covariate_flags.csv
results/tables/v2_1_target_validation_within_state_check.csv
results/tables/v2_1_target_validation_validated_target_matrix.csv
results/tables/v2_1_target_validation_report.md
```

Audit SEA-AD low-pathology donors as internal v2 anchors:

```powershell
$env:PYTHONPATH = "src"
python scripts/audit_sea_ad_control_anchors.py
```

Outputs:

```text
results/tables/sea_ad_low_pathology_anchor_audit_donors.csv
results/tables/sea_ad_low_pathology_anchor_audit_summary.csv
results/reports/sea_ad_low_pathology_anchor_audit.md
```

Use this audit to separate:

- low-pathology internal reference donors
- disease-deviation donors
- donors with insufficient Microglia-PVM cell counts

Terminology matters: SEA-AD low-pathology donors are not pristine healthy controls. They are aged postmortem reference donors. For v2, use them for matched internal calibration and add external healthy/normal microglia for broad pretraining.

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

## 8. Build CELLxGENE External Adapters

Use this step to prepare public CELLxGENE cohorts for v2.2 domain-alignment experiments. These adapters do not alter the SEA-AD Graph-JEPA gene order or master graph topology.

Raw CELLxGENE files are kept local and ignored by Git:

```text
data/external/cellxgene/rexach_cross_dementia.h5ad
data/external/cellxgene/olah_live_microglia.h5ad
```

Current public CELLxGENE assets used:

```text
Rexach cross-dementia:
  https://datasets.cellxgene.cziscience.com/aa87f914-07e0-48aa-b915-8de906c95baf.h5ad

Olah live human microglia:
  https://datasets.cellxgene.cziscience.com/dddc40f4-4969-4eb6-b5e9-b30f03ddd672.h5ad
```

Build aligned microglia-only H5AD adapters:

```powershell
$env:PYTHONPATH = "src"
python scripts/build_cellxgene_adapters.py `
  --rexach-h5ad data/external/cellxgene/rexach_cross_dementia.h5ad `
  --olah-h5ad data/external/cellxgene/olah_live_microglia.h5ad
```

The adapter filters for CELLxGENE microglia using:

```text
cell_type == "microglial cell"
or
cell_type_ontology_term_id == "CL:0000129"
```

It then aligns each cohort to the exact 2,957-gene Graph-JEPA input order. Missing genes are zero-filled, because the v2.2 topology-dropout training explicitly teaches the encoder to handle structural feature absence.

Expected aligned outputs:

```text
data/processed/v2_alignment/rexach_cross_dementia_microglia_jepa_aligned.h5ad
data/processed/v2_alignment/olah_live_microglia_microglia_jepa_aligned.h5ad
```

Expected tracked summaries:

```text
results/tables/v2_2_cellxgene_alignment_stats.csv
results/reports/v2_2_cellxgene_alignment_stats.md
```

Current adapter result:

```text
Rexach cross-dementia:
  microglia: 21,575
  donors: 40
  matched genes: 2,837 / 2,957
  overlap: 95.9%

Olah live microglia:
  microglia: 16,099
  donors: 17
  matched genes: 2,846 / 2,957
  overlap: 96.2%
```

Use these aligned objects for the next domain-adversarial/adaptor phase. Do not treat them as final held-out biological validation if they are used during model alignment.

## 9. Fast Stage C Disease Training

The fast Stage C disease trainer fine-tunes the Stage B encoder while maintaining geometry safety gates and rehearsal anchors. SupCon remains available as an experimental mode, but the active default is now a joint pathology regression head because the SupCon runs produced near-uniform contrastive neighborhoods without improving donor-level pathology geometry.

Hydra-configured training:

```powershell
$env:PYTHONPATH = "src"
python scripts/train_fast_graph_jepa_stage_c_disease_hydra.py
```

Default config:

```text
configs/train/fast_stage_c_supcon.yaml
```

Key parameters in the default config:

```text
loss: joint pathology regression head
pathology_loss_mode: regression
pathology_regression_loss: huber
pathology_head_lr: 0.001
pathology_contrastive_weight: 1.0
pathology_contrastive_temperature: 2.0
pathology_latent_temperature: 0.1

learning rates:
  base_lr: 1e-6 (graph reader)
  lr: 2e-5 (head/predictor)

rehearsal anchors:
  sea_rehearsal_weight: 0.0045
  cellxgene_rehearsal_weight: 0.0045
  rehearsal_margin: 0.85

safety gates:
  min_embedding_effective_dims: 50.0
  max_embedding_top_sv_ratio: 0.2
  safety_gate_start_epoch: 6
```

Useful Hydra overrides:

```powershell
python scripts/train_fast_graph_jepa_stage_c_disease_hydra.py \
  epochs=10 \
  base_lr=0.00001 \
  lr=0.0001 \
  out_dir=results/models/fast_stage_c_experiment \
  log_dir=runs/fast_stage_c_experiment \
  history_out=results/tables/fast_stage_c_experiment_history.csv
```

Direct argparse invocation (without Hydra):

```powershell
$env:PYTHONPATH = "src"
conda run -n sea-ad-jepa python scripts/train_fast_graph_jepa_stage_c_disease.py `
  --checkpoint results/models/v2_2_stage_b_adversarial/stage_b_adversarial.pt `
  --pathology-loss-mode regression `
  --pathology-regression-loss huber `
  --pathology-head-lr 0.001 `
  --base-lr 1e-6 `
  --lr 2e-5 `
  --sea-rehearsal-weight 0.0045 `
  --cellxgene-rehearsal-weight 0.0045 `
  --pathology-contrastive-weight 1.0 `
  --pathology-contrastive-temperature 2.0 `
  --pathology-latent-temperature 0.1 `
  --epochs 10 `
  --checkpoint-every 5 `
  --out-dir results/models/v2_2_fast_stage_c_regression `
  --log-dir runs/v2_2_fast_stage_c_regression `
  --history-out results/tables/v2_2_fast_stage_c_regression_history.csv
```

### Important: Pathology Objective Lessons

The original fast Stage C trainer used `base_lr=1e-6` and `head_lr=2e-5` (a 20x gap). This caused the fast-moving head to absorb the SupCon gradients entirely, leaving the context encoder frozen solid. The Ridge Spearman numbers were numerically identical across Stage B, dead-gradient smoke, and SupCon smoke checkpoints.

An unfrozen SupCon run with stronger base updates moved the encoder, but it damaged geometry. A gentler run partially recovered dimensions but still did not clearly improve pathology geometry. The current pivot is to train a small supervised regression head from the unmasked context-encoder embedding. This gives a direct continuous-label signal without forcing continuous pathology into a classification-style contrastive objective.

The first regression-head smoke test showed the head can learn: Huber pathology loss dropped from `0.756` to about `0.39` while epoch-sampled training geometry remained safe. However, the full-dataset evaluator still reported weaker global geometry (`effective_dims=40.62`, `top_sv_ratio=0.268`), so future runs should use full-dataset evaluation as the safety gate, not only 20-step epoch telemetry.

## 10. Evaluate Fast Stage C Checkpoints

Run the embedding extractor and pathology evaluator:

```powershell
$env:PYTHONPATH = "src"
conda run -n sea-ad-jepa python scripts/evaluate_fast_stage_c.py `
  --checkpoint <path_to_checkpoint.pt> `
  --label "descriptive label"
```

The evaluator:
- Loads a `FastGraphGeneJEPA` checkpoint
- Encodes all ~40,000 SEA-AD Microglia-PVM cells through the frozen context encoder
- Pools to donor level (mean aggregation)
- Scores against all 5 IHC pathology targets using Ridge (linear) and distance-weighted cosine kNN (manifold)
- Appends results to `results/tables/v2_2_fast_stage_c_evaluation.csv`

Default targets:

```text
percent AT8 positive area_Grey matter
percent NeuN positive area_Grey matter
percent GFAP positive area_Grey matter
percent Iba1 positive area_Grey matter
percent 6e10 positive area_Grey matter
```

### Fast Stage C Evaluation Results (2026-06-14)

Three-checkpoint comparison ladder:

```text
Checkpoint                              | AT8 Ridge | AT8 kNN | NeuN Ridge | NeuN kNN | GFAP Ridge | GFAP kNN | Iba1 Ridge | Iba1 kNN | 6e10 Ridge | 6e10 kNN | Eff Dims
Stage B adapter (no disease)            |     0.127 |   0.047 |      0.267 |    0.028 |     -0.257 |   -0.121 |      0.185 |    0.044 |     -0.163 |   -0.033 |    41.00
Safety smoke (dead pathology loss)      |     0.127 |   0.100 |      0.266 |    0.231 |     -0.256 |   -0.204 |      0.161 |   -0.007 |     -0.162 |    0.028 |    39.70
SupCon smoke (active loss, frozen enc)  |     0.127 |  -0.152 |      0.266 |    0.095 |     -0.256 |   -0.264 |      0.161 |    0.035 |     -0.162 |   -0.060 |    39.69
Regression head smoke e8                |     0.127 |   0.050 |      0.266 |    0.084 |     -0.256 |    0.158 |      0.187 |    0.122 |     -0.163 |  -0.112 |    40.62
```

Interpretation:

- Ridge Spearman was identical across all three checkpoints, proving the context encoder did not move.
- kNN degraded under SupCon because the frozen encoder could not follow the head's contortions.
- This is the gradient absorption failure: the 20x LR gap let the head absorb all SupCon gradients without teaching the encoder anything.
- The regression-head smoke learned a supervised pathology loss and improved GFAP/Iba1 kNN, but did not improve AT8/NeuN donor geometry. This is a useful diagnostic, not the final Stage C solution.

## 11. Train Frozen-Backbone Pathology Heads

The preferred Stage C readout is now a frozen Graph-JEPA backbone with a supervised pathology head. This follows the foundation-model pattern: preserve the biological representation and train small heads to decode downstream clinical axes.

Run the linear-vs-MLP probe:

```powershell
$env:PYTHONPATH = "src"
conda run -n sea-ad-jepa python scripts/train_pathology_mlp_head.py `
  --checkpoint results/models/v2_2_stage_b_adversarial/stage_b_adversarial.pt `
  --heads linear mlp `
  --epochs 500 `
  --hidden-dim 64 `
  --dropout 0.15 `
  --lr 0.001 `
  --weight-decay 0.001 `
  --out-dir results/models/pathology_heads_stage_b_lp `
  --metrics-out results/tables/pathology_head_stage_b_lp_metrics.csv `
  --predictions-out results/tables/pathology_head_stage_b_lp_oof_predictions.csv `
  --donor-embeddings-out results/tables/pathology_head_stage_b_frozen_donor_embeddings.csv
```

Current result:

```text
linear head:
  AT8 Spearman:  0.457
  NeuN Spearman: 0.474
  mean Spearman across five targets: 0.279

MLP head:
  AT8 Spearman:  0.291
  NeuN Spearman: 0.235
  mean Spearman across five targets: 0.176
```

Interpretation: the frozen Stage B representation already contains a strong, linearly decodable AT8/NeuN signal. This argues against additional encoder fine-tuning for now. Counterfactual screens should next score perturbations by the pathology-head delta rather than by latent centroid distance alone.

## 12. Probe the Frozen A Beta / 6e10 Axis

Do not fine-tune another amyloid-specific encoder branch unless the frozen representation fails every conservative readout. The safer final amyloid probe uses only the frozen Stage B donor embeddings and a regularized donor-level model.

Run the multi-seed Ridge/ElasticNet sweep:

```powershell
$env:PYTHONPATH = "src"
conda run -n sea-ad-jepa python scripts/sweep_frozen_embedding_abeta_elasticnet.py `
  --seeds "11,17,23,31,47"
```

Expected outputs:

```text
results/tables/v2_2_abeta_frozen_embedding_elasticnet_sweep.csv
results/tables/v2_2_abeta_frozen_embedding_elasticnet_oof_predictions.csv
```

Current best stable result:

```text
ElasticNet(alpha=0.01, l1_ratio=0.95)
mean OOF Spearman across seeds: 0.264 +/- 0.056
representative seed OOF Spearman: 0.296
```

To project that sparse amyloid axis back to single cells and run DGE on the original RNA matrix:

```powershell
$env:PYTHONPATH = "src"
conda run -n sea-ad-jepa python scripts/identify_abeta_responsive_microglia.py
```

Expected outputs:

```text
results/tables/v2_2_abeta_responsive_microglia_axis_coefficients_summary.csv
results/tables/v2_2_abeta_responsive_microglia_cell_scores_summary.csv
results/tables/v2_2_abeta_responsive_microglia_donor_validation_summary.csv
results/tables/v2_2_abeta_responsive_microglia_dge_all_summary.csv
results/tables/v2_2_abeta_responsive_microglia_dge_upregulated_summary.csv
results/tables/v2_2_abeta_responsive_microglia_validation_metrics_summary.csv
```

Current full-cohort result:

```text
cells scored: 40,000
top A beta-axis cells: 2,000

donor mean A beta-axis score vs 6e10:
  Spearman: 0.677
  Pearson:  0.741
  p:        7.65e-16

top-50 DGE overlap with canonical APOE/C1Q/TREM2/SPP1 plaque/DAM marker set:
  overlap: 0
```

Interpretation: the sparse A beta axis is useful as a donor-level amyloid-associated readout, but the top cells are not currently validated as canonical plaque-proximal microglia. Keep the claim bounded unless spatial/plaque-proximity validation becomes available.

## 13. Train a Gated-Attention MIL A Beta Head

This experiment tests whether donor-level 6e10 is better modeled as a multiple-instance learning problem: each donor is a bag of microglia, and the model learns which cells in the bag explain amyloid burden.

The MIL head is deliberately small and interpretable:

```text
src/sea_ad_jepa/mil_head.py
```

Run the default MIL experiment:

```powershell
$env:PYTHONPATH = "src"
conda run -n sea-ad-jepa python scripts/train_abeta_mil_head.py `
  --epochs 80 `
  --print-every 20 `
  --max-cells-per-bag 512
```

Run the smaller stabilized variant:

```powershell
$env:PYTHONPATH = "src"
conda run -n sea-ad-jepa python scripts/train_abeta_mil_head.py `
  --epochs 120 `
  --print-every 30 `
  --max-cells-per-bag 1024 `
  --dropout 0.05 `
  --lr 0.0001 `
  --weight-decay 0.0001 `
  --hidden-dim 32 `
  --metrics-out results/tables/v2_2_abeta_mil_head_stable_metrics.csv `
  --predictions-out results/tables/v2_2_abeta_mil_head_stable_oof_predictions.csv `
  --attention-out results/tables/v2_2_abeta_mil_head_stable_attention.csv `
  --out-dir results/models/v2_2_abeta_mil_head_stable
```

Current result:

```text
default MIL OOF Spearman:    -0.147
stabilized MIL OOF Spearman: -0.097
```

Interpretation: the MIL machinery runs and exports attention weights, but the current head does not generalize for 6e10. Do not interpret high-attention cells biologically unless a future MIL configuration passes the donor-held-out prediction gate.

If a future MIL head passes the prediction gate, validate attention biology with:

```powershell
$env:PYTHONPATH = "src"
conda run -n sea-ad-jepa python scripts/validate_abeta_mil_biology.py `
  --attention results/tables/v2_2_abeta_mil_head_attention.csv
```

## 14. Audit Counterfactual Targets Against Covariates

Before druggability screening, audit the Golden Quadrant counterfactual genes for technical covariate artifacts.

```powershell
$env:PYTHONPATH = "src"
conda run -n sea-ad-jepa python scripts/audit_target_covariates.py
```

Outputs:

```text
results/tables/v2_2_target_covariate_audit.csv
results/tables/v2_2_target_covariate_audit_long.csv
```

Current result:

```text
APOE: CLEARED
APP:  CLEARED
TLR2: CLEARED
CD4:  WARNING: Technical Artifact
```

`CD4` is flagged because donor-level expression correlates with total-count and detected-gene proxies. Prioritize `APOE`, `APP`, and `TLR2` for the first druggability/actionability pass.
