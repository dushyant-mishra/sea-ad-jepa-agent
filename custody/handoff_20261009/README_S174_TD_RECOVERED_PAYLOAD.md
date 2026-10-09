# S174 / TD downstream recovered payload custody — 2026-10-09

This directory is the custody surface for the physical audit performed against the Project Library and the recovered September-8 TD41–TD58 working-artifacts archive.

## What is committed

- `S174_TD_AUDIT_PACKAGE_MANIFEST.csv` — publication map for committed vs hash-only custody artifacts;
- `S174_TD_PHYSICAL_ASSET_MANIFEST.csv` — exact byte count + SHA-256 for the physical Library artifacts used in the audit;
- `scripts/audit/audit_s174_td_downstream_join_20261009.py` — rerunnable audit logic;
- `results/audit/S174_TD_DOWNSTREAM_JOIN_RESULT_20261009.json` — machine audit receipt;
- `docs/agent/S174_DOWNSTREAM_LIBRARY_JOIN_AUDIT_20261009.md` — human adjudication;
- `docs/agent/JEPA_NEW_AGENT_HANDOFF_20261009_POST_S174_DOWNSTREAM_AUDIT.md` — detailed successor takeover.

## Additional local custody generated in this audit

- complete 155-file recovered TD41–TD58 per-file SHA-256 manifest: SHA-256 `fea76c1ae7976ecd17795f0100fd796434507ef9e5088f6d58d72c5d1954b947`;
- exact 78-file recovered `.py`/`.cpp` code bundle: SHA-256 `e39ba5ab80ebdf3ed0a358cdeccb245431d24f4d5a33887a2b0b0662cb5c93c8`;
- complete extracted older corrected-real-TRAIN per-file manifest: SHA-256 `a4beef2bfd2b1d0910cfab05f907f83ca75fed8ac7fd6e63ca016c747763d514`.

These larger custody payloads are hash-referenced rather than newly published as public Git blobs.

## What is deliberately not committed as Git blobs

Large or human-derived binary artifacts remain hash-only custody references, including the S174 RAR, corrected TRAIN ZIP, historical TD working ZIP, discovery subset NPZ, TD50 NPZs, stage count/meta NPZs and matrices, historical result binaries, and row-level `td57_sea_cells.tsv`.

This is deliberate. Their bytes remain in Project/Library custody and are identified by byte count + SHA-256. Do not treat absence from Git blobs as absence from custody.

## Scientific meaning

This custody publication does **not** prove a corrected-S174 replay of TD56/TD57B/TD59. It preserves the evidence needed to audit that claim. The stage-specific corrected-substrate join remains unbound unless a corrected 50K/TD50 rematerialization receipt (or equivalent physical artifacts) is recovered and then connected to a rerun result.

Terminal remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
