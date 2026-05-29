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

1. Improve JEPA objective with pathway-aware or module-aware masking.
2. Add JEPA embedding-to-pathology comparison plots.
3. Extract pathology-associated latent factors.
4. Rank genes/modules associated with A beta, pTau, GFAP, Iba1, and NeuN targets.
5. Add richer hypothesis reports that combine baseline metrics, JEPA metrics, gene rankings, and AD gene-set scores.
