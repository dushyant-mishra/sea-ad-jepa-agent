# TD46S — Broad-Context Concordance-Inversion Trainability screen

Status: FALSIFICATION_SCREEN_ONLY__NO_TARGET_AUTHORITY
Date: 2026-09-07

## Why materially different from TD45S

TD45S showed that 256 random disjoint context genes do not predict the inversion field under donor-heldout ridge, while a target-gene leakage control gives +35.9% MSE improvement.

TD46S tests the same frozen inversion-field target against broad lawful molecular evidence: every all-operator common-scalar address except the 256 target genes.

No target definition is changed.

## Input / target

A_NATURAL_MIXTURE, HVS fast screen only.
No biological labels.
Use the exact TD45 target genes, 4096 target pairs, 32 target hash buckets, donor split, training-donor mu_p reference, and target-sketch construction unchanged.

Broad context gene set:
all 17,186 common-scalar addresses minus the 256 target genes.
Expected size: 16,930.

Target genes are excluded from context by exact address identity.

## Exact broad-context within-cell rank sketch

For every cell, compute average-tie ranks across all 16,930 context genes and normalize ranks to [0,1].

Map every context gene to a fixed 256-dimensional signed CountSketch:
digest = SHA256("TD46S|ctxgene|<gene>")
bucket = first 8 digest bytes unsigned big-endian mod 256
sign = +1 if digest byte 8 LSB=0 else -1.

For bucket b:
sketch_b = sum_g sign_g * (normalized_rank_g - 0.5) / sqrt(number of context genes assigned to b).

The rank sketch must be computed exactly, including the tied zero block. A sparse algorithm is allowed only if independently checked against dense average-rank calculation on at least 32 deterministic cells with max absolute sketch difference <=1e-10.

256 is a computational pilot sketch width, not production D.

## Predictor / shortcut / nested lambda

Use TD45S shortcut features, equal-donor weighting, target standardization, nested donor-fold ridge selection and lambda grid unchanged.

Molecular model = shortcut + 256 broad-context rank-sketch coordinates.

## Broken-context null

If observed Delta > 0, run 16 complete null refits:
permute the 256-dimensional context sketch within TRAIN donor×operator depth/detection matched blocks using:
TD46S|null|<j>|donor|<d>|operator|<o>|block|<b>.

Repeat nested lambda selection and full molecular refit in every null.

## Positive control

If observed Delta <=0, add the 256 target-gene within-cell ranks exactly as in TD45S.
If this control does not yield Delta>0:
TD46S_NOT_MEASURABLE__SCREEN_SENSITIVITY_FAILURE.

## Terminal

PASS only if:
- exact sparse-rank-sketch validation passes;
- target resolution gate remains satisfied;
- observed Delta>0;
- observed Delta > max of 16 broken-context null Deltas.

PASS:
TD46S_BROAD_COMPLEMENTARY_EVIDENCE_SURVIVES__FREEZE_FULL_SOURCE_GATE_NEXT

If primary fails and positive control validates:
NO_BROAD_COMPLEMENTARY_EVIDENCE_FOR_INVERSION_FIELD__TD46S_FAIL

No target authority, production sketch width, threshold, pair count, or training authorization.
