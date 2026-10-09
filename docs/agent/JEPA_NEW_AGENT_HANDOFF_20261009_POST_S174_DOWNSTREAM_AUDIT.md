# JEPA new-agent takeover — post-S174 downstream Library audit — 2026-10-09

## 0. Read this first

Canonical repository: `dushyant-mishra/sea-ad-jepa-agent`.

Canonical custody branches:

- `handoff/jepa-20261008-complete-runtime-s174-takeover`
- `audit/jepa-target-discovery-handoff-snapshot-20261009`

Fetch both live heads before modifying anything. This handoff is intentionally fail-closed and does not grant training or Stage4 authority.

The first prior audit to read is `docs/agent/S174_DOWNSTREAM_LIBRARY_JOIN_AUDIT_20261009.md`, then this file, then the machine-readable custody/results files below.

## 1. Hard current terminal

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

Do not weaken or reinterpret it without new physical evidence.

## 2. What this audit established

The Project Library contains substantial S174 downstream material. The following physical artifacts were mounted, hashed, and audited:

- S174 rebuilt real-TRAIN RAR: 47,964,366 bytes; SHA-256 `88067f2efb5d8a0168eb352f83bd9de88c3b929c95a8f8fa1c40a6e34c568a2f`.
- older Stage81A3R corrected-real-TRAIN ZIP: 50,647,044 bytes; SHA-256 `3b86097d514f1cc2d84b19fd289344e0634356359462173a9b2b0f7541dd7e48`.
- `JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip`: 92,478,083 bytes; SHA-256 `c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417`.
- historical discovery subset NPZ: 50,646,637 bytes; SHA-256 `615e57e3f45cc2bc020e3b48ed5401a9aa65323d82a919e7d577e9642e34be8f`.
- historical TD50 HVS: SHA-256 `d6d30cb5ef791fdaaa6f751ee6d802f8e64e062ab641a48194dfc9b596609aeb`.
- historical TD50 NPH52: SHA-256 `9de0c199414db0705d25cce18cb5007915bcf527c245ed039e2f966437c790fe`.
- historical TD50 SEA-AD: SHA-256 `ab4fa37a2596de609b4245e82dec0ba7e4a43f95d03421acd46c5814eaaa57d4`.

The committed physical-asset manifest is `custody/handoff_20261009/S174_TD_PHYSICAL_ASSET_MANIFEST.csv`.

## 3. Critical provenance distinction

The corrected S174 TRAIN cache is **not itself the TD56/TD57B/TD59 input object**.

Recovered TD56/TD57/TD58 executors consume a frozen 50K sparse matrix and source-specific `td50_HVS.npz`, `td50_NPH52.npz`, and `td50_SEA_AD.npz` metadata/state joined through `global_row`.

The lineage required to close the S174 defect is therefore:

`corrected S174 HVS/SEA-AD shard hashes`
`→ corrected 50K sparse matrix + corrected td50_HVS/td50_SEA_AD metadata/global_row receipt`
`→ exact TD stage executor`
`→ rerun stage result/root`

Narrative continuity or co-presence of endpoint artifacts is insufficient.

## 4. S174 RAR versus older corrected-real-TRAIN ZIP

The S174 RAR is not merely a repackaging of the older corrected-real-TRAIN ZIP. The audit found matching 42-shard basename families but 35/42 changed shard pairs and 70/84 changed member CRCs. The unchanged subset is consistent with NPH52, while HVS/SEA-AD are the affected/rebuilt side.

RAR member extraction was unavailable in this runtime, so per-member SHA-256 values were not recomputed from the RAR. Do not upgrade basename/CRC agreement to per-member byte identity without later extraction and hashing.

## 5. Recovered historical TD payload and custody policy

The September-8 TD41–TD58 archive was physically extracted and contains 155 files total, including 78 `.py`/`.cpp` source files plus historical TD56/TD57/TD57A/TD57B executors, results, replay objects, diagnostics, compiled helpers, NPZ/NPY objects, and row-level data.

Additional custody products generated during this audit:

- complete 155-file per-file SHA-256 manifest: SHA-256 `fea76c1ae7976ecd17795f0100fd796434507ef9e5088f6d58d72c5d1954b947`;
- exact 78-file recovered source-code bundle: SHA-256 `e39ba5ab80ebdf3ed0a358cdeccb245431d24f4d5a33887a2b0b0662cb5c93c8`;
- complete extracted older corrected-real-TRAIN per-file manifest: SHA-256 `a4beef2bfd2b1d0910cfab05f907f83ca75fed8ac7fd6e63ca016c747763d514`.

These larger custody payloads are hash-referenced rather than newly publishing human-derived result/data bytes as public Git blobs. In particular, row-level `td57_sea_cells.tsv` is not added to public Git.

## 6. TD50 structure recovered

Each historical TD50 NPZ contains:

`S`, `tau`, `global_row`, `source_library`, `detected`, `donor`, `operator`.

Observed row counts are HVS 1,129; NPH52 1,310; SEA-AD 22,561. The audit records non-identifying shapes/cardinalities and does not publish donor identifiers.

## 7. Exhaustive corrected-S174 join search

The recovered TD text surface was searched for `S174`, `s174`, `S174_REBUILD_BUILD_RECEIPT_V1`, and representative exact S174 rebuilt shard SHA-256 values from the canonical build receipt.

Result: **0 matches**.

Durable audit artifacts:

- `scripts/audit/audit_s174_td_downstream_join_20261009.py`
- `results/audit/S174_TD_DOWNSTREAM_JOIN_RESULT_20261009.json`
- `docs/agent/S174_DOWNSTREAM_LIBRARY_JOIN_AUDIT_20261009.md`
- `custody/handoff_20261009/S174_TD_AUDIT_PACKAGE_MANIFEST.csv`
- `custody/handoff_20261009/README_S174_TD_RECOVERED_PAYLOAD.md`
- `custody/handoff_20261009/S174_TD_PHYSICAL_ASSET_MANIFEST.csv`

This proves the recovered TD41–TD58 text package does not itself carry a post-S174 join receipt. It does **not** prove no such bytes ever existed elsewhere.

## 8. Stage adjudication

### TD56
Historical physical executor/result bytes are present. A corrected-S174 50K/TD50 rematerialization feeding TD56 is not bound.

`HISTORICAL_RELATIONAL_EVIDENCE__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_TARGET_AUTHORITY`

### TD57B
Historical physical executors and result/replay files are present; the historical 24/24 success remains authentic historical evidence. The recovered `*_replay.json` objects are historical reproducibility evidence, not post-S174 corrected-substrate replay evidence.

`HISTORICAL_PROSPECTIVE_SUCCESS__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_TARGET_AUTHORITY`

### TD59
Historical result identity and independent reconstruction replay closure remain preserved. Do not represent the reconstructed executor as the original first-run executor. The original first-run executor/result bytes and any corrected-S174 TD59 rerun receipt remain unrecovered by this audit.

`TD59_STATISTIC_REPRODUCED__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_PRODUCTION_LOCALITY_OR_TRAINING_AUTHORITY`

## 9. What not to redo

Do not reopen without contradictory/new bytes: TD34 genealogy/panel recovery, Nott ATAC/liftover provenance, SCENIC+ archaeology, NIH-CARD Stage3/4 authority archaeology, TD57C failure, TD60 prospective/unfinished bridge, or broad target-lineage archaeology already captured in prior handoffs.

TD34 is closed by authentic producer + canonical observation-state reconstruction that reproduces exact support/panel hashes.

## 10. Separate runtime lane

The runtime lane is separate. It has already progressed beyond ZERO_UPDATE through a tiny bounded synthetic mutation rehearsal with one guarded optimizer update, EMA only after completion, typed persistence/reload, and adversarial failure behavior. It remains synthetic-only/non-production. Do not alter runtime authority or enable training from this custody lane.

## 11. Genuine open question

The task is no longer “find S174 downstream.” The Library clearly contains downstream material.

The remaining question is whether a corrected 50K/TD50 rematerialization package or stage-specific post-S174 replay receipt exists elsewhere in Project Library/Git history and can be physically joined to the canonical rebuilt S174 shard hashes and TD56/TD57B/TD59 rerun outputs.

Keep evidence levels separate:

1. design/reconciliation contract;
2. corrected metadata/data artifact;
3. stage-specific downstream replay receipt/result.

Only levels 2 and 3 can advance adjudication.

## 12. Ordered next actions

1. Fetch live heads for both custody branches and PR #237 before writing.
2. Read `docs/agent/S174_DOWNSTREAM_LIBRARY_JOIN_AUDIT_20261009.md`, then this handoff.
3. Rerun `scripts/audit/audit_s174_td_downstream_join_20261009.py` against any remounted physical assets.
4. Search specifically for corrected 50K / `td50_HVS` / `td50_SEA_AD` materialization whose receipt names or hashes the new S174 rebuilt shards.
5. Search historical commits/branches for post-S174 materializers that emit the 50K/TD50 objects. Do not infer joins from filenames.
6. If a candidate corrected TD50/50K package appears, hash all inputs and prove `global_row`/row-identity compatibility before rerunning any stage.
7. Only after the join is proven, rerun/reconstruct TD56/TD57B/TD59 and record exact result/root.
8. Update the handoff branch first at every substantive checkpoint, then fast-forward the audit branch to the identical SHA.
9. Keep `main` untouched absent a separately reviewed integration decision.

## 13. Final boundary

Custody and takeover are improved; the scientific terminal is unchanged:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
