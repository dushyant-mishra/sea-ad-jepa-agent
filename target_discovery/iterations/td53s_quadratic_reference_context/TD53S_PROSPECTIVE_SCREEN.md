# TD53S — Fixed Quadratic Exact-Reference Context same-cell screen

Status: FALSIFICATION_SCREEN_ONLY__NO_TARGET_AUTHORITY
Date: 2026-09-07

## Historical gap attacked

TD52 preserved the exact 512 visible-reference rank profile and narrowly improved pooled same-cell alignment, but linear ridge reached only 11/16 movable NPH52 donor passes versus the frozen 12/16 requirement.

TD47 killed nonlinear prediction only for the historical joint inversion field. It did not test the query-local prior-balanced TD51 target from exact reference ranks. TD53S tests one prospectively fixed nonlinear expansion only; there is no architecture/model tournament.

## Frozen target / train-test

Reuse TD52 exactly:
- 64 TD48 query genes Q;
- 512 TD48 visible reference genes R;
- TD51 TRAIN-only prior-balanced ordinal innovation target z_iq;
- TRAIN = all A_NATURAL_MIXTURE HVS + SEA_AD;
- TEST = all A_NATURAL_MIXTURE NPH52;
- same shortcut, donor weighting, target standardization, inner source/donor folds, lambda multiplier grid, matched evaluation blocks and donor recurrence definitions.

No biological labels.

## Exact reference input

For cell i, u_i in R^512 is the TD52 tie-aware normalized rank profile over R only, centered at zero.

## One fixed nonlinear expansion

Construct 512 deterministic Rademacher projection columns a_k in {-1,+1}^512.
For reference coordinate r and projection k:
`a[r,k] = +1` iff the first bit of `SHA256("TD53S|r|<r_address>|k|<k>")` is 1, else -1.

For each cell:
`h_ik = (u_i dot a_k / sqrt(512))^2`.

Molecular predictor = shortcut + 512 exact linear u coordinates + 512 quadratic h coordinates.

The quadratic coordinates are fixed before outcomes and are a random-feature approximation to second-order interactions among visible reference ranks. No projection/width/activation/kernel search is permitted.

## Model

Joint 64-output equal-donor weighted ridge.
Use the same multiplier grid `{1e-3,1e-2,1e-1,1,10}` and TRAIN-only inner folds as TD52. Standardize predictors from TRAIN only. Require >=48 measurable target coordinates.

## Primary NPH52 test

Compute correct-cell equal-donor Delta against the same measurement shortcut.
Require Delta>0.

Run 64 TD52-style matched wrong-cell NPH52 evaluation-context permutations. The complete 1024-dimensional molecular context row (u,h) is replaced by the matched wrong cell; shortcut remains correct-cell.

Aggregate alignment requires observed correct-cell Delta > maximum of all 64 wrong-cell Deltas.

## Donor-primary recurrence

Use the exact TD52 MOVABLE donor definition.
For each movable donor, DONOR_PASS iff donor correct-cell Delta > median of its 64 donor-specific wrong-cell Deltas.
Require >=12/16 DONOR_PASS.

Also require leave-one-movable-donor-out aggregate observed Delta > all 64 corresponding null Deltas for >=12/16 omissions.

## Terminal

If any conjunctive condition fails:
`NO_DONOR_RECURRENT_QUADRATIC_REFERENCE_CONTEXT__TD53S_FAIL`

If all pass:
`TD53S_NONLINEAR_REFERENCE_CONTEXT_SURVIVES__FREEZE_TRAIN_NULL_AND_SOURCE_REPLICATION_NEXT`

No production nonlinear architecture, width, threshold, target authority, or JEPA training authorization is implied by this 50k falsification screen.