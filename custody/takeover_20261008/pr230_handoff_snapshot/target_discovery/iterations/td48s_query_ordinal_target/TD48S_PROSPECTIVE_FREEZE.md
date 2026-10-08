# TD48S — Query-Local Ordinal Position Trainability screen

Status: FALSIFICATION_SCREEN_ONLY__NO_TARGET_AUTHORITY
Date: 2026-09-07

## Hypothesis

The robust concordance geometry may be trainable at the query-local level even though a two-hidden-gene inversion field is not.

For hidden query gene q, define its target as its within-cell ordinal position relative to a fixed visible reference set. Only q is withheld; reference genes are lawful context.

This is not scalar reconstruction. It is an address-resolved ordinal target.

## Input

A_NATURAL_MIXTURE; HVS fast screen.
No biological labels.
All genes from the 17,186 all-operator common-scalar addresses.

## Query genes and visible reference genes

Rank common-scalar addresses by SHA256("TD48S|gene|<g>").

First 64 addresses = fixed QUERY set Q.
Next 512 addresses = fixed visible REFERENCE set R.
Q and R are disjoint.

All other common-scalar genes are additional molecular context.

## Ordinal target

For cell i and query q with full-depth expression x_iq:

tau_iq =
[ number of reference genes h with x_ih < x_iq
  + 0.5 * number with x_ih = x_iq ] / 512.

Thus tau in [0,1] is a tie-aware percentile position of q relative to fixed visible references.

Measured zero remains valid evidence; this target does not equate structural unmeasurement with zero because all Q/R genes are common-scalar in all operators.

The query scalar x_iq is excluded from molecular context.

## Broad molecular context

Context gene set = all 17,186 common-scalar genes minus the 64 QUERY genes.
Reference genes remain in context.

Compute the exact within-cell average-rank vector over these 17,122 context genes and map it to a fixed 256-dimensional signed CountSketch:
SHA256("TD48S|ctxgene|<g>"), same bucket/sign convention as TD46S.

Sparse exact rank-sketch implementation must match dense calculation on 32 deterministic cells within 1e-10.

No query gene contributes to the context sketch.

## Donor split / shortcut / predictor

HVS donors:
SHA256("TD48S|split|0|source|HVS|donor|<d>"), alternating TRAIN/EVAL.

Shortcut:
intercept + log1p(source_library) + log1p(detected_genes) + TRAIN operator one-hot.

Molecular:
shortcut + 256 broad context-rank sketch.

Joint 64-output weighted ridge.
Use the same equal-donor weighting, nested two-inner-donor-fold lambda selection, lambda multiplier grid {1e-3,1e-2,1e-1,1,10}, standardization, and numerical conventions as TD45S.

Each tau coordinate is standardized using TRAIN mean/SD.
Coordinates with TRAIN SD<=1e-8 are NOT_MEASURABLE.
Require >=48/64 measurable query coordinates.

## Primary held-out score

On EVAL donors:
Delta_tau = (MSE_shortcut - MSE_molecular)/MSE_shortcut
averaged equally across measurable standardized query coordinates and equal-donor across cells.

Also report per-query Delta distribution.

## Broken-context null

If observed Delta_tau>0, run 16 complete null refits:
permute the 256 broad context-sketch row within TRAIN donor×operator depth/detection matched blocks:
TD48S|null|<j>|donor|<d>|operator|<o>|block|<b>.

Repeat nested lambda selection/refit in each null.

## Positive control

If primary fails, add the 64 query-gene values through their own tie-aware rank positions relative to R as predictor coordinates.
Positive control must yield Delta_tau>0 or:
TD48S_NOT_MEASURABLE__SCREEN_SENSITIVITY_FAILURE.

## Terminal

PASS only if:
- exact broad-rank sketch validation passes;
- >=48 query coordinates measurable;
- observed Delta_tau>0;
- observed Delta_tau > max of 16 null Deltas.

PASS:
TD48S_QUERY_LOCAL_ORDINAL_TARGET_PREDICTABLE__FREEZE_FULL_SOURCE_MEASUREMENT_GATE_NEXT

If primary fails and positive control validates:
NO_COMPLEMENTARY_EVIDENCE_FOR_QUERY_LOCAL_ORDINAL_TARGET__TD48S_FAIL

No production dimension, query set, reference set, or training authorization.
