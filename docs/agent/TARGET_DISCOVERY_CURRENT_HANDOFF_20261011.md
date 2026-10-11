# Target Discovery — Current Takeover Handoff — 2026-10-11

Status: **ACTIVE REAL TARGET-DISCOVERY LANE**

Primary takeover document:

`docs/agent/TARGET_DISCOVERY_MASTER_HANDOFF_20261011.md`

This file is the short operational overlay. The master handoff carries the full scientific history, target-discovery evidence, data/code hashes, audit lessons, PR #275 governance lineage, Macha runbook context, and downstream decision tree.

Hard terminal:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## 1. Current executable state: PR #282

Branch:

`fix/td-g6-global-row-binding-successor-20261011`

Exact qualified head:

`ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0`

Fresh qualification evidence:

- branch `qual/td-g6-global-row-successor-ff4a21f9-20261011`
- commit `8622f57e67389e3899e76ca7b1dfcc6addd4a3e6`
- focused G6/G7 suite: **219 passed / 0 failed**
- real Sample-A freeze: `PASS_REAL_SAMPLE_FREEZE_SCHEMA_AND_GLOBAL_ROW_BINDING`
- real Sample-A rows: 25,000; SEA_AD 22,561 / NPH52 1,310 / HVS 1,129
- no physical `global_row`; derived rows exactly `0..24999`
- PR #259 compatibility: **1 passed / 0 skipped / 0 failed**
- exact head/worktree clean before and after
- no H5AD value read and no G6/G7 execution during qualification

Qualified production identities:

- common `23be96f8f2c02bf10b751b599ccfa5fb15ba93a456f22b2cad73c1a3294ae7ea`
- G6 `8e6504e02e909a030a33b3fa2b4742fd78354486c1d2a0f40575c11108a6877d`
- G7 `f8e527104c60a7b6fa307558f97158f004ea485846f5b1ea984a3eef5d1e71fe`

Qualification terminal:

`QUALIFIED_FOR_REPLACEMENT_G6_INTEGRITY_EXECUTION__NO_BIOLOGICAL_AUTHORITY`

## 2. Fresh authority: replacement G6 only

Owner decision:

`custody/owner_decisions/20261011/TD_G6G7_OWNER_DECISION_ff4a21f9.json`

Physical SHA-256:

`3d457d4dc484cb46c71925e306f33367ed064d3bf84878512e84391f5ea01a3a`

Runtime authorization:

`custody/owner_decisions/20261011/TD_G6G7_RUNTIME_AUTHORIZATION_ff4a21f9.json`

Physical SHA-256:

`28b3a0c8ed90afe8f8c4d5ab31fe9080303ad3599bf753bbdd55aebe022f3dc7`

Operational scope:

`EXECUTE_REPLACEMENT_G6_ONCE_AT_ff4a21f9__FRESH_NAMESPACE__STOP_FOR_EXTERNAL_AUDIT`

**Current status:** replacement G6 is authorized and pending execution/result. G7 is not operationally authorized.

## 3. Macha's immediate task

Execute replacement G6 exactly once from a fresh clean detached worktree at exact `ff4a21f9...`, under the fresh authority above, into a fresh never-used namespace.

Before marker creation, verify all code/authority/PR259/Sample-A/provenance/collision-ledger/S174/TD-artifact/historical-CSR pins listed in `MACHA_TARGET_DISCOVERY_AND_PARALLEL_LANE_RUNBOOK_20261011.md`.

Expected successful terminal:

`PASS_TD_G6_SOURCE_LIBRARY_EXACT`

Expected successful five-file namespace:

- `G6_EXECUTION_START.json`
- `G6_RECEIPT.json`
- `MANIFEST.json`
- `TD_RELATIONAL_CORRECTED_SAMPLE_A_9216_VALUES_V2.npz`
- `TD_RELATIONAL_CORRECTED_SAMPLE_A_META_V2.npz`

Expected accounting:

- HVS + SEA_AD physical reread: 23,690
- NPH52 historical authenticated pass-through: 1,310
- total: 25,000

After marker creation, every outcome is immutable for that namespace. Hash all five artifacts on PASS.

**STOP AFTER G6. DO NOT RUN G7.**

## 4. Preserved failure history

First real G6 at `fafd4309cc086c95076cefdc94064e8b66e58ae4` remains:

`ATTEMPT_0_SCHEMA_QUALIFICATION_FAILURE__NO_H5AD_VALUE_READ`

Historical namespace:

`D:\jepa_td_real_g6_20261011\G6_OUT_fafd4309`

Start-marker SHA-256:

`ae85dd14d17454a104204543312df332bedeae4ea45a9838f9fc9893a80e5894`

No receipt, no corrected H5AD value read, no biological result.

Failed qualification of `7e482cf50f73a5cecda16482777129dd3ca725a6` remains immutable at:

`qual/td-g6-global-row-successor-7e482cf5-20261011@e4d771cb6d76f9d783b81ddb4e1691c8f4091fd0`

It failed 4 stale synthetic fixtures while the real Sample-A and PR259 gates passed. The production selector contract was correctly preserved; only fixtures were repaired.

## 5. Historical biology awaiting corrected replay

- TD56: historical positive relational recurrence
- TD57B: historical 24/24 PASS; weakest p95 margin `+0.0375178074843`
- TD57C: immutable historical `NO_THREE_VIEW_FINE_LOCAL_RELATIONAL_RECURRENCE__TD57C_FAIL`
- TD59: historical 24/24 PASS; weakest p95 margin `+0.0011566307718604563`; 22/24 above null max
- TD60: `PROSPECTIVELY_FROZEN__NEVER_QUALIFYINGLY_EXECUTED__NO_CURRENT_AUTHORITY`

None of the historical positives currently authorize the target because corrected HVS/SEA physical mapping replay is still pending.

## 6. Parallel PR #275 governance state

PR #275 exact qualified head:

`0cbe6244756df3d1b7ed1ef4e1643aae0f94e875`

Qualification:

- run `38183565983`
- job `114601031751`
- artifact `11718374988`
- digest `sha256:585f7799e0aba4935b37b28319570025de67ecf73d9aa7523a5bf6abeb74de61`
- **197 passed / 0 failed / 0 errors**

Terminal:

`PASS_FULL_SYNTHETIC_METADATA_ONLY_V2_AUTHENTICATED_REGISTRY_TO_ADJUDICATION_CHAIN_197_OF_197`

This is synthetic/metadata-only governance qualification. It does not authorize real values, corrected replay, a real tournament, target selection, representation selection, TD60, Stage4, or training.

## 7. Next agent sequence after Macha reports G6

1. Audit the actual five-file G6 namespace, hashes, receipt/manfiest semantics, one-shot custody, source accounting, physical-value-read accounting, and exact authority binding.
2. If and only if accepted, issue fresh operational G7 authority.
3. Audit G7 after execution.
4. If and only if accepted, issue a separate corrected-replay owner decision for TD56/57B/57C/59.
5. Interpret corrected replay under the frozen interpretation document; never rewrite history.
6. Only then consider instantiating a real V2 target tournament under fresh explicit authority.

V79 and foundation representation are separate lanes and must not contaminate this path.