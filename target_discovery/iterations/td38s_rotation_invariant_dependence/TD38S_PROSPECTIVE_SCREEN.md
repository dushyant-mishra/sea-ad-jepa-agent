# TD38S — Rotation-Invariant Split-Ledger Dependence Energy screen

Status: FALSIFICATION_SCREEN_ONLY__NO_TARGET_AUTHORITY
Date: 2026-09-07

## Historical predecessor
TD37A established strong donor-recurrent split-ledger canonical concordance in SEA_AD but frozen CCA axes collapsed on HVS/NPH52. TD35/36 already rejected ordinary source/global subspaces. Therefore TD38S does NOT test axes, loadings, rotations, state correspondence, clustering, or graph alignment.

## Materially new necessary condition
For two disjoint fixed gene views X and Y of the same cell, the singular values of the regularized whitened cross-covariance operator are invariant to orthogonal changes of basis in either view.

Define the rotation-invariant canonical dependence energy:
E = sum_j rho_j^2
where rho_j are all singular values of
(Cxx + lambda_x I)^(-1/2) Cxy (Cyy + lambda_y I)^(-1/2).

No component identity, sign, ordering, K, rotation, Procrustes alignment, state matching, or cross-source matching enters E.

If a universal split-ledger common-information target is viable, a necessary condition is that E recur above a matched broken-pairing null in each source independently.

## Input
Use only A_NATURAL_MIXTURE from the 50k falsification archive.
Global rows are exactly 0..24999.
Preserve explicit global_row before any merge and use only global_row for CSR addressing.
Sample B is not used.
native_class and broad_class are dropped before statistics.
Common-scalar addresses are states==MEASURED_SCALAR in all 42 operators; expected n=17186.

## Panels
Two independent 512-address panels p in {0,1}.
Rank common-scalar address g by SHA256 UTF-8 bytes of:
TD38S|panel|<p>|address|<g>
Take first 512. First 256 = X; second 256 = Y.
Panels are fixed before outcomes.

## Donor halves
For each source s and split k in {0,1}, rank donor d by SHA256 UTF-8 bytes of:
TD38S|split|<k>|source|<s>|donor|<d>
Alternating ranked donors form H0 and H1.
Each half is analyzed independently; halves are biological replicates, not train/test directions.

## Measurement residualization
Within each source/half/panel:
- derive log_library = log1p(source_library);
- derive log_detected = log1p(full-row CSR nonzero count);
- nuisance design = intercept + log_library + log_detected + operator one-hot with lexicographically smallest operator as reference;
- weighted least squares with equal total donor weight;
- residualize every selected gene;
- weighted-center and weighted-standardize by residual SD, variance floor 1e-8.

## Regularization
For each view covariance C:
lambda = 1e-3 * mean(diag(C)).
No tuning.
PSD inverse square root via eigendecomposition with floor max(1e-10, 1e-10*max_eigenvalue).

## Primary statistic
E = squared Frobenius norm of the whitened cross-covariance operator, equivalently sum of squared canonical singular values over the complete 256-dimensional view.
No rank/prefix is selected.

Also report max rho and effective energy fraction E/256 descriptively, but only E is screened.

## Matched broken-pairing null
Use exactly the TD37A v1.1 deterministic within-donor×operator depth/detection block construction and cyclic Y-shift rule.
Pairings never cross donor or operator.
Nuisance residualization and marginal whitening are held identical; Cxy and E are recomputed for every null.
32 null replicates per source/half/panel.
null_p95 = sorted_null[ceil(0.95*32)-1] = zero-based index 30.
PASS_HALF iff observed E > null_p95.

## Kill rule
A source survives the necessary-condition screen only if PASS_HALF is true for:
- both donor halves,
- both donor splits,
- both independent panels.

That is 8/8 required source cases.

If ANY of HVS, NPH52, or SEA_AD fails source survival:
NO_UNIVERSAL_ROTATION_INVARIANT_SPLIT_LEDGER_DEPENDENCE__TD38S_KILL

If all three sources survive:
TD38S_SURVIVES_NECESSARY_CONDITION__FREEZE_FULL_TD38_BEFORE_ANY_CROSS_SOURCE_ANALYSIS

This screen cannot promote a target, choose D/K/thresholds, open annotations, authorize JEPA training, or replace full-reader qualification.
