# Macha Runbook — Real Target Discovery + Parallel Lane Coordination — 2026-10-11

Primary context:

`docs/agent/TARGET_DISCOVERY_MASTER_HANDOFF_20261011.md`

This is the controlling operational note for Macha while the real target-discovery lane is active.

## 1. Lane separation

### Lane A — REAL target discovery

Current allowed action:

- execute **replacement G6 exactly once** at exact qualified head `ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0`;
- use the fresh owner/runtime authority below;
- write to a fresh never-used namespace;
- preserve all outputs/logs/hashes;
- **STOP after G6 for external audit**.

Forbidden until separately authorized:

- G7 before external G6 audit;
- corrected TD56/57B/57C/59 replay;
- TD60;
- target selection;
- representation selection;
- Stage4;
- real training.

### Lane B — V79 / synthetic

Separate lane. Do not mix code, caches, evidence, authority, output namespaces, claims, or terminals into REAL_TD. V79 is currently on hold unless explicitly resumed.

### Lane C — foundation representation

Separate lane. No representation winner. Do not use representation results to skip target qualification.

## 2. Qualified replacement-G6 implementation

Executable branch:

`fix/td-g6-global-row-binding-successor-20261011`

Exact head:

`ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0`

Fresh qualification evidence:

- branch `qual/td-g6-global-row-successor-ff4a21f9-20261011`
- commit `8622f57e67389e3899e76ca7b1dfcc6addd4a3e6`
- focused suite **219 passed / 0 failed**
- real Sample-A gate `PASS_REAL_SAMPLE_FREEZE_SCHEMA_AND_GLOBAL_ROW_BINDING`
- Sample A 25,000 rows: SEA_AD 22,561 / NPH52 1,310 / HVS 1,129
- no physical `global_row`; derived rows exactly `0..24999`
- PR #259 compatibility **1 passed / 0 skipped / 0 failed**
- exact HEAD clean before/after
- no H5AD value read and no G6/G7 execution during qualification.

Qualified code identities:

- common `23be96f8f2c02bf10b751b599ccfa5fb15ba93a456f22b2cad73c1a3294ae7ea`
- G6 `8e6504e02e909a030a33b3fa2b4742fd78354486c1d2a0f40575c11108a6877d`
- G7 `f8e527104c60a7b6fa307558f97158f004ea485846f5b1ea984a3eef5d1e71fe`

## 3. Fresh authority

Materialize these files byte-for-byte from branch:

`audit/target-discovery-takeover-20261011`

Owner decision:

`custody/owner_decisions/20261011/TD_G6G7_OWNER_DECISION_ff4a21f9.json`

Physical SHA-256:

`3d457d4dc484cb46c71925e306f33367ed064d3bf84878512e84391f5ea01a3a`

Runtime authorization:

`custody/owner_decisions/20261011/TD_G6G7_RUNTIME_AUTHORIZATION_ff4a21f9.json`

Physical SHA-256:

`28b3a0c8ed90afe8f8c4d5ab31fe9080303ad3599bf753bbdd55aebe022f3dc7`

Operational authorization:

`EXECUTE_REPLACEMENT_G6_ONCE_AT_ff4a21f9__FRESH_NAMESPACE__STOP_FOR_EXTERNAL_AUDIT`

Do not reuse historical `fafd4309` authority files.

## 4. Public-data / safety-tooling ruling

HVS, NPH52, SEA-AD, Morabito and associated donor/sample/pathology annotations used here are public research releases. A local Claude Code safety classifier previously labelled some operations as PII handling / auto-mode bypass. Treat that as an **automation/tooling restriction**, not a scientific finding that the project data are private/confidential.

If the safety tool blocks execution again:

- report the exact blocked command and classifier result;
- do not route around the block with unrelated tools;
- use only the narrow reviewed permissions needed for this exact worktree/Python/output path;
- do not broaden permissions globally;
- do not create a new scientific/governance blocker merely because the classifier fired.

## 5. Preserve old records

Never edit, delete, rename-in-place, or reuse:

`D:\jepa_td_real_g6_20261011\G6_OUT_fafd4309`

Classification:

`ATTEMPT_0_SCHEMA_QUALIFICATION_FAILURE__NO_H5AD_VALUE_READ`

Start-marker SHA:

`ae85dd14d17454a104204543312df332bedeae4ea45a9838f9fc9893a80e5894`

Also preserve failed qualification evidence:

`qual/td-g6-global-row-successor-7e482cf5-20261011@e4d771cb6d76f9d783b81ddb4e1691c8f4091fd0`

Historical failure must remain visible even though the successor is now qualified.

## 6. Replacement-G6 preflight

Create a fresh clean detached worktree at exact `ff4a21f9...`.

Before creating a new G6 namespace, require all of the following to match exactly:

- HEAD `ff4a21f9e470f26e34a935b6a4c7c61b03a6dfb0`;
- clean worktree;
- common/G6/G7 identities above;
- owner decision SHA above;
- runtime authorization SHA above;
- PR259 driver/preflight `62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae`;
- PR259 mapping `6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0`;
- replay manifest `4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660`;
- Sample-A freeze `79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6`;
- provenance `df0cb60f2308c08adaeacb1db5d1099c9cd12e90323af8e3958c428d6869cd51`;
- collision ledger `f6909f81a2e73383b4346f8cf6d8b3ecfc282f81bfb42d695c6d6896b6c74722`;
- S174/Macha freeze `240b2b71a94802477ca726a2b4bb020d2ad5542ccf31c4e732906008f81e967c`;
- TD archive `c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417`;
- historical CSR data `0276be0538515146a66012fc9f871eebff2b5cab4de644a7a3a20c29242ef72e`;
- historical CSR indices `f1fc3200adfcebaa5a1214a4f4259fd5a469f6ddbd1379ad73b1222a440e9771`;
- historical CSR indptr `58182d0a8fb8af88cc5b010775056b04e637279669d352b85935ef36d66cf4b1`;
- historical CSR shape `5547a1cd96a984b5163c5540a616006baca3d2a91985005a8f23e970a3133beb`;
- all frozen H5AD source files required by PR259 are present and unchanged;
- destination output namespace has never existed.

Do not pre-emptively modify production code or fixtures during execution.

The successor performs metadata/schema/global-row/TD50/CSR compatibility checks before the immutable start marker. If any pre-marker check fails, preserve the evidence and stop; do not create a replacement namespace and immediately retry without owner review.

## 7. Execute G6 exactly once

Use the qualified V2 G6 entrypoint from the exact worktree head. Record:

- exact command;
- exact worktree path;
- exact output namespace;
- environment;
- HEAD and clean status;
- stdout and stderr;
- precondition pin record.

Once `G6_EXECUTION_START.json` exists, the attempt namespace is immutable evidence. Any exception, mismatch, non-PASS terminal, or partial execution after that point consumes that namespace. Do not repair/delete/rerun it in place.

Expected PASS terminal:

`PASS_TD_G6_SOURCE_LIBRARY_EXACT`

Expected exact success file set:

1. `G6_EXECUTION_START.json`
2. `G6_RECEIPT.json`
3. `MANIFEST.json`
4. `TD_RELATIONAL_CORRECTED_SAMPLE_A_9216_VALUES_V2.npz`
5. `TD_RELATIONAL_CORRECTED_SAMPLE_A_META_V2.npz`

Expected source accounting:

- HVS + SEA_AD physical reread: `23,690`
- NPH52 authenticated historical pass-through: `1,310`
- total Sample A: `25,000`

G6 itself must reauthenticate the physical H5AD sources at value-read time.

## 8. Required return package to external auditor

On PASS, return all of the following without interpretation inflation:

- lane `REAL_TD`;
- exact branch and full HEAD;
- exact command;
- exact output namespace;
- whether marker was created;
- whether corrected H5AD values were opened;
- terminal;
- SHA-256 for all five files;
- `G6_RECEIPT.json` contents;
- `MANIFEST.json` contents;
- source authentication counts;
- physical reread/pass-through counts;
- warnings;
- stdout/stderr paths and hashes if recorded;
- whether any source identity, path, size, or frozen pin differed;
- explicit statement that no G7/corrected replay/TD60/target selection/training followed.

Do not describe a custody PASS as biological validation.

## 9. STOP after G6

**DO NOT RUN G7.**

The external auditor/new agent must first accept the actual G6 namespace, its five-file set, hashes, receipt semantics, source accounting, physical-value-read accounting, and one-shot custody.

Only after that may a new operational G7 authorization be issued.

Do not run corrected TD56/57B/57C/59, TD60, target selection, representation selection, Stage4, or training.

## 10. Coordination with PR #275

PR #275 is already software/governance-qualified at exact head:

`0cbe6244756df3d1b7ed1ef4e1643aae0f94e875`

with **197 passed / 0 failed / 0 errors** and terminal:

`PASS_FULL_SYNTHETIC_METADATA_ONLY_V2_AUTHENTICATED_REGISTRY_TO_ADJUDICATION_CHAIN_197_OF_197`

Macha does not need to work on PR #275 for the current real-TD operation. Do not instantiate a real target tournament or feed G6 results into that machinery until G6+G7 and corrected TD56/57B/57C/59 are separately completed and audited.
