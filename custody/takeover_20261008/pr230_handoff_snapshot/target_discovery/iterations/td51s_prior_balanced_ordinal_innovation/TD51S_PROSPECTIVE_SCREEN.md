# TD51S — Prior-Balanced Query-Ordinal Innovation same-cell screen

Status: FALSIFICATION_SCREEN_ONLY__NO_TARGET_AUTHORITY
Date: 2026-09-07

## Historical failure attacked

TD48 showed small HVS donor-heldout predictability of query ordinal tau. TD49 failed source-internal NPH52 replication. TD50 showed a large HVS+SEA_AD -> NPH52 gain, but a post-gate matched wrong-cell evaluation attack reproduced essentially the entire gain. TD44-47 already killed joint pair/inversion-field targets under linear and nonlinear broad context.

TD51S does not retry raw pair accuracy or the joint inversion field. It removes the pair-specific population-order prior before aggregation and makes same-cell evaluation alignment qualification-bearing.

## Fixed query/reference/context identity

Reuse TD48 exactly:
- 64 query genes Q = first 64 common-scalar addresses under SHA256("TD48S|gene|<g>");
- 512 fixed reference genes R = next 512;
- all 17,122 non-query common-scalar genes form visible molecular context;
- same fixed 256-dimensional TD48 rank CountSketch.

No biological labels.

## Pairwise ordinal innovation target

For query q and reference r define full-depth direction s_iqr in {-1,0,+1} from the frozen normalized expression values; ties are 0.

TRAIN = all A_NATURAL_MIXTURE HVS + SEA_AD donors/cells.
TEST = all A_NATURAL_MIXTURE NPH52 donors/cells.

For every q,r estimate a TRAIN-only population prior mu_qr:
1. mean s_iqr within each donor;
2. mean donor values within HVS and within SEA_AD;
3. equal average of the HVS and SEA_AD source means.

Define fixed TRAIN-only informativeness weight:
w_qr = 1 - mu_qr^2.
No threshold or pair selection.

For each cell/query define the prior-balanced ordinal innovation target:
z_iq = sum_r w_qr * (s_iqr - mu_qr) / sum_r w_qr.

Thus globally deterministic pair order contributes little, while pair relations that vary across cells/sources retain weight. NPH52 target values do not influence mu, w, model selection, or predictor standardization.

## Predictor

Shortcut = intercept + log1p(source_library) + log1p(detected_genes).
Molecular = shortcut + same 256 TD48 broad-context rank sketch.

Joint 64-output equal-donor weighted ridge.
TRAIN-only inner source/donor folds use the frozen TD50 hash and lambda grid {1e-3,1e-2,1e-1,1,10}.
Target coordinates are centered/scaled from TRAIN only. Require >=48 measurable coordinates.

## Primary same-cell screen

Fit shortcut and molecular models on pooled HVS+SEA_AD.
Apply to NPH52 correct-cell context.

Require correct-cell molecular MSE < shortcut MSE.

Then perform 64 matched wrong-cell NPH52 evaluation-context permutations using the exact TD50 evaluation block construction and hash:
TD51S|evalnull|<j>|source|NPH52|donor|<d>|operator|<o>|block|<b>.

The trained molecular model is frozen. Only the 256 context sketch row is permuted within donor×operator depth/detection matched blocks.

PASS_ALIGNMENT iff correct-cell molecular MSE is strictly lower than every one of the 64 matched wrong-cell MSEs.

Equivalently correct-cell Delta_shortcut must exceed max of the 64 wrong-cell Deltas.

## Sensitivity control

If PASS_ALIGNMENT fails, replace the 256 context sketch at TRAIN and TEST with the true 64 z target coordinates as an explicit leakage-positive predictor, fit the same ridge family, and rerun the same evaluation permutation logic. The control must discriminate correct from wrong-cell context or return NOT_MEASURABLE.

## Terminal

If correct molecular does not beat shortcut or PASS_ALIGNMENT fails while positive control succeeds:
NO_SAME_CELL_PRIOR_BALANCED_ORDINAL_INNOVATION__TD51S_FAIL

If primary passes:
TD51S_SAME_CELL_ORDINAL_INNOVATION_SURVIVES__FREEZE_TRAIN_NULL_AND_SOURCE_REPLICATION_NEXT

This 50k screen cannot authorize target selection, production dimensions, thresholds, or JEPA training.