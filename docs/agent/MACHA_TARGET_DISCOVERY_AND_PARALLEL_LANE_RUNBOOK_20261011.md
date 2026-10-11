# Macha Runbook — Real Target Discovery + Parallel Lane Coordination — 2026-10-11

This is the controlling coordination note for Macha while the real target-discovery lane is active.

## 1. Lane separation

### Lane A — REAL target discovery

Current allowed action:

- execute the **replacement G6 exactly once** at qualified head `ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0` under the fresh owner/runtime authority below;
- preserve and return all output/logs/hashes;
- STOP after G6 for external audit.

Forbidden until separately authorized:

- G7 before external G6 audit;
- corrected TD56/57B/57C/59 replay;
- TD60;
- target selection;
- representation selection;
- Stage4;
- real training.

### Lane B — V79

Separate PR #280 lane. Do not mix code, caches, evidence, authority, output namespaces or claims into real TD.

## 2. Qualified replacement G6 implementation

Executable branch:

`fix/td-g6-global-row-binding-successor-20261011`

Exact head:

`ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0`

Fresh qualification evidence:

- branch `qual/td-g6-global-row-successor-ff4a21f9-20261011`
- commit `8622f57e67389e3899e76ca7b1dfcc6addd4a3e6`
- focused suite `219 passed / 0 failed`
- real Sample-A freeze gate `PASS_REAL_SAMPLE_FREEZE_SCHEMA_AND_GLOBAL_ROW_BINDING`
- PR259 compatibility `1 passed / 0 skipped / 0 failed`
- clean exact head before/after
- no H5AD value read during qualification

Qualified identities:

- common `23be96f8f2c02bf10b751b599ccfa5fb15ba93a456f22b2cad73c1a3294ae7ea`
- G6 `8e6504e02e909a030a33b3fa2b4742fd78354486c1d2a0f40575c11108a6877d`
- G7 `f8e527104c60a7b6fa307558f97158f004ea485846f5b1ea984a3eef5d1e71fe`

## 3. Fresh authority

Materialize these files byte-for-byte from audit branch `audit/target-discovery-takeover-20261011`:

Owner decision:

`custody/owner_decisions/20261011/TD_G6G7_OWNER_DECISION_ff4a21f9.json`

Physical SHA-256:

`3d457d4dc484cb46c71925e306f33367ed064d3bf84878512e84391f5ea01a3a`

Runtime authorization:

`custody/owner_decisions/20261011/TD_G6G7_RUNTIME_AUTHORIZATION_ff4a21f9.json`

Physical SHA-256:

`28b3a0c8ed90afe8f8c4d5ab31fe9080303ad3599bf753bbdd55aebe022f3dc7`

Do not reuse the historical `fafd4309` authority files.

## 4. Preserve old records

Do not edit, delete, rename-in-place or reuse:

`D:\jepa_td_real_g6_20261011\G6_OUT_fafd4309`

Classification:

`ATTEMPT_0_SCHEMA_QUALIFICATION_FAILURE__NO_H5AD_VALUE_READ`

Start-marker SHA:

`ae85dd14d17454a104204543312df332bedeae4ea45a9838f9fc9893a80e5894`

Also preserve failed qualification record:

`qual/td-g6-global-row-successor-7e482cf5-20261011@e4d771cb6d76f9d783b81ddb4e1691c8f4091fd0`

## 5. Replacement G6 preflight

Create a fresh clean detached worktree at exact `ff4a21f9...`.

Before creating a new G6 namespace, require:

- exact HEAD `ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0`;
- clean worktree;
- qualified common/G6/G7 identities above;
- fresh owner/runtime files and exact physical SHA values above;
- PR259 driver `62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae`;
- PR259 mapping `6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0`;
- replay manifest `4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660`;
- Sample-A freeze `79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6`;
- provenance `df0cb60f2308c08adaeacb1db5d1099c9cd12e90323af8e3958c428d6869cd51`;
- collision ledger `f6909f81a2e73383b4346f8cf6d8b3ecfc282f81bfb42d695c6d6896b6c74722`;
- Macha freeze `240b2b71a94802477ca726a2b4bb020d2ad5542ccf31c4e732906008f81e967c`;
- TD artifacts ZIP `c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417`;
- historical CSR member pins:
  - data `0276be0538515146a66012fc9f871eebff2b5cab4de644a7a3a20c29242ef72e`
  - indices `f1fc3200adfcebaa5a1214a4f4259fd5a469f6ddbd1379ad73b1222a440e9771`
  - indptr `58182d0a8fb8af88cc5b010775056b04e637279669d352b85935ef36d66cf4b1`
  - shape `5547a1cd96a984b5163c5540a616006baca3d2a91985005a8f23e970a3133beb`.

The destination output namespace must be new and never previously used.

The repaired successor performs metadata/schema/global-row/TD50/CSR checks before its immutable G6 marker. If a pre-marker check fails, preserve evidence and stop.

## 6. Execute G6 exactly once

Use the qualified V2 G6 entrypoint at the exact worktree head. Record the exact command, environment, stdout/stderr, HEAD, clean status and output namespace.

Once `G6_EXECUTION_START.json` exists, preserve every outcome. Do not repair/delete/rerun that namespace without a new owner decision.

Expected successful terminal:

`PASS_TD_G6_SOURCE_LIBRARY_EXACT`

Expected exact success file set:

- `G6_EXECUTION_START.json`
- `G6_RECEIPT.json`
- `MANIFEST.json`
- `TD_RELATIONAL_CORRECTED_SAMPLE_A_9216_VALUES_V2.npz`
- `TD_RELATIONAL_CORRECTED_SAMPLE_A_META_V2.npz`

Expected accounting:

- HVS+SEA physically reread: `23,690`
- NPH52 authenticated historical pass-through: `1,310`
- total Sample A: `25,000`

Hash all five artifacts on PASS and return exact SHA-256 values, receipt/manifest contents and source-authentication accounting.

## 7. STOP after G6

**DO NOT RUN G7.**

External auditor must accept the replacement G6 namespace before any operational G7 authority is issued.

Do not run corrected TD56/57B/57C/59, TD60, target selection, representation selection, Stage4 or training.

## 8. Reporting discipline

Every report must state:

- lane: `REAL_TD`;
- exact branch/SHA;
- exact command;
- whether a G6 marker was created;
- whether corrected H5AD values were opened;
- exact terminal;
- output namespace and artifact hashes;
- downstream actions that remain unauthorized.

Do not describe a custody PASS as biological validation.

## 9. V79 reminder

V79 remains separate at PR #280 and is not authorized to influence this G6 execution.
