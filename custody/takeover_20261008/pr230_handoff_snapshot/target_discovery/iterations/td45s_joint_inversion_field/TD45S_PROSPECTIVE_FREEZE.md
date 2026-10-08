# TD45S — Joint Concordance-Inversion Field Trainability screen

Status: FALSIFICATION_SCREEN_ONLY__NO_TARGET_AUTHORITY
Date: 2026-09-07

## Historical failure attacked

TD41/43 establish reproducible, measurement-reliable within-cell concordance structure.
Adversarial review shows raw pair accuracy is dominated by a population ordering prior.
TD44S is NOT_MEASURABLE and its per-pair ridge formulation is variance-inefficient.

TD45S tests the joint cell-specific inversion field after subtracting the training-donor pair-order reference, using a fixed target sketch only as a computational probe.

## Input

A_NATURAL_MIXTURE; HVS fast screen only.
No biological labels.
All genes are from TD41 panel 0 and therefore from the 17,186 all-operator common-scalar addresses.

Target genes T = panel positions 0..255.
Context genes C = panel positions 256..511.
No target gene enters molecular context.

## Fixed target pairs

Enumerate all unordered pairs within T.
Rank by SHA256("TD45S|targetpair|g|<g>|h|<h>").
Take first 4096 pairs.

4096 and sketch dimensions below are computational pilot parameters only.

## Donor split

Same deterministic HVS split rule as TD44S but preimage:
TD45S|split|0|source|HVS|donor|<donor>.
Alternating donors -> TRAIN/EVAL.

## Training-donor reference direction

For each target pair p, on TRAIN full-depth counts:
- use only resolved cells;
- compute donor-balanced mean sign mu_p in [-1,+1].

For any resolved cell i:
r_ip = sign_ip - mu_p.
Unresolved pairs are missing, not zero biological residual.

This centers the target against the population pair-order prior before trainability scoring.

## Fixed target inversion sketch

Map each of the 4096 target pairs to 32 signed hash buckets:
digest = SHA256("TD45S|targetbucket|g|<g>|h|<h>")
bucket = first 8 digest bytes, unsigned big-endian, mod 32
sign = +1 if digest byte 8 LSB=0 else -1.

For cell i and bucket b:
- include only resolved target pairs assigned to b;
- target z_ib = signed sum of r_ip divided by sqrt(number of resolved pairs in b);
- if no pair in a bucket resolves, that bucket is NOT_MEASURABLE for that cell.

Require >=31/32 measurable target buckets for >=95% of TRAIN and EVAL cells, otherwise:
TD45S_NOT_MEASURABLE__TARGET_SKETCH_RESOLUTION.

The target sketch is centered using TRAIN mu_p only; the same mu_p is applied to EVAL.

## Molecular context

Compute average-tie within-cell ranks of the 256 context genes, normalized to [0,1].
Use all 256 context-rank coordinates directly; no learned dimensionality reduction.

## Shortcut features

Intercept + log1p(source_library) + log1p(full-row detected_genes) + TRAIN-operator one-hot.

Molecular model = shortcut + 256 context ranks.

## Predictor

Joint multi-output weighted ridge, one coefficient matrix for all 32 target-sketch coordinates.

Use only cells with all 32 target buckets measurable for the primary screen.
Equal total donor weight.

Standardize non-intercept predictors using weighted TRAIN statistics.
Target coordinates are centered/scaled using weighted TRAIN mean/SD; SD<=1e-8 makes that target coordinate NOT_MEASURABLE.

Ridge lambda is selected only inside TRAIN from the fixed grid:
{1e-3, 1e-2, 1e-1, 1, 10} * mean diagonal weighted predictor Gram.

Selection uses two deterministic inner donor folds:
SHA256("TD45S|inner|donor|<d>") parity.
Choose lambda minimizing equal-donor validation MSE averaged across measurable target coordinates; ties choose larger lambda.
This entire selection is repeated inside every broken-context null.

Fit shortcut and molecular models independently.

## Primary score

On held-out EVAL donors:
MSE_shortcut = equal-donor mean over cells and target coordinates.
MSE_molecular likewise.

Delta = (MSE_shortcut - MSE_molecular)/MSE_shortcut.

Also report per-coordinate Delta and fraction positive, but only joint Delta is primary.

## Broken-context training null

16 complete null refits.

Within TRAIN, cyclically permute the full 256-gene context-rank row within exact TD37A donor×operator depth/detection blocks:
TD45S|null|<j>|donor|<d>|operator|<o>|block|<b>.

Target inversion sketch and shortcut features remain on true cells.
Repeat inner lambda selection and molecular refit in every null.
Shortcut fit is unchanged.

## Positive control

If primary Delta<=max(null) or Delta<=0, run a predeclared sensitivity control by adding the 256 target-gene within-cell ranks to molecular context.
Repeat TRAIN-only lambda selection.
Positive control must have Delta>0 or return:
TD45S_NOT_MEASURABLE__SCREEN_SENSITIVITY_FAILURE.

Positive control cannot rescue the target.

## Terminal

PASS only if:
- target sketch resolution gate passes;
- observed Delta>0;
- observed Delta > maximum of 16 null Deltas.

PASS:
TD45S_JOINT_INVERSION_FIELD_PREDICTABLE__FREEZE_FULL_DONOR_SOURCE_GATE_NEXT

If primary fails and positive control validates:
NO_COMPLEMENTARY_EVIDENCE_FOR_JOINT_INVERSION_FIELD__TD45S_FAIL

No production target dimension, pair count, weighting, threshold, or training authority.
