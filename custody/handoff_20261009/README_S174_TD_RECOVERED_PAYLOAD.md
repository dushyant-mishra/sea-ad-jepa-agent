# S174 / TD downstream recovered payload custody — 2026-10-09

This directory is the custody surface for the physical audit performed against the Project Library and the recovered September-8 TD41–TD58 working-artifacts archive.

Committed surfaces:
- `S174_TD_AUDIT_PACKAGE_MANIFEST.csv`
- `S174_TD_PHYSICAL_ASSET_MANIFEST.csv`
- `scripts/audit/audit_s174_td_downstream_join_20261009.py`
- `results/audit/S174_TD_DOWNSTREAM_JOIN_RESULT_20261009.json`
- `docs/agent/S174_DOWNSTREAM_LIBRARY_JOIN_AUDIT_20261009.md`
- `docs/agent/JEPA_NEW_AGENT_HANDOFF_20261009_POST_S174_DOWNSTREAM_AUDIT.md`

Additional locally generated custody, preserved by SHA-256:
- complete 155-file recovered TD41–TD58 per-file manifest: `fea76c1ae7976ecd17795f0100fd796434507ef9e5088f6d58d72c5d1954b947`;
- exact 78-file recovered `.py`/`.cpp` code bundle: `e39ba5ab80ebdf3ed0a358cdeccb245431d24f4d5a33887a2b0b0662cb5c93c8`;
- extracted older corrected-real-TRAIN per-file manifest: `a4beef2bfd2b1d0910cfab05f907f83ca75fed8ac7fd6e63ca016c747763d514`.

Large or human-derived binaries remain hash-only custody references, including the S174 RAR, corrected TRAIN ZIP, historical TD working ZIP, discovery subset NPZ, TD50 NPZs, stage matrices/results, and row-level `td57_sea_cells.tsv`. Their absence from Git blobs is not absence from custody.

This publication does **not** prove a corrected-S174 replay of TD56/TD57B/TD59. The missing link remains a corrected 50K/TD50 rematerialization joined to an exact stage rerun receipt.

Terminal:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
