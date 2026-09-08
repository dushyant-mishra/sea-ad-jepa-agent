# TD45S closure — 256-gene complementary context fails, screen sensitivity validated

Status: `NO_COMPLEMENTARY_EVIDENCE_FOR_JOINT_INVERSION_FIELD__TD45S_FAIL`

Prospective freeze: `8974c42a4d66383cdcf2c2cf750c3b566d35190e`
Technical addendum: `dfdc66ba7fea5c0be6215de6de87a3b6d0a1599e`

Target-sketch resolution:
- >=31/32 measurable buckets: 100% TRAIN and EVAL
- all 32 measurable: 100% TRAIN and EVAL

Outer HVS split:
- EVAL cells: 595
- target coordinates: 32

Nested TRAIN-only ridge selection:
- shortcut multiplier: 1
- molecular 256-context-gene multiplier: 10

Held-out donor result:
- shortcut MSE: 0.9622490
- molecular MSE: 0.9777837
- Delta = **-0.0161442**
- only 5/32 target coordinates had positive Delta.

Primary screen therefore fails before null comparison.

Predeclared sensitivity control:
add target-gene ranks to the molecular predictor.
- selected multiplier: 1
- positive-control MSE: 0.6172293
- Delta vs shortcut: **+0.358556**

The screen is sensitive to predictable target structure, so this is not a predictor-sensitivity NOT_MEASURABLE terminal.

Conclusion:
256 disjoint context genes do not establish donor-heldout complementary-evidence predictability for the joint inversion field under this linear screen.

This does not test the much richer lawful evidence available from the remaining ~17k common-scalar genes and does not by itself rule out JEPA trainability from broad molecular context.
