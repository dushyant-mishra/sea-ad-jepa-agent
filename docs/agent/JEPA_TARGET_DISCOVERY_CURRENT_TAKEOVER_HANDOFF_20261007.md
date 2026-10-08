# JEPA Target Discovery — current takeover handoff

Date: 2026-10-07
Branch: `governance/stage-a-prefreeze-decisions-20261007`
Parent audit head: `121449cd99c7f13c67ccf8421848e6d26e39e474`
Status: `TARGET_DISCOVERY_REPLAY_PREFLIGHT_IN_PROGRESS__NO_REAL_VALUE_REPLAY_AUTHORITY__NO_TARGET_WINNER__NO_TRAINING_AUTHORITY`

## Start here

This file is the current entry point for the Target Discovery lane. Do not reconstruct the lane from older chats or from the initial Stage-A prefreeze files alone.

Read, in this order:
1. `docs/agent/JEPA_STAGE_A_PREFREEZE_SELF_AUDIT_CORRECTION_20261007.md`
2. `docs/agent/JEPA_TARGET_DISCOVERY_RELATIONAL_REPLAY_SCOPE_CORRECTION_20261007.md`
3. `docs/agent/JEPA_TD56_TD59_HISTORICAL_PANEL_RECOVERY_RECEIPT_20261007.md`
4. `docs/agent/JEPA_TD_RELATIONAL_REPLAY_9216_RECEIPT_20261007.json`
5. `docs/agent/JEPA_TD_SAMPLE_A_ROW_IDENTITY_RECEIPT_20261007.json`
6. `docs/agent/JEPA_TD_RELATIONAL_CORRECTED_25K_REPLAY_CONTRACT_20261007.md`
7. `docs/agent/JEPA_MACHA_V77_CROSS_LANE_AUDIT_20261007.md`
8. `docs/agent/JEPA_HVS_SEAAD_PHYSICAL_AXIS_REPAIR_CONTRACT_20261007.md`

## Superseded / corrected statements

The original `JEPA_STAGE_A_PREFREEZE_DECISIONS_20261007.*` files are historical records, not current authority where they conflict with the self-audit correction.

Current corrections:
- Foundation-model estimand is `UNSET`.
- Stage-A population is `UNSET`.
- Stage-A deciding donor split is `UNSET`.
- The historical 104 reader-fit donors / 68-36 split are not current Stage-A authority.
- `QUERY_EXCHANGEABILITY` is a q-locality/shortcut prerequisite, not the deciding global-vs-global+local incremental test.
- TD56-TD59 relational results are historical candidate evidence requiring corrected replay where HVS/SEA-AD values came from the defective feature-axis materialization.
- NPH52 is not affected by the same HVS/SEA positional-axis defect, but that does not make every historical NPH result globally qualified for all purposes.
- No target winner, representation winner, TD60 authority, or training authority exists.

## Physical-axis defect and Macha cross-lane authority

The historical HVS/SEA-AD materializer used a provenance/sorted ordinal as if it were the physical sparse-H5 column. That defect contaminates historical HVS/SEA-AD value-level conclusions built from the affected cache/materialization.

Macha lane (`claude/s174-train-cache-rebuild-20261007`) has already:
- proven the V77 cache followed the scrambled positional mapping;
- implemented the corrected identifier-based physical mapping for that cache scope;
- rebuilt and replayed S149 under corrected input;
- shown several earlier synthetic-lane interpretations were tied to inflated/scrambled real targets.

Do not duplicate Macha's S174 value sentinels. Reuse his identifier-join policy and receipts as cross-lane evidence. His corrected V77 cache is not a substitute for the historical Target Discovery 25K Sample-A rows.

## Exact historical relational replay universe — CLOSED

The all-42-operator common measured-scalar core has been reconstructed exactly:
- rows: 17,186
- historical CSV SHA-256: `8aa8dfebb481aa2e60b12ab0f581ba1a36063b6c12dc2d8514d5fe7a20ad07ac`

The TD56→TD59 lineage uses SHA-ranked positions 0..9215 only under:
`SHA256("TD56S|gene|<molecular_address_index>")`.

Exact 9,216-address manifest:
- SHA-256: `4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660`
- status: `PASS_EXACT_HISTORICAL_RELATIONAL_REPLAY_MANIFEST`

Validated against:
- preserved TD57B gene arrays and pair hashes;
- preserved TD57C Panel-0 gene arrays and pair hashes;
- every prospectively frozen TD59 gene and pair hash.

Historical allocation:
- 0..1023: TD56 / TD57A / TD58
- 1024..3071: TD57B
- 3072..6143: TD57C
- 6144..9215: TD59

Never recompute a new corrected gene panel or replace an unresolved historical gene. Missing/noninjective frozen address => `NOT_ESTIMABLE` / STOP for the affected gate.

## Exact historical Sample-A row identity — CLOSED

`FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv` authority SHA-256:
`79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6`

Exact historical `A_NATURAL_MIXTURE` identity is recovered and authenticated:
- total: 25,000 rows
- HVS: 1,129
- NPH52: 1,310
- SEA_AD: 22,561
- Sample-A identity CSV SHA-256: `8fad0f85129b902876048f94ac15399a116d064294cc7849c72c740b1a8c2573`
- status: `PASS_EXACT_HISTORICAL_SAMPLE_A_ROW_IDENTITY`

Identity columns include:
`global_row, sample_row, source, matrix_id, operator_index, local_row, donor_id, cell_id, stable_key`.

Therefore do not resample cells or infer row identity from the corrupted 50K value matrix.

## Minimal corrected replay contract

Do not rebuild the full 41,238-address 50K matrix.

Required corrected materialization:
- rows: exact 25,000 Sample-A cells, original order;
- logical shape: `(25000, 41238)` to preserve canonical address indexing;
- stored value columns: only the exact 9,216 replay addresses;
- normalization: `log1p(raw_count * 10000 / full_source_library)`;
- HVS physical feature IDs from native `raw/var`;
- SEA-AD physical feature IDs from native `var/gene_ids`;
- NPH52 through its separate audited identity path;
- no gene replacement, no new panel, no new threshold, no new donor split.

Historical replay order must remain:
1. TD56
2. TD57A
3. TD58
4. TD57B
5. TD57C using the original sequential stop rule
6. TD59

TD57C's historical HVS FAIL remains recorded as history, but its current scientific status is `REPLAY_REQUIRED` because the HVS numeric substrate was affected.

## Current executable support

### 1. Replay-manifest generator
`scripts/v5/build_td_relational_replay_manifest.py`

Purpose:
- reconstruct the exact 17,186 common core from frozen support authorities;
- derive the exact first 9,216 TD56S-ranked addresses;
- validate preserved TD57B/TD57C arrays and TD59 hashes;
- fail closed if historical identity changes.

Test:
`tests/v5/test_build_td_relational_replay_manifest.py`

### 2. HVS/SEA physical-axis metadata verifier
`scripts/v5/verify_hvs_seaad_physical_axis_metadata.py`

Purpose:
- inspect feature metadata only;
- verify expected native feature order/hash without reading expression arrays.

Test:
`tests/v5/test_verify_hvs_seaad_physical_axis_metadata.py`

### 3. Target-Discovery mapping preflight
`scripts/v5/audit_td_relational_replay_mapping_preflight.py`

Purpose:
- VALUE-BLIND preflight over exact 9,216 addresses and exact Sample-A rows;
- reuse the S174 identifier-join policy;
- open only H5AD `var` and `obs`, never count arrays;
- require every historical replay address to resolve one-to-one;
- verify exact Sample-A cell/local-row identity;
- fail closed on ledger collisions, join collisions, unresolved addresses, missing matrices, or row mismatch.

Tests:
`tests/v5/test_audit_td_relational_replay_mapping_preflight.py`

The current mapping preflight explicitly does **not** authorize real-value replay.

## Next safe step

Run the value-blind mapping preflight in the canonical local JEPA environment where the native HVS/SEA H5AD files and the following frozen authorities are present:
- exact 9,216 replay manifest;
- exact `FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv`;
- provenance map expected by S174 identifier join;
- collision ledger;
- Macha S174 freeze/asset inventory;
- native source H5AD root.

Required outcome before any count value is opened:
`PASS_TD_RELATIONAL_MAPPING_PREFLIGHT_VALUE_BLIND`.

If any matrix/address/cell fails, STOP. Do not substitute a gene, cell, matrix, or new support definition.

After that PASS, remaining pre-value gates are:
1. source asset identities/size bindings remain exact;
2. raw whole-cell library-size and detected-gene sentinels must reproduce for every replay cell during materialization;
3. small overlap with existing S174 decoder/value sentinels must agree;
4. write corrected data to a new immutable namespace; never overwrite historical 50K artifacts.

Only then can corrected real values be materialized under separately explicit authority.

## What a future agent must NOT do

- Do not treat the old 50K HVS/SEA values as current numeric authority.
- Do not substitute Macha's V77 rebuilt cache for TD Sample-A.
- Do not recompute a new 17,186 core from corrected expression outcomes and then change the historical panels.
- Do not reinterpret TD57C historical FAIL as currently binding without replay.
- Do not use `QUERY_EXCHANGEABILITY` as proof that q-local information adds beyond a global/relational representation.
- Do not select `DONOR_WEIGHTED`, 104 donors, 68/36 split, or 2,464 exact query panel membership as production/Stage-A authority merely because earlier prefreeze notes proposed them.
- Do not run TD60, training, TEST, DEV/SEALED, Morabito, pathology, or external biological qualification from this lane.

## Current scientific question after replay

The replay is not a new target tournament. It asks only:
**Which historical relational claims survive correction of the HVS/SEA physical-feature-axis defect under their exact original frozen rules?**

Only after this is known should the project return to Stage-A representation qualification and separately ask whether q-safe local/program information adds held-donor information beyond the surviving global/relational state.
