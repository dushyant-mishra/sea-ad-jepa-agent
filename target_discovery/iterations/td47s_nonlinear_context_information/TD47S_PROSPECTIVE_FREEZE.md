# TD47S — Nonlinear Broad-Context Information Existence screen

Status: FALSIFICATION_SCREEN_ONLY__NO_TARGET_AUTHORITY
Date: 2026-09-07

## Question

TD45/46 show no donor-heldout linear ridge gain from complementary rank context, despite strong target-gene positive controls.

Does the broad complementary molecular context contain nonlinear donor-generalizable information about the same joint inversion field?

## Frozen inputs

Reuse exactly:
- TD45 target inversion sketch Z (32 coordinates);
- TD45 HVS TRAIN/EVAL donor split;
- TD46 exact 256-dimensional rank CountSketch of all 16,930 non-target common-scalar genes;
- TD46 shortcut model and target standardization.

No biological labels.

## Nonlinear predictor

Standardize the 256 context-sketch coordinates using outer TRAIN mean/SD.

For each EVAL cell:
- compute squared Euclidean distance to every TRAIN cell in standardized context sketch;
- use fixed K=32 nearest TRAIN cells;
- predict each standardized target coordinate by the uniform mean of those 32 TRAIN target vectors.

K=32 is fixed before outcomes and is a pilot computational parameter, not production K.
No K search, metric search, source matching, state matching, or learned embedding.

Primary MSE is equal-donor mean over EVAL cells and the same measurable 32 target coordinates.

Primary Delta_knn = (MSE_shortcut - MSE_knn)/MSE_shortcut.

## Broken-context null

16 nulls.

Use exact TD37A TRAIN donor×operator depth/detection blocks.
Within each block, cyclically reassign TRAIN target vectors relative to the fixed TRAIN context rows:
TD47S|null|<j>|donor|<d>|operator|<o>|block|<b>.

Because context locations are unchanged, neighbor identities/distances are fixed; only target vectors attached to TRAIN context rows are permuted.

For every null compute the same EVAL KNN prediction and Delta_knn.

## Positive control

If observed Delta_knn<=0 or <=max(null), repeat the same fixed-K procedure using the 256 target-gene within-cell ranks as the neighbor space.

Positive control must have Delta>0 or:
TD47S_NOT_MEASURABLE__NONLINEAR_SCREEN_SENSITIVITY_FAILURE.

## Terminal

PASS only if:
- observed Delta_knn > 0;
- observed Delta_knn > max of 16 broken-context null Deltas.

PASS:
TD47S_NONLINEAR_COMPLEMENTARY_INFORMATION_EXISTS__FREEZE_FULL_SOURCE_GATE_NEXT

If primary fails and positive control validates:
NO_NONLINEAR_COMPLEMENTARY_INFORMATION_FOR_INVERSION_FIELD__TD47S_FAIL

No target authority, production K, or neural-training authorization.
