# V65 first real privileged-factor recoverability execution contract

**Date:** 2026-09-30  
**Status:** PROSPECTIVE DESIGN — do not execute until Stage-4-like paired correspondence is separately authorized

## Objective

Test whether a real regulatory state constructed from privileged ATAC measurements contains a stable subspace that lawful RNA can recover beyond technical shortcuts.

This first experiment is deliberately global rather than query-specific. Its purpose is to qualify the recoverability machinery on real paired biology before defining query-conditioned regulatory teacher targets.

## Authority and split

Input source is the hash-bound paired NIH-CARD subset:

`sha256 6dca0d35ed7fd6cc16bc086a07e36a9f4dc178b71608d0fdf4de2727428e00a6`.

Canonical donor membership is **only**:

`results/v64/V64_NIHCARD_PAIRED_DONOR_SPLIT_V1.json`.

The donor membership embedded in the earlier recoverability preflight is superseded for execution.

TRAIN = 16 donors / 1,440 nuclei.  
VALIDATION = 4 donors / 360 nuclei.  
TEST = 4 donors / 360 nuclei.

TEST remains unopened until every construction, model, metric and threshold below is frozen.

## Privileged factor: ATAC-only

Define `Z_priv_ATAC_V1` from ATAC only.

RNA must not enter privileged-factor construction.

Use the 12,000 paired-subset peaks exactly as supplied; do not feature-select using RNA recoverability.

Construction:
1. TRAIN nuclei only fit ATAC term-frequency / inverse-document-frequency transforms.
2. Apply the frozen TRAIN transform to VALIDATION/TEST.
3. Fit truncated SVD on TRAIN only.
4. Primary privileged rank is fixed at 16.
5. Retain the full 16-dimensional privileged state whether or not RNA predicts it.

Do not remove a component because it correlates with depth. Depth dominance is a shortcut finding, not a reason to rotate the teacher after seeing outcomes.

## Lawful RNA input

Use the paired-subset 4,000 RNA genes.

Normalization is library-size normalization to 10,000 followed by `log1p`, learned without using privileged values.

No ATAC value, assay-availability label, donor ID, protected outcome, or target-derived feature may enter the RNA predictor.

## First predictor

Primary recoverability predictor is ridge regression from lawful RNA to the fixed 16-D ATAC state.

Regularization candidates must be fixed before VALIDATION and selected using TRAIN-only donor-blocked cross-validation.

This first experiment does not authorize a neural predictor. Failure of linear recovery means `UNQUALIFIED under this test`, not `REGULATORY_PRIVATE`.

## Baselines

Required prospective comparators:

1. technical-only RNA baseline:
   - log RNA library size;
   - detected-gene count.

2. simple global-RNA baseline:
   - first 16 TRAIN-fitted RNA PCA coordinates.

3. donor-preserving permutation negative control:
   - permute RNA-to-ATAC nucleus pairing within donor.

The candidate predictor receives no credit for recoverability if its performance is not materially better than technical/simple baselines.

## Primary metrics

Compute metrics donor-wise and summarize across donors.

Primary:
- multivariate held-out explained variance of the 16-D privileged state.

Secondary:
- canonical correlations between predicted and true privileged states;
- principal-angle cosines for candidate shared subspaces;
- relational-geometry correlation within donor.

Do not pool cells across donors as if nuclei were independent biological N.

## Shared-rank candidates

Candidate shared ranks are fixed prospectively:

`0, 2, 4, 8, 16`.

For each nonzero rank, the projection is fit using TRAIN only.

VALIDATION may choose among these ranks using the future precision/decision rule; TEST may not choose rank or rotation.

No post-hoc TEST rotation is allowed.

## Classification logic

This experiment may yield:
- `RNA-RECOVERABLE`;
- `PARTIALLY-RNA-RECOVERABLE`;
- `UNQUALIFIED`.

It **cannot by itself assign `REGULATORY-PRIVATE`**.

That label additionally requires independent evidence that the unrecoverable privileged factor is biologically credible. Poor RNA prediction alone is insufficient.

## Shortcut gates

At minimum report recovery relative to:
- RNA library depth;
- detected genes;
- ATAC library depth as a diagnostic of privileged-state technical loading;
- evidence availability/missingness;
- donor identity only as a grouping variable, never a predictor.

If the candidate RNA predictor is matched by technical baselines, classify the factor `UNQUALIFIED` for universal RNA supervision regardless of raw R².

## Decision thresholds

No biological outcome may be opened until a successor precision contract prospectively freezes:
- minimum acceptable donor support;
- confidence-interval procedure;
- material improvement over technical/global-RNA baselines;
- minimum subspace geometry threshold;
- rule for selecting shared rank;
- multiplicity treatment.

Until that precision contract exists, this experiment is design-frozen but execution-blocked.

## Interpretation asymmetry

Low RNA recoverability does not mean the ATAC state is biologically false.

High RNA recoverability does not prove biological validity.

Only a locked recoverable subspace can later be considered for compulsory universal RNA supervision.

## Governance

TRAINING OFF.  
Phase B STOPPED.  
Stage 4 NOT AUTHORIZED.  
Morabito PROTECTED.  
TEST unopened.  
No multimodal teacher implementation authorized.
