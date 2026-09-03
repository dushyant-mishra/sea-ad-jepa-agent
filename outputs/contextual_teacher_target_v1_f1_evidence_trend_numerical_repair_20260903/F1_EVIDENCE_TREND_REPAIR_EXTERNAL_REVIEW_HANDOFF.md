# F1 Evidence-Trend Numerical Repair — External Review Handoff

Terminal: `PASS_F1_EVIDENCE_TREND_NUMERICAL_REPAIR_AWAITING_EXTERNAL_REVIEW`

- Scope is synthetic-only. Real F1 and reader/forward authority remain forbidden.
- Production slope is exactly `(A100-A20)+0.5*(A80-A40)` in float64; A60 has coefficient zero.
- Independent reference uses a separate `math.fsum` implementation.
- Maximum per-donor slope difference: `0.0`.
- Exact-flat fixtures return exact zero in both implementations.
- Near-boundary positive gates: `{'independent_gate': True, 'production_gate': True}`.
- Near-boundary negative gates: `{'independent_gate': False, 'production_gate': False}`.
- Legacy donor-varying flat fixture produced `104` nonzero historical slopes and a historical PASS; repaired slopes are all exact zero and non-estimable/vetoed.
- Complete gate-vector agreement: `True`.
- Every non-evidence gate/report and the accepted QR-HC3 report/gate are unchanged.
- Historical Git-blob authorities remain byte-for-byte unchanged: `{"scripts/v4/contextual_target_f1_decision_integration_v4.py": "5dfd5858f1e8865f871b633a033e400f2d7fb5e2fb52bebbc613f7efed1bce2a", "scripts/v4/contextual_target_f1_decision_v1.py": "204859f48b96d1bb268d9249596b801537f2c911183dc4a20bc30fe5683e2d34", "scripts/v4/contextual_target_f1_decision_v4.py": "5215faffe1e90b6567054fd7fb4d62d501787dbacd704e09ff28af9c65d45913", "scripts/v4/contextual_target_f1_hc3_15c_adapter_v2.py": "c5432f84cb51105419a68c4d14e81d52d84818bad206af0458b4ba6fc37d5a3d", "scripts/v4/contextual_target_f1_hc3_stable_qr_v2.py": "8a4a18314687f410b01a3e798670d9cffb6ee377abe9217c719dfceaec941961"}`.
- No expression, protected outcomes, model/checkpoint, training, optimizer, EMA, DEV, SEALED, or pathology data were accessed.
