# TD53S closure — fixed quadratic reference context fails LOO donor robustness

Status: `NO_DONOR_RECURRENT_QUADRATIC_REFERENCE_CONTEXT__TD53S_FAIL`

Prospective freeze: `d10b6994ee2b0410fd4cd63791d7d916fef3c2d1`

Target/train-test are unchanged from TD52. The only new feature is the prospectively fixed 512-dimensional squared Rademacher projection expansion of the exact 512 visible-reference rank profile, appended to the 512 linear reference-rank coordinates.

Selected ridge multipliers:
- shortcut: 0.001
- molecular quadratic context: 10

Equal-donor NPH52 TEST:
- shortcut MSE: 3.8057814260
- molecular MSE: 3.5071805524
- observed Delta: **0.0784598063**

64 matched wrong-cell evaluation-context nulls:
- median Delta: **0.0777428194**
- max Delta: **0.0784435793**
- observed-minus-null-max: **+1.6227e-05**

Aggregate alignment therefore passes only narrowly.

Donor recurrence:
- movable NPH52 donors: 16
- donor correct-cell Delta > donor-specific null median: **12/16**
- prospective requirement: >=12/16
- donor sign recurrence therefore passes exactly.

Leave-one-movable-donor-out robustness:
- aggregate correct-cell alignment > all 64 corresponding nulls in only **7/16** omissions
- prospective requirement: >=12/16
- FAIL
- LOO margin range approximately -1.97e-4 to +3.10e-4

All TD53S conditions were conjunctive. Therefore the candidate fails.

Interpretation:
A fixed second-order expansion can redistribute the small same-cell signal enough to reach the donor sign threshold, but the result is highly composition-sensitive and not leave-one-donor stable. There is no justification for a nonlinear architecture search after this failure.

The remaining scientific direction should not keep optimizing query-local predictors. The robust evidence lies at the ordinal relational/block geometry level, while cell/query-specific innovation remains weak and heterogeneous.

No target authority, production nonlinear architecture, threshold, or JEPA training authorization.