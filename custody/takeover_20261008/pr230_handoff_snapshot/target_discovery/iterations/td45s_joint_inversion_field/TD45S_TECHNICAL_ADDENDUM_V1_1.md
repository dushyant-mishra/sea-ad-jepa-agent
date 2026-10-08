# TD45S technical addendum v1.1

Status: PROSPECTIVE_TECHNICAL_BINDING__NO_OUTCOME_INSPECTED
Parent: TD45S_PROSPECTIVE_FREEZE.md

## Inner donor fold
For donor d:
digest = SHA256 UTF-8 of "TD45S|inner|donor|<d>".
Inner fold = digest byte 0 least-significant bit (0 or 1).

Each inner validation arm is scored only on donors in that arm and fit on the other arm.

## Donor weights
In every fit/validation/evaluation subset with N cells and D donors, donor d receives total weight N/D, equally divided across its n_d cells. Weights sum to N.

## Standardization
Predictor means/SDs are computed with fit-arm donor weights only and applied frozen to validation/EVAL.
Operator dummy columns are defined from the outer TRAIN set; unseen validation/EVAL operators are all-zero.
Non-intercept SD<=1e-8 is replaced by 1 after centering.

Target-sketch coordinate means/SDs are computed from outer TRAIN for final fit and separately from each inner fit arm for lambda selection. Coordinates with SD<=1e-8 are NOT_MEASURABLE and excluded consistently from that fit's MSE.

## Ridge scaling
For standardized predictor design with intercept, base = mean diagonal of X_nonintercept^T W X_nonintercept.
Candidate lambda = multiplier * base for multipliers {1e-3,1e-2,1e-1,1,10}.
Intercept is not penalized.

Inner selection minimizes the mean of the two equal-donor validation MSEs. Ties within 1e-12 select the larger multiplier.

## Joint MSE
Within a cell, MSE is averaged over measurable target coordinates; then cells are equal-donor weighted.
