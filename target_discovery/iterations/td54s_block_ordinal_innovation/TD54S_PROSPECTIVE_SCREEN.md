# TD54S — Fixed Block Sketch of Query-Ordinal Innovation

Status: FALSIFICATION_SCREEN_ONLY__NO_TARGET_AUTHORITY
Date: 2026-09-07

## Historical gap attacked

TD48 established weak but real donor-heldout predictability for 64 individual query ordinal positions. TD51 prior-balanced those coordinates but donor-level same-cell recurrence remained weak. TD52/53 improved context fidelity/nonlinearity but did not make the 64-coordinate target leave-one-donor stable.

TD45-47 aggregated a different object: pair inversions among hidden target genes. They do not test whether averaging the already-promising query-local ordinal innovations across fixed address-dependent projections increases biological SNR.

TD54S changes only the target aggregation, not the underlying ordinal semantics.

## Base query target

Reuse TD51 exactly:
- same 64 TD48 query genes Q;
- same 512 visible reference genes R;
- same TRAIN-only source-balanced pair priors mu_qr and weights 1-mu_qr^2;
- same 64 prior-balanced query-ordinal innovation coordinates z_iq;
- TRAIN = pooled A_NATURAL_MIXTURE HVS + SEA_AD;
- TEST = A_NATURAL_MIXTURE NPH52;
- no biological labels.

## Fixed block sketch

Construct a deterministic 64 x 16 Rademacher matrix H.
For query address q and output coordinate k:
`H[q,k] = +1` iff the first bit of `SHA256("TD54S|query|<q_address>|k|<k>")` is 1, else -1.

Define 16 target coordinates:
`b_ik = sum_q H[q,k] * z_iq / sqrt(64)`.

No output coordinate is selected or dropped except the standard TRAIN variance measurability rule. Require all 16 measurable.

This is a fixed address-dependent sketch of query-local ordinal innovation, not an arithmetic block mean and not a hidden-gene scalar reconstruction.

## Molecular context

Use the exact TD52 512 visible-reference rank coordinates as the primary molecular context. This choice is frozen to isolate target aggregation; no nonlinear expansion or broad-context search is allowed.

Shortcut, equal-donor weighting, TRAIN-only standardization, inner source/donor folds, and ridge multiplier grid `{1e-3,1e-2,1e-1,1,10}` are exactly TD52.

## NPH52 same-cell gate

Fit shortcut and molecular models on pooled HVS+SEA_AD.
Evaluate the 16 standardized block targets on NPH52.

Require correct-cell Delta>0.

Run 64 exact TD52 matched wrong-cell NPH52 evaluation-context permutations, with preimage:
`TD54S|evalnull|<j>|source|NPH52|donor|<d>|operator|<o>|block|<b>`.

Aggregate alignment requires correct-cell Delta > max of all 64 wrong-cell Deltas.

## Donor-primary recurrence

Use the TD52 MOVABLE donor definition.
For each movable donor, DONOR_PASS iff correct-cell donor Delta > median of its 64 donor-specific null Deltas.
Require >=12/16 DONOR_PASS.

Require leave-one-movable-donor-out aggregate alignment against all corresponding 64 nulls in >=12/16 omissions.

## Terminal

Any conjunctive failure:
`NO_DONOR_RECURRENT_BLOCK_ORDINAL_INNOVATION__TD54S_FAIL`

All pass:
`TD54S_BLOCK_ORDINAL_INNOVATION_SURVIVES__FREEZE_INDEPENDENT_BLOCK_AND_SOURCE_REPLICATION_NEXT`

This 50k screen cannot select production sketch width, block size, thresholds, or authorize JEPA training.