# F1 HC3 Command 15A4 — external-review handoff

Terminal: `PASS_F1_HC3_REPLICATION_FRONTIER_COMPLETE_AWAITING_EXTERNAL_REVIEW`.

- All 70 source-prefix rows were evaluated.
- All 35 NPH-free rows were evaluated.
- Independent reconstruction recomputed all 7,280 donor-deletion ranks.
- SVD projection leverage and pivoted-QR leverage agree within the frozen tolerance.
- Current cohort: 30 rows are donor-replicated HC3-admissible and 40 are nonreplicated/HC3-boundary rows.
- NPH52 C1 is donor-indispensable at `NPH52::human_NPH_906` across all 35 NPH-containing rows.
- HVS prefix 6 is donor-indispensable at `HVS::H20.06.354` across five NPH-free rows; SEA-AD has no donor-indispensable prefix in this cohort.
- No design or rank triple was selected or frozen.
- No outcome, expression, model, checkpoint, forward, training, or EMA access occurred.
- Current admissible/nonadmissible ranks and donor identities are not future-cohort constants.

The reusable artifact freezes only the cohort-agnostic reconstruction, full-design rank, LOO donor-replication, SVD/QR leverage, and HC3-admissibility procedure.
