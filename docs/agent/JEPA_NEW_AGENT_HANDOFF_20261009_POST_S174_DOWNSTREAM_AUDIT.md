# JEPA new-agent takeover — post-S174 downstream Library audit — 2026-10-09

## 0. Read this first

Canonical repository: `dushyant-mishra/sea-ad-jepa-agent`.

Canonical custody branches:

- `handoff/jepa-20261008-complete-runtime-s174-takeover`
- `audit/jepa-target-discovery-handoff-snapshot-20261009`

They were synchronized at the start of this publication at parent head:

`d2f7ea138c2bc14eae5d41117b1aff32c90162da`

Fetch both live heads before modifying anything. This handoff is intentionally fail-closed and does not grant training or Stage4 authority.

The first prior audit to read is:

`docs/agent/S174_DOWNSTREAM_LIBRARY_JOIN_AUDIT_20261009.md`

Then read this file and the machine-readable custody/results files listed below.

## 1. Hard current terminal

Do not weaken or reinterpret this terminal without new physical evidence:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

No corrected target winner, representation winner, Stage4 authorization, or production/real-training authority was granted by this work.

## 2. What this chat actually established

The Project Library contains much more S174 downstream material than an earlier handoff implied. The following physical artifacts were mounted and audited:

- S174 rebuilt real-TRAIN RAR: 47,964,366 bytes, SHA-256 `88067f2efb5d8a0168eb352f83bd9de88c3b929c95a8f8fa1c40a6e34c568a2f`.
- older Stage81A3R corrected-real-TRAIN ZIP: 50,647,044 bytes, SHA-256 `3b86097d514f1cc2d84b19fd289344e0634356359462173a9b2b0f7541dd7e48`.
- recovered `JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip`: 92,478,083 bytes, SHA-256 `c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417`.
- historical discovery subset NPZ: 50,646,637 bytes, SHA-256 `615e57e3f45cc2bc020e3b48ed5401a9aa65323d82a919e7d577e9642e34be8f`.
- historical TD50 HVS: SHA-256 `d6d30cb5ef791fdaaa6f751ee6d802f8e64e062ab641a48194dfc9b596609aeb`.
- historical TD50 NPH52: SHA-256 `9de0c199414db0705d25cce18cb5007915bcf527c245ed039e2f966437c790fe`.
- historical TD50 SEA-AD: SHA-256 `ab4fa37a2596de609b4245e82dec0ba7e4a43f95d03421acd46c5814eaaa57d4`.

The exact physical-asset manifest is committed as:

`custody/handoff_20261009/S174_TD_PHYSICAL_ASSET_MANIFEST.csv`

## 3. Critical scientific/provenance distinction

The corrected S174 TRAIN cache is **not itself the TD56/TD57B/TD59 input object**.

Recovered TD56/TD57/TD58 executors consume:

1. a frozen 50K sparse matrix under the historical `td_matrix_npz/arrays` surface; and
2. source-specific `td50_HVS.npz`, `td50_NPH52.npz`, and `td50_SEA_AD.npz` metadata/state, joined through `global_row`.

Therefore the lineage needed to close the S174 defect is:

`corrected S174 HVS/SEA-AD shard hashes`
`→ corrected 50K sparse matrix + corrected td50_HVS/td50_SEA_AD metadata/global_row receipt`
`→ exact TD stage executor`
`→ rerun stage result/root`

Narrative continuity or the presence of both endpoint artifacts is not sufficient.

## 4. S174 RAR versus older corrected-real-TRAIN ZIP

The S174 RAR is not merely a repackaging of the older corrected-real-TRAIN ZIP.

The audit found matching 42-shard basename families but substantive member changes: 35/42 shard pairs changed and 70/84 member CRCs differ. The unchanged subset is consistent with the NPH52 side that S174 documented as carried byte-identically; HVS/SEA-AD are the affected/rebuilt side.

The RAR could be inventoried through its directory metadata in this runtime, but its compressed members could not be extracted because no working external RAR decompressor was available. Do **not** promote RAR member basename/CRC agreement to per-member SHA-256 proof unless those members are later extracted and hashed.

## 5. Recovered historical TD payload and custody policy

The September-8 TD41–TD58 archive was physically extracted. It contains 155 files total, including 78 `.py`/`.cpp` source files, TD56 executors/results, TD57/TD57A/TD57B executors/results/replay objects, diagnostics, compiled helpers, NPZ/NPY objects, and row-level data.

The complete recovered archive itself is physically identified by SHA-256 `c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417`. A complete local per-file SHA-256 manifest was generated as `TD41_TD58_RECOVERED_FILE_MANIFEST.csv` with 155 rows; its own SHA-256 is `fea76c1ae7976ecd17795f0100fd796434507ef9e5088f6d58d72c5d1954b947`.

An exact 78-file source-code bundle was also generated locally as `TD41_TD58_RECOVERED_CODE_EXACT_20260908.tar.gz`, SHA-256 `e39ba5ab80ebdf3ed0a358cdeccb245431d24f4d5a33887a2b0b0662cb5c93c8`.

Those larger custody payloads remain hash-referenced rather than newly publishing human-derived result/data bytes as Git blobs. The row-level `td57_sea_cells.tsv` is specifically not added as a public Git blob.

## 6. Exact TD50 structure recovered

The historical TD50 NPZ objects expose the keys:

`S`, `tau`, `global_row`, `source_library`, `detected`, `donor`, `operator`.

Observed row counts:

- HVS: 1,129 rows.
- NPH52: 1,310 rows.
- SEA-AD: 22,561 rows.

The audit records shapes/dtypes and non-identifying row/operator/source cardinalities, but deliberately does not publish donor identifiers.

## 7. Exhaustive corrected-S174 join search result

The recovered TD text surface was searched for:

- `S174` / `s174`;
- `S174_REBUILD_BUILD_RECEIPT_V1`;
- representative exact S174 rebuilt shard SHA-256s from the canonical build receipt.

Machine result: **0 matches**.

The rerunnable audit script and machine receipt are:

- `scripts/audit/audit_s174_td_downstream_join_20261009.py`
- `results/audit/S174_TD_DOWNSTREAM_JOIN_RESULT_20261009.json`

This is evidence that the recovered TD41–TD58 text package does not itself carry a post-S174 join receipt. It is not proof that no such bytes ever existed elsewhere.

## 8. Stage-by-stage adjudication

### TD56

Preserved: physical historical executors and historical result NPZs across HVS, NPH52, and SEA-AD variants.

Not established: a corrected-S174 50K/TD50 rematerialization feeding a TD56 rerun.

Current classification:

`HISTORICAL_RELATIONAL_EVIDENCE__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_TARGET_AUTHORITY`

### TD57B

Preserved: physical historical executors and historical result JSON/stdout/replay files. Historical 24/24 success remains authentic historical evidence.

Important: inspected `*_replay.json` files are historical replay/reproducibility objects, not post-S174 corrected-substrate replay evidence.

Not established: a corrected-S174 50K/TD50 rematerialization feeding TD57B and producing a new result/root.

Current classification:

`HISTORICAL_PROSPECTIVE_SUCCESS__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_TARGET_AUTHORITY`

### TD59

Preserved in historical handoff/custody records: pre-outcome binding and result identity; independent reconstruction replay closure; explicit warning that reconstructed executor bytes are not the original first-run executor bytes.

Still not recovered by this audit: original TD59 first-run executor/result bytes; corrected-S174 50K/TD50 rematerialization + TD59 rerun receipt.

Current classification:

`TD59_STATISTIC_REPRODUCED__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_PRODUCTION_LOCALITY_OR_TRAINING_AUTHORITY`

## 9. What not to redo

Do not restart or reopen these unless genuinely contradictory/new bytes appear:

- TD34 exact genealogy/panel recovery;
- Nott ATAC/liftover provenance;
- SCENIC+ status archaeology;
- NIH-CARD Stage3/4 authority archaeology;
- TD57C failure;
- TD60 prospective/unfinished bridge;
- broad target-lineage archaeology already captured in prior handoffs.

TD34 is closed by an authentic producer + canonical observation-state reconstruction that reproduces exact support/panel hashes. The active question is not TD34.

## 10. Separate runtime lane — do not collide

A separate runtime lane has already progressed beyond ZERO_UPDATE through a tiny bounded synthetic mutation rehearsal. It demonstrated one guarded optimizer update, EMA only after completed update, typed persistence/reload and adversarial failure behavior. It remains synthetic-only and non-production.

Do not use this target-discovery custody lane to alter runtime authority, enable production training, or merge unrelated runtime work.

## 11. Current genuine open question

The task is no longer “find S174 downstream.” The Library clearly contains S174 downstream material.

The genuine open question is:

> Does a corrected 50K/TD50 rematerialization package or stage-specific post-S174 replay receipt exist anywhere else in Project Library/Git history, and can it be physically joined to the canonical rebuilt S174 shard hashes and TD56/TD57B/TD59 rerun outputs?

Evidence levels must remain separate:

1. **design/reconciliation contract** — explains what should have changed;
2. **corrected metadata/data artifact** — proves rematerialization happened;
3. **stage-specific downstream replay receipt/result** — proves the corrected artifact was actually consumed.

Only levels 2 and 3 can advance adjudication; a design note alone cannot.

## 12. Ordered next actions for the successor

1. Fetch live heads for both canonical custody branches and PR #237 before writing.
2. Read `docs/agent/S174_DOWNSTREAM_LIBRARY_JOIN_AUDIT_20261009.md` and this handoff.
3. Verify the committed manifests against any currently mounted Library assets with `scripts/audit/audit_s174_td_downstream_join_20261009.py`.
4. Search specifically for a corrected 50K matrix / `td50_HVS` / `td50_SEA_AD` rematerialization whose receipt names or hashes the new S174 rebuilt shards.
5. Search historical Git commits/branches for materializers that emit the 50K/TD50 objects after the S174 correction date. Do not infer a join from filename similarity.
6. If a candidate corrected TD50/50K package is recovered, hash every physical input and prove `global_row`/row-identity compatibility before rerunning any TD stage.
7. Only after that join is proven, execute/reconstruct stage-specific TD56/TD57B/TD59 replay as appropriate and record an exact result/root.
8. Update the handoff branch first at each substantive checkpoint, then advance the audit branch to the identical SHA so they do not drift.
9. Keep `main` untouched unless a separately reviewed integration decision is made.

## 13. Custody/publication map added by this handoff

- `custody/handoff_20261009/S174_TD_AUDIT_PACKAGE_MANIFEST.csv`
- `custody/handoff_20261009/README_S174_TD_RECOVERED_PAYLOAD.md`
- `custody/handoff_20261009/S174_TD_PHYSICAL_ASSET_MANIFEST.csv`
- local full extracted-stage manifest SHA-256 `a4beef2bfd2b1d0910cfab05f907f83ca75fed8ac7fd6e63ca016c747763d514`
- local complete 155-file TD manifest SHA-256 `fea76c1ae7976ecd17795f0100fd796434507ef9e5088f6d58d72c5d1954b947`
- local exact 78-file code bundle SHA-256 `e39ba5ab80ebdf3ed0a358cdeccb245431d24f4d5a33887a2b0b0662cb5c93c8`
- `scripts/audit/audit_s174_td_downstream_join_20261009.py`
- `results/audit/S174_TD_DOWNSTREAM_JOIN_RESULT_20261009.json`
- `docs/agent/S174_DOWNSTREAM_LIBRARY_JOIN_AUDIT_20261009.md`
- this handoff file

Large binary/human-derived data remain custody-by-hash, not newly uploaded Git blobs.

## 14. Final boundary

This publication improves custody and takeover completeness. It does not change the scientific terminal:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
