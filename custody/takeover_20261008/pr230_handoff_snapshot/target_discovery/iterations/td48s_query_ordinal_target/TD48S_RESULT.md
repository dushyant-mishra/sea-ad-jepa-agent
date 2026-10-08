# TD48S result — query-local ordinal target survives HVS trainability screen

Status: `TD48S_QUERY_LOCAL_ORDINAL_TARGET_PREDICTABLE__NO_TARGET_AUTHORITY`

Prospective freeze: `c5abcd3642f23d72167d408155efd38063fe070a`
Technical addendum: `893327909b52f0f6989569f17f91203911010cd9`

## Exact context implementation

- query genes: 64 fixed common-scalar addresses
- visible reference genes: 512 fixed disjoint common-scalar addresses
- broad context: remaining 17,122 common-scalar addresses
- 256-dimensional fixed rank CountSketch
- 32 deterministic dense-vs-sparse checks
- max absolute difference: **7.77e-16**, PASS

All 64 query tau coordinates were measurable.

## Nested donor-heldout HVS result

TRAIN-only selected ridge multiplier:
- shortcut: 1
- molecular broad context: 10

Held-out donor MSE:
- shortcut: 0.7725489533
- molecular: 0.7711613155

Primary:
`Delta_tau = +0.001796181`

Per-query:
- 40/64 coordinates positive
- median coordinate Delta ~+0.00676

## 16 complete broken-context null refits

Every null repeated the TRAIN matched context permutation, inner donor lambda selection, and final fit.

Null Delta range:
- max: **-0.0193386074**
- median: **-0.0206425544**
- min: ~-0.0221141

Observed Delta is positive and exceeds every null replicate.

Prospective terminal:
`TD48S_QUERY_LOCAL_ORDINAL_TARGET_PREDICTABLE__FREEZE_FULL_SOURCE_MEASUREMENT_GATE_NEXT`

Interpretation boundary:
This is the first label-free donor-heldout evidence that broad complementary molecular context predicts a query-local ordinal target beyond depth/detection/operator shortcuts and a structure-preserving broken-context null.

The absolute HVS improvement is small (~0.18%), so this is not target authority and requires independent source replication and measurement-depth reliability before promotion.
