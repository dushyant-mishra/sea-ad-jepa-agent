# V64 privileged-state recoverability decomposition protocol

**Date:** 2026-09-30  
**Status:** PROSPECTIVE ARCHITECTURE / QUALIFICATION PROTOCOL — TRAINING OFF

## 1. Objective

A future privileged teacher may contain regulatory or functional information not identifiable from RNA alone. The project therefore requires a prospective procedure for determining which part of a privileged teacher state is eligible for universal RNA-student supervision.

The object of qualification is a **recoverable subspace**, not an arbitrary individual coordinate.

This follows the project's existing basis-stability lesson: if a latent subspace is stable but axes rotate, scientific interpretation and qualification must be rotation-aware.

## 2. Objects

Let:

- `X_RNA` = lawful RNA-only student input.
- `Z_priv` = privileged teacher factor constructed from declared richer evidence.
- `D` = donor identity used only for splitting/aggregation, not as a predictive feature.
- `O` = declared observation/technical descriptors used for shortcut diagnostics, not as hidden biological state.

A future decomposition may be written conceptually as:

`Z_priv = Z_shared + Z_private`

where `Z_shared` is the component reproducibly predictable from lawful RNA and `Z_private` is residual privileged structure.

This equation does not imply Euclidean coordinate subtraction is the final implementation. The qualified object may be a subspace/projection.

## 3. Non-negotiable anti-leakage rules

The privileged factor must be constructed without evaluation-donor outcomes influencing:

- factor dimensionality;
- basis rotation;
- feature selection;
- RNA predictor architecture;
- regularization;
- recoverability threshold;
- shared/private split.

If `Z_priv` construction itself uses RNA, the exact RNA contribution must be declared and a successor design must demonstrate that recoverability is not tautological. A regulatory factor cannot qualify merely because RNA was used to define it.

Query-safety rules remain binding for query-conditioned factors.

## 4. Biological splitting hierarchy

Minimum qualification split:

- donor-disjoint TRAIN;
- donor-disjoint VALIDATION;
- donor-disjoint TEST.

Where multiple datasets/studies are available, add a stronger transport level:

- TRAIN/VALIDATION within development datasets;
- completely held-out dataset/study TEST.

Where measurement technologies differ, report technology transport separately rather than combining it with biological novelty.

Cell-random splitting is allowed only for software smoke tests, never for scientific recoverability authority.

## 5. Fitting sequence

### 5.1 Privileged factor

Fit/construct `Z_priv` using TRAIN only where fitting is required.

Any factor normalization or basis fit must be trained without TEST donors.

### 5.2 RNA predictor

Fit a lawful RNA-only map:

`f_RNA(X_RNA) -> Z_priv`

using TRAIN biological units only.

Predictor complexity, regularization and any candidate shared-rank selection are chosen within TRAIN/VALIDATION.

### 5.3 Stable privileged geometry

Before coordinate-wise recoverability is interpreted, assess privileged-state basis stability across independent TRAIN resamples/donor partitions using rotation-aware diagnostics such as:

- principal angles;
- canonical correlations;
- orthogonal Procrustes similarity;
- eigen/singular-value separation where relevant.

If the subspace is stable but individual axes are not, qualification proceeds at the subspace level.

## 6. Recoverability metrics

No single metric is yet frozen as scientific authority. A successor execution contract must prospectively choose primary and secondary metrics.

Eligible metric families include:

- held-out subspace canonical correlation;
- principal-angle alignment between predicted and privileged subspaces;
- cross-validated multivariate explained variance;
- held-out relational-geometry agreement;
- coordinate prediction only when coordinate stability is independently established.

All metrics must be donor-aggregated or donor-aware so large donors cannot silently dominate scientific mass.

## 7. Baselines

RNA recoverability must be compared prospectively against relevant lawful baselines, including as applicable:

- query identity only;
- broad/global RNA state only;
- simple expression/activity proxies;
- generic cell-state representation;
- observation/technical descriptors;
- evidence-availability indicators as an explicit shortcut diagnostic, not as a lawful biology baseline.

A complex RNA predictor is not credited for reproducing a privileged factor when a simple activity/detection proxy performs equivalently.

## 8. Shared/private rank selection

Do not select the shared dimensionality on TEST.

Permissible strategy:

1. define candidate ranks before TEST;
2. fit each candidate on TRAIN;
3. choose rank using donor-held-out VALIDATION under a predeclared rule;
4. lock the projection;
5. evaluate once on TEST.

Nested donor-level cross-validation is an alternative if frozen prospectively.

Post-hoc rotation to maximize TEST recoverability is forbidden.

## 9. Classification

A future decision contract may classify factors as:

- `RNA_RECOVERABLE`
- `PARTIALLY_RNA_RECOVERABLE`
- `PRIVILEGED_PRIVATE`
- `UNQUALIFIED`

The exact numerical thresholds are NOT set here.

### RNA_RECOVERABLE

The declared privileged factor/subspace passes the prospective recoverability and shortcut gates at the required biological holdout level.

### PARTIALLY_RNA_RECOVERABLE

A prospectively selected subspace passes, while a nontrivial residual does not.

Only the locked passing subspace can be compulsory universal RNA-student supervision.

### PRIVILEGED_PRIVATE

The privileged factor has independent biological support but does not pass RNA recoverability.

It may remain useful for:
- multimodal inference;
- biological validation;
- uncertainty;
- geometry constraints;
- teacher-side adjudication.

It cannot be treated as a missing answer for RNA-only cells.

### UNQUALIFIED

Evidence is insufficient to decide recoverability or biological validity.

## 10. The private residual is preserved

Failure of the RNA predictor does not authorize deleting or redefining the residual until the teacher becomes easier to predict.

The private residual remains an explicit scientific object.

Any successor decomposition must report:

- total privileged dimension/rank;
- qualified shared rank;
- retained private rank;
- donor support;
- uncertainty.

## 11. Shortcut and availability tests

At minimum test whether recoverability is explained by:

- library depth;
- detected-gene count;
- query detection;
- promoter accessibility/activity;
- general ATAC depth;
- E2 degree;
- evidence availability;
- dataset/operator identity.

The 379 E2-anchored but NIH-CARD-RNA-unmeasurable genes remain a named availability-negative probe when relevant.

If evidence availability alone predicts the qualified shared/private assignment, qualification stops for shortcut audit.

## 12. Held-out evidence family

RNA recoverability is not biological validation.

Where feasible, after a shared subspace is locked, evaluate whether it predicts or aligns with a mechanistically distinct evidence family not used in factor construction or recoverability selection.

Example:

`privileged factor from paired RNA+ATAC/network evidence -> shared RNA-recoverable subspace -> held-out contact or perturbational evidence`

This asks whether the shared state carries transferable biology rather than merely shared assay activity.

## 13. Universal/full-corpus rule

FULL104-scale RNA-only cells receive compulsory targets only for factors carrying current RNA-recoverability authority.

For a private factor:

- no zero target;
- no pseudo-target merely because the modality is missing;
- no loss term that penalizes RNA-only cells for not reproducing the private state.

Missing privileged measurements must remain missingness, not negative biology.

## 14. Smoke-test versus scientific-test boundary

Synthetic tests may prove software semantics:

- a shared latent can be recovered from RNA;
- an independent private latent cannot;
- forcing the full privileged state lowers attainable recovery;
- decomposition bookkeeping does not zero-fill private state.

Synthetic tests do NOT establish biological recoverability thresholds.

Real scientific qualification requires donor/dataset holdouts under a prospectively frozen execution contract.

## Governance

- TRAINING OFF
- Phase B STOPPED
- Stage 4 NOT AUTHORIZED
- Morabito PROTECTED
- no multimodal teacher implementation authorized by this protocol
