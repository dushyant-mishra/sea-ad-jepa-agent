# Current Status

Last updated: 2026-05-27

## Completed

- Created the `sea-ad-jepa` conda environment.
- Downloaded SEA-AD donor metadata and MTG quantitative neuropathology metadata.
- Built donor-level pathology target table with 84 donors and 17 targets.
- Generated metadata QC figures.
- Downloaded the SEA-AD MTG final-nuclei AnnData file:

```text
data/raw/snrna/SEAAD_MTG_RNAseq_final-nuclei.2024-02-13.h5ad
```

- Installed CUDA-enabled PyTorch in `sea-ad-jepa`.
- Pinned the scientific Python stack to avoid native Windows crashes from bleeding-edge NumPy/SciPy/scikit-learn builds.
- Verified GPU access:

```text
PyTorch: 2.7.0+cu128
CUDA available: True
GPU: NVIDIA GeForce RTX 3080 Laptop GPU
VRAM: 16 GB
```

- Added fast H5AD metadata summary tooling.
- Confirmed main expression matrix shape:

```text
1,378,211 nuclei x 36,601 genes
```

- Confirmed relevant columns:

```text
Donor ID
Brain Region
Class
Subclass
Supertype
Continuous Pseudo-progression Score
```

- Confirmed `Subclass = Microglia-PVM` contains 40,000 nuclei.
- Created a fast contiguous 10,000-cell pilot:

```text
data/processed/sea_ad_mtg_contiguous_10k_hvg3k.h5ad
```

- Ran donor-level ridge baseline on the 10k pilot and 500 genes:

```text
results/tables/contiguous_10k_ridge_pathology_500genes.csv
```

- Ran a 2-epoch GPU JEPA smoke test:

```text
results/models/contiguous_10k_jepa_smoke/gene_jepa.pt
```

- Built full Microglia-PVM donor-level pseudobulk features from the full H5AD:

```text
data/processed/sea_ad_mtg_microglia_pvm_pseudobulk.csv
```

- Created a 10,000-cell Microglia-PVM JEPA pilot:

```text
data/processed/sea_ad_mtg_microglia_pvm_10k_hvg3k.h5ad
```

- Ran Microglia-PVM pseudobulk pathology baselines:

```text
results/tables/microglia_pvm_pseudobulk_ridge_1000genes.csv
```

Top held-out donor associations:

```text
number of AT8 positive cells per area_Grey matter: Spearman ~= 0.536
percent AT8 positive area_Grey matter: Spearman ~= 0.531
percent NeuN positive area_Grey matter: Spearman ~= 0.511
```

- Trained JEPA on the 10,000-cell Microglia-PVM pilot:

```text
results/models/microglia_pvm_jepa_10k/gene_jepa.pt
```

Training loss decreased from `0.627` to `0.431` over 20 epochs.

- Extracted JEPA donor embeddings and compared them against pathology targets:

```text
results/tables/microglia_pvm_jepa_embedding_ridge.csv
```

- Added and tested mixed random/module-aware JEPA masking:

```text
results/models/microglia_pvm_jepa_10k_mixed_masking/gene_jepa.pt
results/tables/microglia_pvm_jepa_mixed_embedding_ridge.csv
```

Mixed masking reached lower training loss than the first random-masking JEPA run, and improved NeuN-related donor prediction. It still did not outperform pseudobulk for AT8/pTau, suggesting the next pilot should preserve curated module genes rather than relying only on highly variable gene selection.

- Built and tested a module-preserving Microglia-PVM pilot:

```text
data/processed/sea_ad_mtg_microglia_pvm_10k_hvg3k_module_preserved.h5ad
results/models/microglia_pvm_jepa_10k_module_preserved_mixed/gene_jepa.pt
results/tables/microglia_pvm_jepa_module_preserved_embedding_ridge.csv
```

This increased curated module coverage from partial overlap to all seven curated microglia/AD modules. It also improved the JEPA AT8/pTau signal compared with the earlier JEPA runs:

```text
percent AT8 positive area_Grey matter
  random JEPA: Spearman ~= 0.316
  mixed HVG-only JEPA: Spearman ~= 0.295
  10k module-preserved mixed JEPA: Spearman ~= 0.395
  all-cell module-preserved mixed JEPA, 60 epochs: Spearman ~= 0.454
  all-cell module-preserved mixed JEPA, 100 epochs: Spearman ~= 0.451
```

The longer all-cell JEPA run improved the AT8 cell-count target and NeuN-related targets, but it did not yet beat the pseudobulk baseline for AT8 area. This suggests the next gains should come from better biological supervision or module design, not simply more epochs.

- Expanded the curated microglia module list from 7 to 15 modules:

```text
plaque response
complement
lipid metabolism
lysosome/phagocytosis
interferon response
inflammatory signaling
AT8-associated first-pass genes
homeostatic microglia
disease-associated microglia
senescence/stress
oxidative stress
synapse pruning
antigen presentation
vascular/barrier myeloid
chemokine/migration
```

- Rebuilt the all-cell Microglia-PVM pilot with expanded module preservation:

```text
data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad
40,000 cells x 2,957 genes
```

- Trained expanded-module JEPA with donor-balanced sampling:

```text
results/models/microglia_pvm_jepa_expanded_modules_balanced_e40/gene_jepa.pt
results/models/microglia_pvm_jepa_expanded_modules_balanced_e80/gene_jepa.pt
```

The expanded-module donor-balanced model gave a small improvement for the main AT8 area target, but lower learning rate continuation did not improve it further:

```text
percent AT8 positive area_Grey matter
  all-cell module-preserved mixed JEPA, 100 epochs: Spearman ~= 0.451
  expanded-module donor-balanced JEPA, 40 epochs: Spearman ~= 0.457
  expanded-module donor-balanced JEPA, 80 epochs: Spearman ~= 0.453
```

- Added pathology-aware fine-tuning with donor-held-out validation:

```text
scripts/finetune_jepa_pathology.py
```

First target:

```text
percent AT8 positive area_Grey matter
```

Held-out validation result from the first split:

```text
best validation Spearman ~= 0.738 at epoch 13
```

This is the strongest AT8 signal so far, but it is a supervised single-split result. It should be repeated across donor splits before being presented as stable model performance.

- Fixed the core JEPA architecture by adding an EMA target encoder:

```text
target_encoder starts as a clone of context_encoder
target_encoder gradients are frozen
after each optimizer step:
  target <- ema_decay * target + (1 - ema_decay) * context
```

This replaced the earlier static random target encoder, which was a major bottleneck.

- Trained a fresh EMA JEPA on the expanded-module donor-balanced pilot:

```text
results/models/microglia_pvm_jepa_ema_expanded_balanced_e40/
```

The EMA loss curve changed sharply:

```text
epoch 1:  loss ~= 0.380
epoch 10: loss ~= 0.012
epoch 20: loss ~= 0.013
epoch 40: loss ~= 0.035
```

The best self-supervised EMA JEPA checkpoints nearly matched the pseudobulk AT8-area baseline:

```text
percent AT8 positive area_Grey matter
  pseudobulk baseline: Spearman ~= 0.531
  static-target expanded-module JEPA, 40 epochs: Spearman ~= 0.457
  EMA expanded-module JEPA, 10 epochs: Spearman ~= 0.513
  EMA expanded-module JEPA, 20 epochs: Spearman ~= 0.516
  EMA expanded-module JEPA, 30 epochs: Spearman ~= 0.515
  EMA expanded-module JEPA, 40 epochs: Spearman ~= 0.515
```

This is the strongest self-supervised JEPA result so far. It does not clearly beat pseudobulk yet, but the EMA fix removed most of the gap.

- Fine-tuned the EMA checkpoint on AT8 pathology with donor-held-out validation:

```text
results/models/microglia_pvm_jepa_ema_expanded_at8_finetune/
best validation Spearman ~= 0.699
```

This was strong, but lower than the earlier single-split pathology-aware result from the static-target encoder. The fine-tuning result should therefore be treated as promising but split-sensitive until repeated donor-split validation is implemented.

- Added a VICReg-style variance hinge to the JEPA loss:

```text
loss = alignment_loss + variance_weight * variance_loss
```

The variance term penalizes latent dimensions whose batch standard deviation falls below a threshold. This is intended to reduce latent contraction during EMA training.

First run:

```text
variance_weight = 0.05
variance_gamma = 1.0
```

The variance term added a small improvement for the main AT8-area endpoint:

```text
percent AT8 positive area_Grey matter
  EMA JEPA, 20 epochs: Spearman ~= 0.516
  EMA + variance JEPA, 10 epochs: Spearman ~= 0.512
  EMA + variance JEPA, 20 epochs: Spearman ~= 0.514
  EMA + variance JEPA, 30 epochs: Spearman ~= 0.519
  EMA + variance JEPA, 40 epochs: Spearman ~= 0.514
  pseudobulk baseline: Spearman ~= 0.531
```

This is the best self-supervised JEPA result so far, but it still does not clearly beat pseudobulk. The next evaluation step should be repeated donor-held-out validation across pseudobulk, EMA JEPA, EMA+variance JEPA, and pathology-aware JEPA.

- Ranked Microglia-PVM pseudobulk genes associated with AT8 pathology:

```text
results/tables/microglia_pvm_percent_AT8_gene_rankings.csv
results/tables/microglia_pvm_percent_AT8_gene_set_scores.csv
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

## Notes

The first attempted microglia-specific extraction was slow because microglia rows are distributed across the full H5AD file. This is now handled by sequential CSR streaming in `scripts/build_microglia_streaming_pilot.py`.

## Next Steps

1. Add JEPA embedding-to-pathology comparison plots.
2. Extract pathology-associated latent factors.
3. Rank genes/modules associated with A beta, pTau, GFAP, Iba1, and NeuN targets.
4. Add richer hypothesis reports that compare pseudobulk, random-masking JEPA, mixed-masking JEPA, and module-preserved mixed JEPA.
