# S174 downstream Library join audit — 2026-10-09

## Scope

This audit answers one narrow question only:

> Does the material currently present in the Project Library physically bind the corrected S174 HVS/SEA-AD TRAIN rebuild to a corrected 50K/TD50 substrate and then to rerun TD56, TD57B, and TD59 results?

It does **not** reopen target discovery, TD34, TD57C, TD60, Nott, SCENIC+, NIH-CARD authority, Stage 4, or training authority.

## Physical Library assets inspected

1. `/Jepa project/s174_rebuilt_real_train_v1.rar`
   - Library size: 47,964,366 bytes.
   - RAR directory is readable in the audit runtime.
   - Inventory: 42 `*.counts.npz` + 42 `*.meta.npz` members (plus directory entry).
   - The member basename set matches the 42-shard corrected TRAIN family.
   - This runtime did not have an extraction backend capable of extracting RAR members, so per-member SHA-256 values were **not** recomputed from this RAR. Do not promote basename/header agreement to byte-identity proof.

2. `/Jepa project/stage81a3r_corrected_real_train.zip`
   - Materialized and inspected separately as an older corrected-real-TRAIN package.
   - It is **not** byte-equivalent to the S174 RAR shard family: 35/42 shard pairs changed; 70/84 member CRCs differ.
   - The seven unchanged shard pairs are consistent with the NPH52 family, matching S174's documented rule that NPH52 is carried byte-identically while HVS/SEA-AD are rebuilt.

3. `/Jepa project/JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip`
   - Materialized and fully extracted for this audit.
   - Contains historical TD56 executors/results and TD57/TD57B executors/results/replay files.
   - No TD59 first-run executor/result bytes are present in this TD41-TD58 package, as expected from its historical scope.

## Canonical S174 repair receipts

The S174 build receipt on `claude/s174-train-cache-rebuild-20261007` binds the rebuilt cache to exact per-shard SHA-256 values. Example HVS entries include:

- `HVS::19cd530b-622c-4bd8-b738-dbf169412cb0`
  - counts `645df92bab23d274048c4d7fa15b55a13ec5c2f5daadde0531aa807d2712aade`
  - meta `60147fc84f0c39003d3ce4c6609b0f7ceba95eec0d4bca71404ecaf21220fa9a`
- `HVS::38374d1b-6549-4429-b59a-ff2706dacd96`
  - counts `6b1f86c3bbf375750e3335d1a3e598a8c3cc174e1cefb61acf7908642f8ebfe0`

The S174 status receipt at freeze time explicitly classified the rebuilt cache as `NOT_YET_USED` and said use for replays required a separate owner decision. Later G1b passed and authorized the corrected cache, but authorization of the cache is not itself a TD-stage replay receipt.

The later commit `46d8eaa8fa23cd60762a8a90c55b84e8d86364b2` replayed V77 synthetic/statistical receipts on the corrected universe. Its own commit message says the replay scope was V77 realization-isolation/dynamic-range/statistical work and that target/representation/training authority remained unchanged. This is **not** evidence of a TD56/TD57B/TD59 rerun.

## Actual historical TD dependency surface

Inspection of the recovered TD executors shows that TD56/TD57/TD58 do not consume the S174 TRAIN shard directory directly. They consume a frozen 50K sparse matrix plus source-specific TD50 metadata keyed by `global_row`.

Historical TD50 metadata hashes bound in the recovered executors are:

- `td50_HVS.npz` — `d6d30cb5ef791fdaaa6f751ee6d802f8e64e062ab641a48194dfc9b596609aeb`
- `td50_NPH52.npz` — `9de0c199414db0705d25cce18cb5007915bcf527c245ed039e2f966437c790fe`
- `td50_SEA_AD.npz` — `ab4fa37a2596de609b4245e82dec0ba7e4a43f95d03421acd46c5814eaaa57d4`

Historical sparse-matrix component hashes include:

- `data.npy` — `0276be0538515146a66012fc9f871eebff2b5cab4de644a7a3a20c29242ef72e`
- `indices.npy` — `f1fc3200adfcebaa5a1214a4f4259fd5a469f6ddbd1379ad73b1222a440e9771`
- `indptr.npy` — `58182d0a8fb8af88cc5b010775056b04e637279669d352b85935ef36d66cf4b1`
- `shape.npy` — `5547a1cd96a984b5163c5540a616006baca3d2a91985005a8f23e970a3133beb`

The recovered TD50 metadata objects carry `global_row`, `source_library`, `detected`, `donor`, and `operator` fields.

Therefore the required corrected lineage is not merely:

`S174 rebuilt TRAIN -> historical TD result`

It is:

`S174 corrected HVS/SEA-AD shard hashes -> corrected 50K sparse matrix + corrected td50_HVS/td50_SEA_AD metadata/global_row receipt -> exact stage executor -> rerun stage result/root`.

## Exhaustive join search result

The extracted TD41-TD58 package was searched across text/code/JSON/CSV/YAML surfaces for:

- `S174` / `s174`
- `S174_REBUILD_BUILD_RECEIPT_V1`
- corrected-substrate/rematerialization markers
- representative new S174 shard hashes from the canonical build receipt

Result: **zero matches**.

The TD57B files named `*_replay.json` are byte-identical to their paired historical result/stdout objects in the recovered package for the inspected SEA-AD/HVS cases. They establish historical replay/reproducibility closure, not a post-S174 replay.

The current S174 branch `results/v77` namespace contains the S174 rebuild/G1/G1b/recovery/status receipts and the later V77 corrected-universe replay, but no stage-specific TD56/TD57B/TD59 corrected-substrate replay receipt was identified in this audit.

The Project Library was also searched for TD56/TD57B/TD59 + S174/rematerialization/new-shard-hash joins. Historical handoffs and historical TD results were recovered, but no separate artifact was found that binds the new S174 shard hashes to regenerated TD50/50K objects and then to rerun TD56/TD57B/TD59 outputs.

## Stage adjudication after Library audit

### TD56

Physical historical executor/result bytes: **PRESENT**.

Corrected-S174 stage-specific join receipt: **NOT FOUND IN AUDITED LIBRARY/REPO SURFACES**.

Classification remains:

`HISTORICAL_RELATIONAL_EVIDENCE__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_TARGET_AUTHORITY`

### TD57B

Physical historical executor/result/replay bytes: **PRESENT**.

Historical 24/24 result remains an authentic historical result.

Corrected-S174 stage-specific join receipt: **NOT FOUND IN AUDITED LIBRARY/REPO SURFACES**.

Classification remains:

`HISTORICAL_PROSPECTIVE_SUCCESS__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_TARGET_AUTHORITY`

### TD59

Historical result identity and independent reconstruction replay closure remain preserved in handoff records. The reconstructed replay must not be represented as the original first-run executor bytes.

Corrected-S174 stage-specific join receipt: **NOT FOUND IN AUDITED LIBRARY/REPO SURFACES**.

Original first-run executor/result bytes: **STILL NOT RECOVERED BY THIS AUDIT**.

Classification remains:

`TD59_STATISTIC_REPRODUCED__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_PRODUCTION_LOCALITY_OR_TRAINING_AUTHORITY`

## Important interpretation

The user's Project Library **does contain substantial S174 downstream material**: the physical S174 rebuilt TRAIN archive, canonical S174 receipts in GitHub, the historical 50K target-discovery archive, real TD56/TD57B executors/results, and TD59 reconstruction records.

The residual gap is narrower than “S174 downstream missing.” The missing object is the **stage-specific corrected-substrate join receipt** (or equivalent physical corrected 50K/TD50 rematerialization + rerun output) that proves the new S174 HVS/SEA-AD mapping propagated into TD56, TD57B, or TD59.

Absence from the audited Library/repository surfaces is not proof that such bytes never existed elsewhere. If a separate corrected 50K/TD50 archive is later mounted, this adjudication must be reopened against its physical hashes.

## Governance boundary

Nothing in this audit changes:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

No target, representation, production locality, Stage 4, or real-training authority is granted by this custody audit.
