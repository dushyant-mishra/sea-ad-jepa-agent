# Independent physical GSE301119 full-matrix reproduction — exact GPU-laptop command

Date: September 25, 2026. This addendum addresses PR #118 Section 3.2, which explicitly concedes that no independent reproduction of the **effect matrices** was performed. PR #91 independently validated the *guide-by-donor support census* but did not validate effects.

The versioned independent base-R script `scripts/r/independently_verify_gse301119_all_effects_v1.R` reimplements the mathematical estimator from the already-frozen two-donor, ten-cell-per-target×donor contract without importing the primary R producer. It recomputes **every gene × target** for CRISPRi and CRISPRa separately, comparing both full matrices to the existing **SHA-pinned** heavy RDS results and independently checking per-gene detection masks, donor-matched NT controls, missingness and exact column/row identity. A sign flip can no longer satisfy the check merely because inhibition and activation agree within one producer.

## Preconditions and exact source roots

| role | bytes | SHA-256 |
|---|---:|---|
| CRISPRi raw guide×donor pseudobulk | 40,248,363 | `e796504f41ddd65f3a5b72699d12431ce664974e0860ecb255858bd084283549` |
| CRISPRa raw guide×donor pseudobulk | 30,245,701 | `9fe028f508ce33a8c968ab05c363c345135b0b6227db4476838c70fb9d874d90` |
| CRISPRi previously produced FC matrix | 29,391,063 | `7f550f436333cf6159f54ff7b3221617952fcc13ac2b9d68c4cf572d53b39e43` |
| CRISPRa previously produced FC matrix | 21,338,886 | `474202c0705a57bdc939ce483fe7612d9082fb57d80d94eefd8bd3d3c509ba93` |

Use authenticated `D:/jepa_perturb_outputs_20260923/gse301119_rawpb_v1/` and `D:/jepa_perturb_outputs_20260923/gse301119_donor_aware_v1/` directories from PR #77 and #118, respectively, or verify identical actual bytes if the drive layout changed. Existing R environment was R 4.6.1, SeuratObject 5.4.0, library `D:/jepa_rlib46`; this verifier itself only needs base R, an available sparse `Matrix` reader and `digest`+`jsonlite` for receipts.

```powershell
$env:R_LIBS_USER = "D:/jepa_rlib46"
Rscript analysis/therapeutic_perturbation_etl/scripts/r/independently_verify_gse301119_all_effects_v1.R --crispri-raw "D:/jepa_perturb_outputs_20260923/gse301119_rawpb_v1/CRISPRi_guide_donor_raw_counts.rds" --crispra-raw "D:/jepa_perturb_outputs_20260923/gse301119_rawpb_v1/CRISPRa_guide_donor_raw_counts.rds" --crispri-matrix "D:/jepa_perturb_outputs_20260923/gse301119_donor_aware_v1/CRISPRi_donor_aware_log2fc_matrix.rds" --crispra-matrix "D:/jepa_perturb_outputs_20260923/gse301119_donor_aware_v1/CRISPRa_donor_aware_log2fc_matrix.rds" --out "D:/jepa_perturb_outputs_20260925/independent_gse301119_full_matrix_v1/GSE301119_INDEPENDENT_REPRODUCTION_V1.json"
```

Use a clean branch checkout and a versioned *new* output directory; no output overwrite. Fail closed if an existing RDS lacks exact rownames/colnames, or the donor metadata do not align with the raw count columns. Do not manufacture missing names from other files or repair in place. Pin any corrected physical pseudobulk producer separately with a new versioned digest and re-run independent review.

## What constitutes closure

Expected **full effects**: CRISPRi 206 targets, 204 cross-donor estimable; CRISPRa 206 targets, 198 cross-donor estimable. Every finite gene-level log2FC must agree to **≤1e-9**, all NA masks must be identical, and perturbation-wide gene detection masks must agree exactly. Confirm neither modality silently borrowed the other's feature universe (36,601 and 19,162 features). Output includes input root hashes, max absolute error, full finite-comparison census, and explicit absence of population-level inference. If any check fails, **STOP** and leave the old PR118 effects `CODE_UNTESTED`; inspect the upstream metadata/normalization rather than relaxing the tolerance after seeing results.

Only the synthetic CI runs automatically on GitHub. Full physical rerun needs the heavy RDS files on the GPU laptop and **has not been performed by this review branch**.

Even a physical PASS here is an independent computational reproduction on the **same two donors and same input data**, not biological replication and not independent cross-study validation. GSE335887 reserved profiles, FULL104 protected data, N1 masking and model training remain unopened.
