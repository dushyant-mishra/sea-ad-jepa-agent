# V65 privileged recoverability execution-mechanics contract

**Date:** 2026-09-30  
**Status:** PROSPECTIVE NUMERICAL MECHANICS — REAL PAIRED EXECUTION NOT AUTHORIZED

This contract fills numerical implementation details left open by the first-factor contract and by `V65_PRIVILEGED_RECOVERABILITY_PRECISION_DECISION_CONTRACT_V2_20260930.md`. V2 remains the sole authority for ranks, gates, thresholds, classification, TEST use and permutation semantics. This document cannot weaken V2.

## Input and split

Use only `results/v64/gpt_handoff_bundle/nihcard_paired_subset.npz`, SHA-256
`6dca0d35ed7fdc16bc086a07e36a9f4dc178b71608d0fdf4de2727428e00a6`.

Use only donor membership from `results/v64/V64_NIHCARD_PAIRED_DONOR_SPLIT_V1.json`:
16 TRAIN / 4 VALIDATION / 4 TEST; 1,440 / 360 / 360 nuclei.

Before fitting, require aligned RNA/ATAC rows, finite nonnegative integer counts, and positive RNA and ATAC library size for every nucleus. Failure is a STOP, not an imputation rule.

## ATAC TF-IDF

For TRAIN raw ATAC counts `A`, with `N_train=1440`:

`L_i = sum_j A_ij`

`TF_ij = A_ij / L_i`

`df_j = number of TRAIN nuclei with A_ij > 0`

`IDF_j = log(1 + N_train / (1 + df_j))`

`TFIDF_ij = TF_ij * IDF_j`.

IDF is fit on TRAIN only. VALIDATION/TEST use their own row library sizes and the frozen TRAIN IDF. No additional scale factor, log transform, binarization, peak filtering or feature selection is applied. Peaks with TRAIN df=0 remain in the 12,000-peak coordinate system.

## Privileged basis and target

Compute economy SVD on TRAIN TF-IDF:

`M_train = U S V^T`.

Use the first 16 right-singular directions as `V16`, and scores `Z_raw = M @ V16`.

If the 16/17 singular-value boundary satisfies:

`abs(s[15]-s[16]) <= 1e-8 * max(1, abs(s[15]), abs(s[16]))`

STOP because the rank-16 target subspace is not uniquely frozen.

For each retained component, fix storage sign by finding the peak loading with largest absolute value, breaking exact ties by lowest peak index, and requiring that loading to be positive.

Using TRAIN scores only, compute coordinate mean and population SD. Require all SDs >0. Define:

`Z_priv_ATAC_V1 = (Z_raw - TRAIN_mean) / TRAIN_SD`.

Apply the same TRAIN mean/SD to VALIDATION/TEST. Do not remove a component because it correlates with depth.

## RNA representation

For raw RNA counts:

`R_i = sum_g RNA_ig`; require `R_i>0`.

`RNA_log1p10k_ig = log(1 + 10000 * RNA_ig / R_i)`.

Keep all 4,000 genes in frozen order.

Fit per-gene TRAIN mean and population SD. If TRAIN SD=0, retain the gene position but set its standardized feature to zero in every split. Otherwise standardize with TRAIN mean/SD. Candidate ridge and PCA baseline use this identical standardized 4,000-D RNA matrix.

## Candidate ridge

Fit multivariate ridge from all 4,000 standardized RNA features to the full standardized 16-D privileged target.

Alpha grid:

`[0.01, 0.1, 1.0, 10.0, 100.0]`.

Select alpha by leave-one-TRAIN-donor-out CV. In each fold compute full-16-D donor `R2_multi` using that fold's training-target mean as the reference. Score each alpha by the arithmetic mean across 16 held-out TRAIN donors. Choose the largest score; if tied within absolute 1e-12, choose the largest alpha.

After selection, fit one model on all TRAIN donors. No rank/shell-specific candidate fit is allowed.

## Technical baseline

Inputs are exactly:

1. `log(raw RNA library size)`;
2. detected-gene count.

Standardize both using TRAIN mean/population SD and require nonzero SD.

Fit full-16-D multivariate ridge. Select its alpha independently using the same grid, same TRAIN donor folds, same mean-donor-R2 objective and same largest-alpha tie rule. Then fit once on all TRAIN.

## Global-RNA baseline

Fit PCA16 on the same TRAIN-standardized 4,000-D RNA matrix using economy SVD of centered TRAIN X.

Apply the same 16/17 boundary tie rule; STOP on a tie. Fix signs using the largest-absolute-loading / lowest-index convention.

Project every split using this TRAIN basis. Fit full-16-D multivariate ridge from PCA16 scores to the target. Select alpha independently by the same TRAIN-only donor-CV rule and then fit once on all TRAIN.

## Full-state fits before rank/shell evaluation

Candidate, technical baseline and PCA baseline each predict the full 16-D target exactly once.

For every aggregate projector `P_k` and shell `S_k`, project:

- frozen true target;
- frozen candidate prediction;
- frozen technical-baseline prediction;
- frozen PCA-baseline prediction.

No model or baseline may be refit for a rank or shell.

All V2 projector, shell, geometry, deterministic permutation, VALIDATION and TEST rules then apply unchanged.

## Numerical custody

Use float64 for fitted arrays and metrics.

Before VALIDATION, persist and hash-bind:

- TRAIN IDF;
- V16 privileged basis;
- privileged TRAIN mean/SD;
- RNA TRAIN mean/SD and zero-SD mask;
- RNA PCA16 basis;
- three selected alphas;
- candidate and baseline coefficients/intercepts;
- all P_k and S_k;
- donor split identity;
- source digest;
- producer digest/blob;
- V2 precision-contract digest.

TEST remains unopened while any of these are mutable.

## Firewall and governance

This contract was written without real paired recoverability outcomes and does not authorize reading those outcomes.

Do not compute real RNA→ATAC prediction, real VALIDATION rank, real geometry, real pairing-null outcome or real TEST metrics until explicitly authorized.

`recoverability_execution_authorized=false`  
`TEST=UNOPENED`  
`TRAINING=OFF`  
`Phase B=STOPPED`  
`Stage 4=NOT_AUTHORIZED`  
`Morabito=PROTECTED`.
