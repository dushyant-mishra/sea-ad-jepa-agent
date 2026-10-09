# JEPA new-agent takeover — post-S174 downstream Library audit — 2026-10-09

Canonical repository: `dushyant-mishra/sea-ad-jepa-agent`.

Canonical custody branches:
- `handoff/jepa-20261008-complete-runtime-s174-takeover`
- `audit/jepa-target-discovery-handoff-snapshot-20261009`

Fetch both live heads before modifying anything. This handoff is fail-closed and does not grant training or Stage4 authority.

Read `docs/agent/S174_DOWNSTREAM_LIBRARY_JOIN_AUDIT_20261009.md` first, then this file, then the machine-readable custody/results artifacts.

## Hard terminal

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Physical audit state

Mounted and hashed:
- S174 rebuilt real-TRAIN RAR: 47,964,366 bytes; SHA-256 `88067f2efb5d8a0168eb352f83bd9de88c3b929c95a8f8fa1c40a6e34c568a2f`.
- older Stage81A3R corrected-real-TRAIN ZIP: 50,647,044 bytes; SHA-256 `3b86097d514f1cc2d84b19fd289344e0634356359462173a9b2b0f7541dd7e48`.
- TD41–TD58 working archive: 92,478,083 bytes; SHA-256 `c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417`.
- historical discovery subset NPZ: SHA-256 `615e57e3f45cc2bc020e3b48ed5401a9aa65323d82a919e7d577e9642e34be8f`.
- TD50 HVS: `d6d30cb5ef791fdaaa6f751ee6d802f8e64e062ab641a48194dfc9b596609aeb`.
- TD50 NPH52: `9de0c199414db0705d25cce18cb5007915bcf527c245ed039e2f966437c790fe`.
- TD50 SEA-AD: `ab4fa37a2596de609b4245e82dec0ba7e4a43f95d03421acd46c5814eaaa57d4`.

The committed physical manifest is `custody/handoff_20261009/S174_TD_PHYSICAL_ASSET_MANIFEST.csv`.

## Exact provenance distinction

The corrected S174 TRAIN cache is not the direct TD56/TD57B/TD59 input. Historical TD56/TD57/TD58 executors consume a frozen 50K sparse matrix plus `td50_HVS.npz`, `td50_NPH52.npz`, and `td50_SEA_AD.npz`, joined through `global_row`.

Required closure chain:

`corrected S174 HVS/SEA-AD shard hashes -> corrected 50K sparse matrix + corrected td50_HVS/td50_SEA_AD metadata/global_row receipt -> exact stage executor -> rerun result/root`

Narrative continuity is insufficient.

## Recovered TD custody

The September-8 TD41–TD58 archive contains 155 files, including 78 `.py`/`.cpp` source files and historical TD56/TD57/TD57A/TD57B executors/results/replays.

Generated custody products:
- complete 155-file per-file SHA-256 manifest: `fea76c1ae7976ecd17795f0100fd796434507ef9e5088f6d58d72c5d1954b947`;
- exact 78-file source-code bundle: `e39ba5ab80ebdf3ed0a358cdeccb245431d24f4d5a33887a2b0b0662cb5c93c8`;
- extracted older corrected-real-TRAIN manifest: `a4beef2bfd2b1d0910cfab05f907f83ca75fed8ac7fd6e63ca016c747763d514`.

These larger/human-derived payloads are hash-referenced rather than newly published as public Git blobs. Row-level `td57_sea_cells.tsv` is specifically not added to public Git.

## TD50 structure

Each historical TD50 NPZ contains `S`, `tau`, `global_row`, `source_library`, `detected`, `donor`, `operator`.

Row counts: HVS 1,129; NPH52 1,310; SEA-AD 22,561.

## Corrected-S174 join search

The recovered TD text surface was searched for `S174`, `s174`, `S174_REBUILD_BUILD_RECEIPT_V1`, and representative new S174 shard SHA-256 values.

Result: **0 matches**.

Durable audit artifacts:
- `scripts/audit/audit_s174_td_downstream_join_20261009.py`
- `results/audit/S174_TD_DOWNSTREAM_JOIN_RESULT_20261009.json`
- `docs/agent/S174_DOWNSTREAM_LIBRARY_JOIN_AUDIT_20261009.md`
- `custody/handoff_20261009/S174_TD_AUDIT_PACKAGE_MANIFEST.csv`
- `custody/handoff_20261009/README_S174_TD_RECOVERED_PAYLOAD.md`
- `custody/handoff_20261009/S174_TD_PHYSICAL_ASSET_MANIFEST.csv`

## Stage adjudication

TD56: historical executor/result bytes present; corrected-S174 TD50/50K replay not bound.
`HISTORICAL_RELATIONAL_EVIDENCE__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_TARGET_AUTHORITY`

TD57B: historical executor/result/replay files present; historical 24/24 remains authentic historical evidence; corrected-S174 replay not bound.
`HISTORICAL_PROSPECTIVE_SUCCESS__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_TARGET_AUTHORITY`

TD59: historical result identity + independent reconstruction replay closure preserved; original first-run executor/result bytes and corrected-S174 TD59 replay receipt remain unrecovered.
`TD59_STATISTIC_REPRODUCED__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_PRODUCTION_LOCALITY_OR_TRAINING_AUTHORITY`

## Do not redo

Do not reopen absent contradictory/new bytes: TD34, Nott ATAC/liftover, SCENIC+, NIH-CARD Stage3/4 authority, TD57C failure, TD60 prospective bridge, or broad target-lineage archaeology already captured in prior handoffs.

## Separate runtime lane

Runtime has progressed beyond ZERO_UPDATE only through a bounded synthetic mutation rehearsal. It remains synthetic-only/non-production. Do not alter runtime authority or enable training from this custody lane.

## Genuine open question

Find whether a corrected 50K/TD50 rematerialization package or stage-specific post-S174 replay receipt exists elsewhere in Project Library/Git history and physically joins the canonical rebuilt S174 shard hashes to TD56/TD57B/TD59 rerun outputs.

Evidence levels:
1. design/reconciliation contract;
2. corrected metadata/data artifact;
3. stage-specific downstream replay receipt/result.

Only levels 2 and 3 can advance adjudication.

## Ordered successor actions

1. Fetch live heads for both custody branches and PR #237.
2. Read the S174 downstream audit and this handoff.
3. Rerun `scripts/audit/audit_s174_td_downstream_join_20261009.py` against remounted assets.
4. Search specifically for corrected 50K / `td50_HVS` / `td50_SEA_AD` materialization whose receipt names or hashes the new S174 rebuilt shards.
5. Search post-S174 historical commits/branches for 50K/TD50 materializers; never infer joins from filenames.
6. If a candidate package appears, hash all inputs and prove `global_row`/row-identity compatibility before replay.
7. Only after the join is proven, rerun/reconstruct TD56/TD57B/TD59 and record exact result/root.
8. Update the handoff branch first at every substantive checkpoint, then move the audit branch to the identical SHA.
9. Keep `main` untouched absent separately reviewed integration.

## Final boundary

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
