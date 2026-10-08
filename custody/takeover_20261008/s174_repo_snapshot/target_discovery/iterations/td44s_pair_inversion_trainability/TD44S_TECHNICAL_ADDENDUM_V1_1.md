# TD44S technical addendum v1.1

Status: PROSPECTIVE_TECHNICAL_BINDING__NO_OUTCOME_INSPECTED
Parent: TD44S_PROSPECTIVE_FREEZE.md

## Hash convention
For any SHA256 use UTF-8 exact preimage.

For context gene g:
digest = SHA256("TD44S|ctxbucket|<g>").
bucket = unsigned big-endian integer from digest bytes 0..7 mod 96.
sign = +1 when least-significant bit of digest byte 8 is 0; otherwise -1.

Each bucket value is divided by sqrt(number of context genes assigned to that bucket). Empty buckets remain zero.

## Context ranks
For each cell independently, use average ranks for tied context-gene expression values.
Normalize as (rank-1)/(384-1).
Center each normalized rank by subtracting 0.5 before CountSketch accumulation.

## Donor weights
Within any pair-specific resolved TRAIN or EVAL subset with N cells and D donors, each donor has total weight N/D and each cell of donor d has weight N/(D*n_d).
Thus weights sum to N while donors contribute equally.

## Predictor columns
Shortcut operator columns are created from TRAIN operators only, in sorted numeric order, dropping the smallest TRAIN operator as reference.
An EVAL operator unseen in TRAIN has all operator dummy columns zero and is reported; it does not create a new column.

All non-intercept predictor columns, including dummy/context columns, are standardized by weighted TRAIN mean and SD. SD <=1e-8 is set to 1 and the centered column becomes zero.

## Ridge
With weighted standardized design X including intercept:
lambda = 1e-2 * mean(diag(X_nonintercept^T W X_nonintercept)).
Intercept is not penalized.
If there are zero non-intercept estimable columns, the model is NOT_MEASURABLE.
Solve by symmetric linear system; numerical singularity after ridge is NOT_MEASURABLE.

## Evaluation MSE
For each target pair, normalize EVAL donor weights by the same equal-donor rule and compute weighted mean squared error.
Delta_p is computed exactly from these weighted MSEs.

## Null blocks
Broken-context null blocks are constructed using TRAIN cells only, independently within each donor×operator stratum, with the exact TD37A v1.1 ordinal rank-fraction / detected-octile / consecutive-block rule.
Context rows are cyclically shifted within each block; target and shortcut rows are not moved.

SHA256_U64 for null shifts is first digest bytes 0..7 interpreted unsigned big-endian.
