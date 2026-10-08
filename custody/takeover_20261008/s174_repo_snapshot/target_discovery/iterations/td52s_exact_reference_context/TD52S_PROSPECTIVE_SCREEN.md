# TD52S — Exact Visible-Reference Context same-cell screen

Status: FALSIFICATION_SCREEN_ONLY__NO_TARGET_AUTHORITY
Date: 2026-09-07

## Historical failure attacked

TD48–TD51 encode all 17,122 non-query context genes into one query-agnostic 256-D CountSketch. TD51's prior-balanced ordinal innovation target narrowly beat the pooled matched-wrong-cell null but failed donor recurrence. A plausible unresolved mechanism is destructive context compression: the exact 512 reference genes that define each query's ordinal target are mixed with ~16,600 unrelated context genes.

TD52S keeps the biological target unchanged and changes only the transparent baseline context representation.

## Frozen target identity

Reuse TD51 exactly:
- Q = 64 fixed TD48 query genes;
- R = 512 fixed disjoint visible reference genes;
- TRAIN = all A_NATURAL_MIXTURE HVS + SEA_AD;
- TEST = all A_NATURAL_MIXTURE NPH52;
- TRAIN-only pair prior mu_qr and weight w_qr=1-mu_qr^2;
- prior-balanced target z_iq exactly as TD51.

No biological labels.

## Exact reference context

For every cell, compute the tie-aware within-cell average rank of each of the 512 visible R genes among R only:

u_ir = (rank_ir - 1) / 511 - 0.5.

Ties use average ranks. All R genes are in the 17,186 all-operator common-scalar intersection.

These 512 exact coordinates are visible molecular context. No hashing, learned feature selection, PCA, CCA, clustering, state labels, source matching, or query scalar enters the context.

## Predictor

Shortcut = intercept + log1p(source_library) + log1p(detected_genes).
Molecular = shortcut + the exact 512-reference rank coordinates.

Joint 64-output equal-donor weighted ridge.
Use the TD50/TD51 TRAIN-only inner source/donor folds and multiplier grid {1e-3,1e-2,1e-1,1,10}.
Target centering/scaling uses TRAIN only. Require >=48 measurable target coordinates.

## Primary NPH52 same-cell test

Fit shortcut and molecular models on pooled HVS+SEA_AD.
Apply frozen models to NPH52 correct-cell context.

Compute equal-donor TEST MSE and Delta=(MSE_shortcut-MSE_molecular)/MSE_shortcut.
Require Delta>0.

Construct 64 matched wrong-cell NPH52 context permutations using exactly the TD51/TD50 donor×operator depth/detection blocks and hash:
TD52S|evalnull|<j>|source|NPH52|donor|<d>|operator|<o>|block|<b>.

Only the 512 reference-rank context row is permuted. Model and measurement shortcut stay frozen.

Aggregate alignment condition:
correct-cell Delta > max of all 64 matched wrong-cell Deltas.

## Donor-primary recurrence gate

A donor is MOVABLE if at least one of its evaluation-context blocks has size >=2. Donors with no movable context are NOT_MEASURABLE for recurrence and do not count as PASS or FAIL.

For each MOVABLE donor compute donor-specific correct-cell Delta and the 64 donor-specific matched-wrong-cell Deltas.
Define DONOR_PASS iff correct-cell Delta > median of that donor's 64 null Deltas.

Require at least 12 DONOR_PASS among 16 MOVABLE NPH52 donors. This is the smallest integer giving a one-sided exact sign-test probability <0.05 under p=0.5 for n=16.

Additionally require leave-one-MOVABLE-donor-out aggregate alignment to remain positive against the corresponding 64 nulls for at least 12 of the 16 omissions.

## Kill / survive

If Delta<=0, aggregate alignment fails, donor sign recurrence fails, or LOO recurrence fails:
NO_DONOR_RECURRENT_SAME_CELL_REFERENCE_CONTEXT__TD52S_FAIL

If all pass:
TD52S_EXACT_REFERENCE_CONTEXT_SURVIVES__FREEZE_TRAIN_NULL_AND_INDEPENDENT_SOURCE_GATE_NEXT

This 50k screen cannot authorize a target, choose production dimensions/thresholds, or authorize JEPA training.