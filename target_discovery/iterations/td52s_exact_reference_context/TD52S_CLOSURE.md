# TD52S closure — exact reference context improves alignment but fails donor sign recurrence

Status: `NO_DONOR_RECURRENT_SAME_CELL_REFERENCE_CONTEXT__TD52S_FAIL`

Prospective freeze: `3f4d37c4bed50cbb958373ccb40cf081dcb46ebb`

## Primary result

Target = TD51 prior-balanced 64-query ordinal innovation, unchanged.
Context = exact 512 visible-reference within-cell rank coordinates, no hash compression.
TRAIN = pooled A_NATURAL_MIXTURE HVS + SEA_AD.
TEST = A_NATURAL_MIXTURE NPH52.

All 64 target coordinates measurable.
Selected ridge multipliers:
- shortcut: 0.001
- exact-reference molecular: 10

Equal-donor NPH52 TEST:
- shortcut MSE: 3.8057814260
- correct-cell molecular MSE: 3.3573426862
- observed Delta: **0.1178309234**

64 matched wrong-cell evaluation-context nulls:
- null median Delta: ~0.116973
- null maximum Delta: **0.1177197315**
- observed-minus-null-max: **+0.0001111920**

Thus the aggregate same-cell alignment condition passes.

## Donor-primary gate

17 NPH52 donors are present; 16 have at least one movable matched-context block. `human_NPH_906` has no movable context and is NOT_MEASURABLE for donor recurrence.

Among the 16 movable donors:
- correct-cell Delta > donor-specific null median: **11/16**
- prospective requirement: **>=12/16**
- correct-cell Delta > donor-specific null maximum: 1/16, descriptive only

Therefore the frozen donor sign recurrence gate fails.

The closest failed donor is separated from its null median by approximately -2.45e-4 in Delta units, so no strict-vs-nonstrict comparison or numerical tie can alter the 11/16 result.

## Leave-one-donor-out robustness

Among the 16 movable donor omissions:
- aggregate correct-cell alignment remains above all 64 corresponding nulls in **12/16** omissions
- prospective requirement: >=12/16

Thus the LOO condition passes exactly, but the donor sign condition does not. All conditions were conjunctive.

## Interpretation

Removing the 256-D global rank-sketch bottleneck and preserving the exact 512 visible-reference rank profile increases the pooled correct-cell margin relative to TD51, so destructive compression was a real contributor.

However, exact reference ranks with a linear ridge still do not establish donor-recurrent same-cell information. The remaining unresolved mechanism is conditional nonlinearity/query-specific structure, not lack of reference information per se.

Do not relax the 12/16 rule after observing 11/16.

No target authority, production dimension, threshold, or JEPA training authorization.