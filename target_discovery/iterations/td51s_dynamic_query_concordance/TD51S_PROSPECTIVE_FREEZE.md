# TD51S — Dynamic-Reference Query Concordance cross-source screen

Status: `FALSIFICATION_SCREEN_ONLY__NO_TARGET_AUTHORITY`
Date: 2026-09-07

## Historical failure attacked

Binding predecessors:
- TD41/43: within-cell pairwise concordance geometry is cross-source reproducible and measurement-reliable conditional on resolution.
- TD44–47: raw/random pair inversion fields are not donor-heldout complementary-evidence inferable.
- TD48: query-local ordinal position with 512 arbitrary references is weakly HVS-predictable.
- TD49: the same source-internal NPH52 refit fails.
- TD50: pooled HVS+SEA_AD -> NPH52 mapping passes its TRAIN-null contract, but a post-freeze NPH52 evaluation-alignment audit reproduces the gain after matched context reassignment.

TD51 attacks the two identified problems jointly:
1. remove the globally predetermined pair-order floor before target formation;
2. make correct TEST-cell context alignment qualification-bearing.

## Input

Use only A_NATURAL_MIXTURE.
No biological labels.

All target/reference/context addresses come from the 17,186 addresses that are MEASURED_SCALAR in all 42 operators.

TRAIN sources for target definition and predictor fitting:
- HVS
- SEA_AD

TEST source:
- NPH52

No NPH52 target value, pair direction, target variance, or molecular context may participate in dynamic-reference selection, predictor fitting, target centering/scaling, or lambda selection.

Explicit `global_row` is retained before merges and is the only CSR row address.

## Query genes

Reuse the exact 64 TD48 query genes:
rank the 17,186 common-scalar addresses by
`SHA256("TD48S|gene|<g>")`;
the first 64 addresses are Q.

No query identity changes from TD48–50.

## Candidate reference pool

From all common-scalar addresses excluding Q, rank by
`SHA256("TD51S|refpool|<g>")`.

Take the first 2,048 addresses as the fixed candidate reference pool P.

2,048 is a falsification-pilot parameter only.

## TRAIN-only dynamic-reference score

For every query q in Q and candidate reference h in P, separately within HVS and SEA_AD TRAIN sources:

For each donor d:
- use full-depth cells in that donor;
- pair sign is +1 if q>h, -1 if q<h, unresolved if tied;
- if the donor has >=1 resolved cell, compute donor conditional mean sign `mu_d(q,h)`;
- otherwise donor score is missing.

For source s:
- `mu_s(q,h)` = mean of finite donor scores;
- `support_s(q,h)` = fraction of source donors with a finite donor score.

A candidate reference is eligible for query q only if:
- support_HVS >= 0.50
- support_SEA_AD >= 0.50

For each eligible pair define:
`dominance(q,h) = max(abs(mu_HVS), abs(mu_SEA_AD))`.

Rank eligible references by:
1. ascending dominance;
2. descending min(support_HVS, support_SEA_AD);
3. SHA256("TD51S|ref|q|<q>|h|<h>").

Take the first **64** references for each query.

If any query has fewer than 64 eligible references:
`TD51S_NOT_MEASURABLE__INSUFFICIENT_DYNAMIC_REFERENCES`.

No NPH52 expression participates in this selection.

## Dynamic query target

For cell i, query q, and its 64 frozen dynamic references R_q:

`tau_dyn(i,q) = [# {h in R_q: x_ih < x_iq} + 0.5 * # {h: x_ih = x_iq}] / 64`.

All q and h are common-scalar addresses.
Measured ties are valid target evidence.
Structural unmeasurement cannot occur for these addresses under the frozen operator support contract.

## Broad molecular context

Reuse the TD48 broad context:
all 17,186 common-scalar addresses minus the 64 QUERY genes.

Dynamic references remain visible context.

Compute the exact within-cell average-rank vector over the 17,122 context genes and the same fixed 256-dimensional TD48 signed CountSketch.

Sparse implementation must match dense average-rank sketch on 32 deterministic NPH52 TEST cells with max absolute difference <=1e-10 before scoring.

## TRAIN / TEST

TRAIN = all HVS + SEA_AD A-sample cells/donors.
TEST = all NPH52 A-sample cells/donors.

TRAIN weighting: equal total weight per donor across the pooled 87 donors.
TEST scoring: equal total weight per NPH52 donor.

## Portable shortcut

Predictors:
- intercept
- log1p(source_library)
- log1p(full-row detected_genes)

Do not use source ID, dataset ID, matrix ID, donor ID or operator categorical identity.

Molecular model:
shortcut + fixed 256-dimensional broad context-rank sketch.

## Predictor and model selection

Joint 64-output weighted ridge exactly as TD50.

Inner pooled TRAIN donor fold:
`SHA256("TD51S|inner|source|<source>|donor|<d>")` digest byte-0 LSB.

Lambda multiplier grid:
`{1e-3, 1e-2, 1e-1, 1, 10}`.

All predictor standardization, target centering/scaling, inner selection and final fitting use TRAIN only.

Require >=48/64 TRAIN-measurable target coordinates.

Also require >=48/64 TEST coordinates with finite nonzero TEST variation for evaluation; this is an estimability check only and cannot alter fitting.

## Primary cross-source score

On NPH52 TEST:
`Delta_dyn = (MSE_shortcut - MSE_molecular) / MSE_shortcut`.

MSE is equal-donor weighted over cells and measurable standardized query coordinates.

## TRAIN broken-context null

16 complete refits.

Within each TRAIN source separately and donor×operator depth/detection block, cyclically permute the 256-dimensional molecular context row:
`TD51S|trainnull|<j>|source|<s>|donor|<d>|operator|<o>|block|<b>`.

Repeat inner lambda selection and final molecular fit in every null.

Targets and shortcut remain attached to true TRAIN cells.

## TEST correct-cell alignment null

64 frozen-model evaluation nulls.

Hold the observed TRAIN-fitted model fixed.

Within NPH52 TEST donor×operator depth/detection matched blocks, cyclically reassign the 256-dimensional molecular context row:
`TD51S|evalnull|<j>|source|NPH52|donor|<d>|operator|<o>|block|<b>`.

Shortcut features and true NPH52 target remain attached to the original cell.

For every null compute:
- raw `Delta_dyn`;
- within-donor-centered `Delta_dyn_within`, obtained by independently subtracting each NPH52 donor's per-query mean from true targets and each model prediction before MSE.

## Observed within-donor criterion

Compute observed `Delta_dyn_within` using the same within-donor centering.

This diagnostic is qualification-bearing because TD50 showed that source/donor calibration can otherwise create a large cross-source delta without correct-cell alignment.

## Positive control

If any primary criterion fails, add the true 64 dynamic tau coordinates themselves as predictor coordinates to TRAIN and TEST under the same pooled fitting/evaluation standardization.

The positive control must yield raw `Delta_dyn > 0` and within-donor `Delta_dyn_within > 0` or return:
`TD51S_NOT_MEASURABLE__SCREEN_SENSITIVITY_FAILURE`.

The control cannot rescue the candidate.

## PASS rule

PASS only if all are true:
1. dynamic-reference construction is estimable for all 64 queries;
2. >=48 TRAIN and >=48 TEST target coordinates are measurable;
3. observed raw `Delta_dyn > 0`;
4. observed raw `Delta_dyn > max(16 TRAIN-null deltas)`;
5. observed raw `Delta_dyn > max(64 TEST-alignment-null deltas)`;
6. observed within-donor `Delta_dyn_within > 0`;
7. observed within-donor `Delta_dyn_within > max(64 within-donor TEST-alignment-null deltas)`.

PASS terminal:
`TD51S_DYNAMIC_QUERY_CONCORDANCE_SURVIVES_CROSS_SOURCE_CELL_ALIGNMENT__CANDIDATE_FOR_DEEPER_QUALIFICATION`

If sensitivity control validates but any PASS rule fails:
`NO_CELL_ALIGNED_CROSS_SOURCE_DYNAMIC_QUERY_CONCORDANCE__TD51S_FAIL`.

No target authority, production reference count, sketch width, query set, threshold or JEPA training authorization.
