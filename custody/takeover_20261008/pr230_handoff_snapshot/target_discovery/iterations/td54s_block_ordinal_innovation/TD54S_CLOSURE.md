# TD54S closure — block aggregation does not establish donor-recurrent same-cell information

Status: `NO_DONOR_RECURRENT_BLOCK_ORDINAL_INNOVATION__TD54S_FAIL`

Prospective freeze: `89feb81116e251bc0bc1b17105d36fd18fca5225`

Target = fixed 16-dimensional signed sketch of the 64 TD51 prior-balanced query-ordinal innovation coordinates.
Context = exact 512 TD52 visible-reference ranks.
TRAIN = pooled HVS+SEA_AD; TEST = NPH52.

All 16 target coordinates measurable.
Selected ridge multipliers:
- shortcut: 0.001
- molecular: 10

NPH52 equal-donor TEST:
- shortcut MSE: 1.9381607291
- molecular MSE: 1.7971205094
- observed Delta: **0.0727701359**

64 matched wrong-cell evaluation-context nulls:
- median Delta: **0.0714496251**
- max Delta: **0.0727480751**
- observed-minus-null-max: **+2.2061e-05**

Aggregate alignment narrowly passes.

Donor recurrence:
- 16 movable donors
- donor correct-cell Delta > donor null median: **11/16**
- prospective requirement: >=12/16
- FAIL

Leave-one-donor-out robustness:
- aggregate alignment survives in only **5/16** omissions
- prospective requirement: >=12/16
- FAIL

Thus fixed block aggregation of query-ordinal innovations does not solve donor-generalizable same-cell identifiability.

Interpretation:
The remaining failure is not simply per-query noise. Generic/global context representations appear to dilute or average away query-specific molecular information. A lawful successor must test query-specific visible context selected entirely inside TRAIN and frozen before untouched-source evaluation.

No target authority or JEPA training authorization.