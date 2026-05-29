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
- Verified GPU access:

```text
PyTorch: 2.7.0+cu128
CUDA available: True
GPU: NVIDIA GeForce RTX 3080 Laptop GPU
VRAM: 16 GiB
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

## Notes

The first attempted microglia-specific extraction was slow because microglia rows are distributed across the full H5AD file. The current contiguous pilot is a smoke-test dataset, not the final biological pilot.

Next optimization target:

```text
stream the full CSR matrix sequentially and build microglia donor-level pseudobulk features or a microglia-specific pilot without random HDF5 row access
```

## Next Steps

1. Build a sequential CSR streaming extractor for Microglia-PVM.
2. Create a proper Microglia-PVM pilot or donor-level pseudobulk matrix.
3. Run baseline pathology prediction on microglia-specific features.
4. Train JEPA on the microglia pilot.
5. Extract pathology-associated latent factors.
6. Rank genes/modules associated with A beta, pTau, GFAP, Iba1, and NeuN targets.

