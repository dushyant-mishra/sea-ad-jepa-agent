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
S174 RAR: 47,964,366 bytes, SHA-256 `88067f2efb5d8a0168eb352f83bd9de88c3b929c95a8f8fa1c40a6e34c568a2f`.
Older corrected-TRAIN ZIP: 50,647,044 bytes, SHA-256 `3b86097d514f1cc2d84b19fd289344e0634356359462173a9b2b0f7541dd7e48`.
TD41–TD58 ZIP: 92,478,083 bytes, SHA-256 `c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417`.
Discovery subset NPZ: SHA-256 `615e57e3f45cc2bc020e3b48ed5401a9aa65323d82a919e7d577e9642e34be8f`.
TD50 hashes: HVS `d6d30cb5ef791fdaaa6f751ee6d802f8e64e062ab641a48194dfc9b596609aeb`; NPH52 `9de0c199414db0705d25cce18cb5007915bcf527c245ed039e2f966437c790fe`; SEA-AD `ab4fa37a2596de609b4245e82dec0ba7e4a43f95d03421acd46c5814eaaa57d4`.

## Provenance distinction
Historical TD56/TD57/TD58 executors consume a frozen 50K sparse matrix plus source-specific TD50 state through `global_row`; they do not directly consume the corrected S174 TRAIN shards.

Required closure chain:
`S174 corrected HVS/SEA-AD shard hashes -> corrected 50K + corrected td50_HVS/td50_SEA_AD global_row receipt -> exact TD executor -> rerun result/root`.

## Recovered custody
The TD41–TD58 archive contains 155 files, including 78 Python/C++ source files and historical TD56/TD57/TD57A/TD57B executors/results/replays.

Generated local custody roots:
- 155-file per-file manifest SHA-256 `fea76c1ae7976ecd17795f0100fd796434507ef9e5088f6d58d72c5d1954b947`;
- exact 78-file source bundle SHA-256 `e39ba5ab80ebdf3ed0a358cdeccb245431d24f4d5a33887a2b0b0662cb5c93c8`;
- extracted older corrected-TRAIN manifest SHA-256 `a4beef2bfd2b1d0910cfab05f907f83ca75fed8ac7fd6e63ca016c747763d514`.

Large/human-derived data remain hash-only custody and are not newly published as public Git blobs.

## Search result
Recovered TD text was searched for `S174`, `s174`, `S174_REBUILD_BUILD_RECEIPT_V1`, and representative new S174 shard hashes. Result: **0 matches**.

Durable artifacts:
- `scripts/audit/audit_s174_td_downstream_join_20261009.py`
- `results/audit/S174_TD_DOWNSTREAM_JOIN_RESULT_20261009.json`
- `docs/agent/S174_DOWNSTREAM_LIBRARY_JOIN_AUDIT_20261009.md`
- `custody/handoff_20261009/S174_TD_AUDIT_PACKAGE_MANIFEST.csv`
- `custody/handoff_20261009/S174_TD_PHYSICAL_ASSET_MANIFEST.csv`

## Stage adjudication
TD56: `HISTORICAL_RELATIONAL_EVIDENCE__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_TARGET_AUTHORITY`

TD57B: `HISTORICAL_PROSPECTIVE_SUCCESS__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_TARGET_AUTHORITY`

TD59: `TD59_STATISTIC_REPRODUCED__CORRECTED_SUBSTRATE_REPLAY_NOT_BOUND__NO_PRODUCTION_LOCALITY_OR_TRAINING_AUTHORITY`

## Do not redo
Do not reopen absent contradictory/new bytes: TD34, Nott ATAC/liftover, SCENIC+, NIH-CARD Stage3/4 authority, TD57C failure, TD60 prospective bridge, or broad target-lineage archaeology already captured in prior handoffs.

## Separate runtime lane
Runtime has progressed beyond ZERO_UPDATE only through a bounded synthetic mutation rehearsal. It remains synthetic-only/non-production. Do not alter runtime authority or enable training from this custody lane.

## Genuine open question
Recover, if it exists, a corrected 50K/TD50 rematerialization package or stage-specific post-S174 replay receipt that physically joins the canonical rebuilt S174 shard hashes to TD56/TD57B/TD59 rerun outputs.

Evidence levels remain separate: (1) design contract, (2) corrected artifact, (3) downstream replay receipt. Only levels 2 and 3 advance adjudication.

## Ordered successor actions
1. Fetch both live custody heads and PR #237.
2. Read the S174 downstream audit and this handoff.
3. Rerun the audit script against remounted assets.
4. Search for corrected 50K / `td50_HVS` / `td50_SEA_AD` materialization naming/hashing the new S174 shards.
5. Search post-S174 commits/branches for 50K/TD50 materializers; do not infer joins from filenames.
6. If found, hash all inputs and prove `global_row`/row-identity compatibility before replay.
7. Only after that join, rerun/reconstruct TD56/TD57B/TD59 and record exact result/root.
8. Update handoff branch first, then audit branch to the identical SHA.
9. Keep `main` untouched absent separately reviewed integration.

## Final boundary
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
