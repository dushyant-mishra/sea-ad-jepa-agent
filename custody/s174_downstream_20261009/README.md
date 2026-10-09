# S174 downstream custody package — 2026-10-09

This directory preserves the audit evidence used to answer whether corrected S174 HVS/SEA-AD TRAIN shards were propagated into the historical 50K/TD50 substrate and then replayed through TD56, TD57B, or TD59.

## Included

- `S174_DOWNSTREAM_LOCAL_ASSET_MANIFEST.csv` — exact bytes/SHA-256 for the three physical Library archives inspected.
- `S174_RAR_DIRECTORY_MANIFEST.csv` — all 85 RAR directory entries with uncompressed/compressed sizes and CRC32. Directory evidence only: the runtime had no working RAR payload-extraction backend.
- `STAGE81A3R_VS_S174_RAR_MEMBER_COMPARISON.csv` — all 84 NPZ basename comparisons between the pre-S174 Stage81A3R ZIP and S174 RAR by uncompressed size+CRC.
- `TD41_TD58_EXTRACTED_MEMBER_SHA256_MANIFEST.csv` — all 155 extracted historical TD41–TD58 members with exact bytes/SHA-256 and text/binary classification.
- `TD50_METADATA_SCHEMA_AND_HASH_SUMMARY.json` — fail-closed no-pickle schema/hash summary for `td50_HVS`, `td50_NPH52`, and `td50_SEA_AD`.
- `TD56_RESULT_NPZ_SCHEMA_AND_HASH_SUMMARY.json` — no-pickle hash/statistic summary for all nine historical TD56 result NPZs.
- `RECOVERED_KEY_TEXT_SHA256_MANIFEST.csv` — exact hashes for the decision-bearing TD50/TD56/TD57B text artifacts reviewed in this audit.
- `recovered_td41_td58_key_text/compute_td50_source.py` — exact recovered TD50 source producer copied into Git. Other historical executors/results are retained as exact hash-bound archive members rather than duplicated again.
- `S174_DOWNSTREAM_JOIN_AUDIT_RESULT.json` — machine-readable stage adjudication.
- `scripts/audit/audit_s174_td50_downstream_join_20261009.py` — replayable custody audit logic.

## Binary and historical-byte custody boundary

The 92,478,083-byte historical TD41–TD58 ZIP, 50,647,044-byte Stage81A3R corrected-real-TRAIN ZIP, and 47,964,366-byte S174 RAR are not duplicated into ordinary Git history. Their exact SHA-256 identities are in `S174_DOWNSTREAM_LOCAL_ASSET_MANIFEST.csv`.

Likewise, historical NPZ/NPY/PKL/binary executables are not expanded into Git. Every extracted historical member, including the TD50 objects, TD56 result NPZs, TD57B results/replays, TD57C surfaces, and TD58 artifacts, is independently size/SHA-bound in the 155-row full archive manifest. This preserves exact custody without silently converting the handoff branch into a binary data mirror.

## Current result

The Library contains substantial S174 and downstream material, but no audited artifact binds the new S174 shard hashes to a regenerated 50K/TD50 `global_row` substrate and then to a stage-specific TD56, TD57B, or TD59 rerun. The unresolved object is the corrected-substrate join receipt, not generic downstream evidence.

Nothing here changes:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
