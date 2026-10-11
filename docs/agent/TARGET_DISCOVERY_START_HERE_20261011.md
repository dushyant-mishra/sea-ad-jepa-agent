# Target Discovery — START HERE — 2026-10-11

For a new agent taking over the **real target-discovery lane**, read in this order:

1. `docs/agent/TARGET_DISCOVERY_CURRENT_HANDOFF_20261011.md`
2. `docs/agent/TARGET_DISCOVERY_CANONICAL_TAKEOVER_20261011.md`
3. `docs/agent/TARGET_DISCOVERY_CANONICAL_STATE_20261011.json`
4. `docs/agent/TD_G6_ATTEMPT0_EXECUTION_RECORD_20261011.md`
5. `docs/agent/TARGET_DISCOVERY_HISTORY_AND_AUDIT_LESSONS_20261011.md`
6. `docs/agent/TARGET_DISCOVERY_EVIDENCE_CODE_DATA_INDEX_20261011.md`
7. `docs/agent/MACHA_TARGET_DISCOVERY_AND_PARALLEL_LANE_RUNBOOK_20261011.md`
8. Raw successor qualification evidence at `qual/td-g6-global-row-successor-7e482cf5-20261011@e4d771cb6d76f9d783b81ddb4e1691c8f4091fd0`
9. `docs/superpowers/specs/2026-10-11-td-corrected-replay-interpretation-prefreeze.md`
10. `target_discovery/HANDOFF_CURRENT_20260907.md`
11. `target_discovery/iterations/td33_global_row_binding_guard/TD33_SUMMARY.json`
12. PR #282 exact successor code/diff, PR #277 historical custody qualification/evidence, and PR #259 G4/G5 value-blind evidence.
13. PR #275 V2 tournament governance only after the real G6/G7/corrected-replay critical path is understood.

Current hard terminal:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

Latest successor qualification result:

`FAILED_GATE_1_STALE_SYNTHETIC_FIXTURES__REAL_SAMPLE_GATE_PASS__PR259_COMPAT_PASS__NO_EXECUTION_AUTHORITY`

Exact failed-qualified PR #282 head:

`7e482cf50f73a5cecda16482777129dd3ca725a6`

Exact qualification evidence commit:

`e4d771cb6d76f9d783b81ddb4e1691c8f4091fd0`

Gate summary:

- focused suite: **4 failed / 215 passed**;
- real Sample-A freeze: **PASS**, `PASS_REAL_SAMPLE_FREEZE_SCHEMA_AND_GLOBAL_ROW_BINDING`, 25,000 rows, exact source counts, no physical `global_row`;
- real PR #259 compatibility: **PASS**, `1 passed / 0 skipped / 0 failed`;
- worktree clean before and after;
- no patch or rerun during qualification;
- no owner/runtime authority created;
- no G6 or G7 execution.

The four failures are stale synthetic fixtures that do not provide the stronger real G6 selector schema (`donor_id`, `local_row`, `matrix_id`, `operator_index`, and where applicable `cell_id`). This is not a real-data failure. Preserve the production selector contract and repair the stale tests to the real schema.

Immediate real-TD task:

`REPAIR_STALE_G6_SYNTHETIC_TEST_FIXTURES__NEW_EXACT_COMMIT__FRESH_QUALIFICATION__NO_G6_EXECUTION`

First real G6 at `fafd4309` remains preserved as:

`ATTEMPT_0_SCHEMA_QUALIFICATION_FAILURE__NO_H5AD_VALUE_READ`

It is not a biological failure. `G6_OUT_fafd4309` is immutable historical evidence.

G7 remains blocked.
Corrected TD56/57B/57C/59 remain blocked.
TD60 remains never qualifyingly executed and must never be called failed.
Target selection, representation selection in this lane, Stage4 and real training remain blocked.
V79 is a separate lane.
