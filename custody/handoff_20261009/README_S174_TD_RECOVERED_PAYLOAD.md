# S174 / TD downstream recovered payload custody — 2026-10-09

This directory is the custody surface for the physical audit performed against the Project Library and the recovered September-8 TD41–TD58 working-artifacts archive.

## What is committed

- exact recovered TD41–TD58 source code (`78` `.py`/`.cpp` members) in `TD41_TD58_RECOVERED_CODE_EXACT_20260908.tar.gz` (SHA-256 `e39ba5ab80ebdf3ed0a358cdeccb245431d24f4d5a33887a2b0b0662cb5c93c8`);
- `TD41_TD58_RECOVERED_FILE_MANIFEST.csv`, which hashes **all 155 recovered files**, including binary/row-level artifacts not committed as Git blobs;
- `S174_TD_PHYSICAL_ASSET_MANIFEST.csv`, which hashes the large physical Library artifacts used in the audit;
- `STAGE81A3R_CORRECTED_REAL_TRAIN_EXTRACTED_MANIFEST.csv`, which hashes every file in the extracted older corrected-real-TRAIN package;
- `scripts/audit/audit_s174_td_downstream_join_20261009.py` and its machine-readable result JSON.

## What is deliberately not committed as Git blobs

Large or human-derived binary artifacts remain hash-only custody references, including the S174 RAR, corrected TRAIN ZIP, historical TD working ZIP, discovery subset NPZ, TD50 NPZs, stage count/meta NPZs and matrices, and row-level `td57_sea_cells.tsv`.

This is deliberate. Their bytes remain in Project/Library custody and are identified by byte count + SHA-256. Do not treat absence from Git blobs as absence from custody.

## Scientific meaning

Historical result/data bytes are represented by the complete 155-file SHA-256 manifest rather than being newly published as human-derived Git blobs.

This custody publication does **not** prove a corrected-S174 replay of TD56/TD57B/TD59. It preserves the evidence needed to audit that claim. The stage-specific corrected-substrate join remains unbound unless a corrected 50K/TD50 rematerialization receipt (or equivalent physical artifacts) is recovered and then connected to a rerun result.

Terminal remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
