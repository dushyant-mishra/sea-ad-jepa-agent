# F1 HC3 15C Numerical Robustness Repair — External Review Handoff

Terminal: `PASS_F1_HC3_15C_NUMERICAL_ROBUSTNESS_REPAIR_AWAITING_EXTERNAL_REVIEW`

- Scope: synthetic-only numerical independence repair; the evidence-slope issue is untouched.
- Frozen nuisance design: `(5,0,4)`, effective `104 x 16`, rank `16`, df `88`.
- Production HC3: reduced QR/triangular solves. Independent validation: thin SVD/pseudoinverse.
- QR/SVD baseline and prospective +/-1e-5 near-boundary fixtures agree within frozen tolerances and exactly on gates.
- Near-boundary gates: positive `True`; negative `False`.
- All 14 frozen truth-table cases and the 15C adversarial suite pass.
- Frozen v1/v4/integration Git blobs remain unchanged: `{"scripts/v4/contextual_target_f1_decision_integration_v4.py": "5dfd5858f1e8865f871b633a033e400f2d7fb5e2fb52bebbc613f7efed1bce2a", "scripts/v4/contextual_target_f1_decision_v1.py": "204859f48b96d1bb268d9249596b801537f2c911183dc4a20bc30fe5683e2d34", "scripts/v4/contextual_target_f1_decision_v4.py": "5215faffe1e90b6567054fd7fb4d62d501787dbacd704e09ff28af9c65d45913"}`.
- No expression, model/checkpoint tensor, training, optimizer, EMA, DEV, SEALED, pathology, or real F1 outcome was accessed.
- Reader/forward authority remains unset. Real F1 remains unauthorized pending external review.
