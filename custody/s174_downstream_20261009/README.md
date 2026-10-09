# S174 downstream custody package — 2026-10-09

This directory preserves the audit evidence used to answer whether corrected S174 HVS/SEA-AD TRAIN shards were propagated into the historical 50K/TD50 substrate and then replayed through TD56, TD57B, or TD59.

## Included

- `S174_DOWNSTREAM_LOCAL_ASSET_MANIFEST.csv` — exact bytes/SHA-256 for the three physical Library archives inspected.
- `S174_RAR_DIRECTORY_MANIFEST.csv` — RAR directory metadata for the physical S174 rebuilt TRAIN archive. This is directory-level evidence only; the audit runtime lacked a working RAR extraction backend.
- `STAGE81A3R_VS_S174_RAR_MEMBER_COMPARISON.csv` — pre-S174 Stage81A3R ZIP vs S174 RAR member size/CRC comparison for 84 NPZ members.
- `TD41_TD58_EXTRACTED_MEMBER_SHA256_MANIFEST.csv` — SHA-256/size inventory for every extracted member of the historical TD41–TD58 archive.
- `TD50_METADATA_SCHEMA_AND_HASH_SUMMARY.json` — safe no-pickle schema/hash summary for the three historical `td50_*` metadata objects.
- `TD56_RESULT_NPZ_SCHEMA_AND_HASH_SUMMARY.json` — safe no-pickle schema/hash summary for all nine historical TD56 result NPZs.
- `S174_DOWNSTREAM_JOIN_AUDIT_RESULT.json` — machine-readable adjudication.
- `recovered_td41_td58_key_text/` — exact recovered decision-bearing text executors/results needed to understand the TD50→TD56/TD57B dependency surface.
- `scripts/audit/audit_s174_td50_downstream_join_20261009.py` in the repository — replayable custody audit logic.

## Binary custody boundary

The 92,478,083-byte historical TD41–TD58 ZIP, 50,647,044-byte Stage81A3R corrected-real-TRAIN ZIP, and 47,964,366-byte S174 RAR are not duplicated into ordinary Git history. Their exact SHA-256 identities are recorded in the manifest. Historical binary NPZ/NPY data are likewise represented by exact per-file SHA-256 rows; selected text executors/results are copied byte-for-byte into Git for direct review.

## Current result

The Library does contain substantial downstream material, but no audited artifact binds the new S174 shard hashes to a regenerated 50K/TD50 `global_row` substrate and then to a stage-specific TD56, TD57B, or TD59 rerun. The gap is therefore the corrected-substrate join receipt, not a generic absence of downstream evidence.

Nothing here changes the terminal:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
