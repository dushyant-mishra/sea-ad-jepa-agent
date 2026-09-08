# T0 IMMUNE Support Count Authority Specification V1

Status: **EXTERNAL INTERFACE FREEZE — 2026-09-08**

Parent membership SHA-256:
`d471499836118ddaf963ae9241f612d2e9a78bff4add62834347fc0ca06a3529`

Authenticate membership bytes first, then count accepted membership rows by donor.

Require membership rows to declare SEA_AD, MTG matrix, operator 31, reader-fit membership semantics where carried, and unique cell identity.

Output:
- source = SEA_AD
- operator_index = 31
- donor_id
- cells

Production invariants:
- 46 donors;
- exact candidate donor set;
- total cells = 20,804;
- exact positive integer cells;
- one row per donor;
- membership identity externally bound;
- `real_execution_ready=False`.

The cells quantity has only two lawful roles:
1. cells > 0 contributes only to threshold-free technical definedness/existence;
2. cells >= 80 defines tail_measurable.

The 80-cell floor never affects parent eligibility or discovery/confirmation assignment.
