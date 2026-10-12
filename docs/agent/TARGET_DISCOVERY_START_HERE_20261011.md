# Target Discovery — START HERE — 2026-10-11

For a new agent taking over the **real target-discovery lane**, read in this order:

1. `docs/agent/TD_G7_CURRENT_GATE_ff4a21f9_20261011.md` — current operational gate after accepted G6.
2. `docs/agent/TARGET_DISCOVERY_MASTER_HANDOFF_20261011.md` — complete scientific + operational takeover.
3. `docs/agent/TARGET_DISCOVERY_CANONICAL_STATE_20261011.json` — machine-readable current state.
4. `docs/agent/TD_G6_EXTERNAL_ACCEPTANCE_ff4a21f9_20261011.json` — external acceptance of replacement G6.
5. `custody/owner_decisions/20261011/TD_G7_OPERATIONAL_AUTHORIZATION_ff4a21f9.json` — one-shot G7 operational release.
6. `docs/agent/TARGET_DISCOVERY_CURRENT_HANDOFF_20261011.md` — historical short current-state overlay; use the G7 gate note above for the newest operational state.
7. `docs/agent/MACHA_TARGET_DISCOVERY_AND_PARALLEL_LANE_RUNBOOK_20261011.md` — execution contract and stop discipline.
8. `docs/agent/TARGET_DISCOVERY_EVIDENCE_CODE_DATA_INDEX_20261011.md` — hashes, code, data, evidence navigation.
9. `docs/agent/TD_G6_ATTEMPT0_EXECUTION_RECORD_20261011.md` — immutable first real G6 failure record.
10. `docs/agent/TARGET_DISCOVERY_HISTORY_AND_AUDIT_LESSONS_20261011.md` — causal history and audit lessons.
11. `docs/agent/TD_V2_GOVERNANCE_QUALIFICATION_20261011.md` — PR #275 V2 governance qualification history.
12. Accepted replacement-G6 evidence: `evidence/td-g6-replacement-ff4a21f9-20261011@c595af589821bee28eb77e88e44b79dc81835e7a`.
13. Successful G6-successor qualification evidence: `qual/td-g6-global-row-successor-ff4a21f9-20261011@8622f57e67389e3899e76ca7b1dfcc6addd4a3e6`.
14. Failed predecessor qualification evidence: `qual/td-g6-global-row-successor-7e482cf5-20261011@e4d771cb6d76f9d783b81ddb4e1691c8f4091fd0`.
15. `docs/superpowers/specs/2026-10-11-td-corrected-replay-interpretation-prefreeze.md`.
16. `docs/superpowers/specs/2026-10-11-td-multitarget-tournament-prefreeze-v2.md`.
17. `target_discovery/HANDOFF_CURRENT_20260907.md` and `target_discovery/iterations/td33_global_row_binding_guard/TD33_SUMMARY.json` for deeper historical context.

Current hard terminal:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Current real-TD state

PR #282 exact qualified executable head:

`ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0`

Replacement G6 executed exactly once and is externally accepted:

`ACCEPT_G6_PASS__VALUE_SUBSTRATE_AND_SOURCE_CUSTODY_CONFIRMED__NO_BIOLOGICAL_TARGET_AUTHORITY`

G6 evidence:
- evidence commit `c595af589821bee28eb77e88e44b79dc81835e7a`
- receipt terminal `PASS_TD_G6_SOURCE_LIBRARY_EXACT`
- receipt SHA-256 `2edaa2d2e03b8d862172e97b35fb94888305ef0e843cd71206ee56f53b28a52b`
- values SHA-256 `fdc13516a31a4163498cfc1bb9b9dd5fc615bc4ba8e7ec3fd3f4a51522e344a9`
- metadata SHA-256 `bd3a494b3dd8239a78485dfc6006e75a75c32e5f2eb0a33afd2da2472522fe74`
- HVS+SEA physical reread 23,690; NPH52 pass-through 1,310; total 25,000
- detected-count changes are confined to SEA_AD (22,560 rows); this is diagnostic only and not biological authority.

## Current authorized next action

Fresh G7 operational authorization:

`custody/owner_decisions/20261011/TD_G7_OPERATIONAL_AUTHORIZATION_ff4a21f9.json`

SHA-256:

`19a50126219d25989ca466a83b813fcbabdeeb148804e1f616bbb7bbdfe3b4ee`

Operational scope:

`EXECUTE_G7_ONCE_AT_ff4a21f9__AGAINST_ACCEPTED_G6__FRESH_OUTPUT__STOP_FOR_EXTERNAL_AUDIT`

Expected PASS terminal:

`PASS_TD_G7_S174_EXACT_OVERLAP`

G7 is one attempt only. Use a fresh output and stop after G7 for external audit.

The G7 executable still consumes the exact original G6/G7 integrity authority bytes:
- owner decision SHA-256 `3d457d4dc484cb46c71925e306f33367ed064d3bf84878512e84391f5ea01a3a`
- runtime authorization SHA-256 `28b3a0c8ed90afe8f8c4d5ab31fe9080303ad3599bf753bbdd55aebe022f3dc7`.

## Still blocked

Corrected TD56/57B/57C/59 replay remains blocked until G7 is externally accepted and a separate corrected-replay authority is issued.

TD60, target selection, representation selection, Stage4 and training remain blocked.

Historical `G6_OUT_fafd4309` remains immutable as:

`ATTEMPT_0_SCHEMA_QUALIFICATION_FAILURE__NO_H5AD_VALUE_READ`

TD60 remains never qualifyingly executed and must never be called failed. V79 and foundation representation remain separate lanes.
