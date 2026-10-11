# Target Discovery — Current Takeover Handoff — 2026-10-11

Status: **ACTIVE REAL TARGET-DISCOVERY LANE**

Hard terminal:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

This is the current-state addendum to the canonical takeover package in PR #284. Historical/scientific detail remains in `TARGET_DISCOVERY_CANONICAL_TAKEOVER_20261011.md`; this file controls the immediate operational state.

## 1. Latest state: PR #282 successor is qualified for replacement G6 integrity execution

Executable branch:

`fix/td-g6-global-row-binding-successor-20261011`

Exact qualified head:

`ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0`

This commit is exactly one test-only child of failed-qualification head `7e482cf50f73a5cecda16482777129dd3ca725a6`. The only changed files are:

- `tests/v5/test_materialize_td_relational_corrected_sampleA_v2.py`
- `tests/v5/test_td_v2_sample_a_row_order.py`

The production `select_sample_a()` contract and common/G6/G7 production scripts were not weakened or changed by the fixture repair.

## 2. Fresh qualification — accepted

Evidence branch:

`qual/td-g6-global-row-successor-ff4a21f9-20261011`

Evidence commit:

`8622f57e67389e3899e76ca7b1dfcc6addd4a3e6`

Authoritative raw evidence directory:

`docs/agent/TD_G6G7_FULL_CUSTODY_SUCCESSOR_20261011/qualification_ff4a21f9/`

Accepted gates:

1. Focused G6/G7 suite including `test_td_g6_global_row_binding.py`: **219 passed / 0 failed**.
2. Authenticated real Sample-A freeze SHA `79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6`: **PASS** with `PASS_REAL_SAMPLE_FREEZE_SCHEMA_AND_GLOBAL_ROW_BINDING`; no physical `global_row`; derived rows exactly `0..24999`; 25,000 rows with SEA_AD 22,561, NPH52 1,310, HVS 1,129.
3. Exact PR #259 compatibility: **1 passed / 0 skipped / 0 failed**; replay manifest pin `4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660` matches.
4. Exact head before/after `ff4a21f9...`; worktree clean before and after.
5. No H5AD value read; no G6/G7 execution during qualification.

Qualified production identities:

- common `23be96f8f2c02bf10b751b599ccfa5fb15ba93a456f22b2cad73c1a3294ae7ea`
- G6 `8e6504e02e909a030a33b3fa2b4742fd78354486c1d2a0f40575c11108a6877d`
- G7 `f8e527104c60a7b6fa307558f97158f004ea485846f5b1ea984a3eef5d1e71fe`

Qualification terminal:

`QUALIFIED_FOR_REPLACEMENT_G6_INTEGRITY_EXECUTION__NO_BIOLOGICAL_AUTHORITY`

## 3. Fresh owner/runtime authority — created after external audit

Owner decision:

`custody/owner_decisions/20261011/TD_G6G7_OWNER_DECISION_ff4a21f9.json`

Physical SHA-256:

`3d457d4dc484cb46c71925e306f33367ed064d3bf84878512e84391f5ea01a3a`

Runtime authorization:

`custody/owner_decisions/20261011/TD_G6G7_RUNTIME_AUTHORIZATION_ff4a21f9.json`

Physical SHA-256:

`28b3a0c8ed90afe8f8c4d5ab31fe9080303ad3599bf753bbdd55aebe022f3dc7`

The authority binds exact implementation `ff4a21f9...`, exact common/G6/G7 identities, exact PR259 preflight/mapping/manifest pins, and keeps biological replay, target selection, TD60 and training explicitly false.

Operational authority is **replacement G6 only**. G7 remains blocked until external audit accepts the replacement G6 namespace.

## 4. Immediate Macha task

Execute replacement G6 exactly once from a fresh clean detached worktree at exact `ff4a21f9...`, under the fresh owner/runtime files above, into a fresh never-used namespace.

Before execution:

- materialize the two authority files byte-for-byte from the audit branch and verify the two physical SHA-256 values above;
- verify exact HEAD/clean worktree and the three code identities;
- verify PR259 driver/mapping/manifest pins;
- verify historical CSR member hashes;
- verify Sample-A freeze, provenance, collision ledger, Macha freeze and TD artifacts pins;
- require the new namespace never existed.

The repaired successor must complete metadata/schema/global-row/TD50/CSR compatibility checks before creating `G6_EXECUTION_START.json`.

After a start marker exists, preserve every outcome and do not repair or rerun in place.

Expected PASS terminal:

`PASS_TD_G6_SOURCE_LIBRARY_EXACT`

Expected successful five-file namespace:

- `G6_EXECUTION_START.json`
- `G6_RECEIPT.json`
- `MANIFEST.json`
- `TD_RELATIONAL_CORRECTED_SAMPLE_A_9216_VALUES_V2.npz`
- `TD_RELATIONAL_CORRECTED_SAMPLE_A_META_V2.npz`

Expected row accounting:

- HVS+SEA physical reread: 23,690
- NPH52 authenticated historical pass-through: 1,310
- total: 25,000

**STOP AFTER G6. DO NOT RUN G7.**

## 5. Preserved predecessor records

First real G6 at implementation `fafd4309cc086c95076cefdc94064e8b66e58ae4` remains:

`ATTEMPT_0_SCHEMA_QUALIFICATION_FAILURE__NO_H5AD_VALUE_READ`

`G6_OUT_fafd4309` remains immutable historical evidence; start-marker SHA `ae85dd14d17454a104204543312df332bedeae4ea45a9838f9fc9893a80e5894`.

Failed qualification of `7e482cf5...` remains immutable at:

`qual/td-g6-global-row-successor-7e482cf5-20261011@e4d771cb6d76f9d783b81ddb4e1691c8f4091fd0`

It failed Gate 1 with 4 stale synthetic fixture failures while real Sample-A and PR259 gates passed. Do not rewrite that history.

## 6. Downstream state

G7: blocked pending external audit of replacement G6.

Corrected TD56/TD57B/TD57C/TD59 replay: blocked pending accepted G6+G7 and separate owner authority.

Historical outcomes remain:

- TD56 historical positive;
- TD57B historical 24/24 positive;
- TD57C immutable historical FAIL;
- TD59 historical 24/24 positive;
- TD60 `PROSPECTIVELY_FROZEN__NEVER_QUALIFYINGLY_EXECUTED__NO_CURRENT_AUTHORITY` — never call it failed.

No target winner. No representation winner. Stage4/training off.

V79 remains a separate lane and must not contaminate this execution.
