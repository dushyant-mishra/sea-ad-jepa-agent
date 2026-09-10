# JEPA heavy-asset reference ledger — FINAL R4 — 2026-09-09

Purpose: allow a new chat/runtime to recover required large assets by exact identity without asking the user to download or duplicate them.

## Known uploaded/local large assets in this project runtime

- `/mnt/data/FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`
  - SHA-256: `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`
  - contains the authoritative foundation calibration bundle; historical metadata SQLite member `foundation_metadata_rows.sqlite`.
- `/mnt/data/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001`
  - SHA-256: `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e`
- `/mnt/data/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002`
  - SHA-256: `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875`
- assembled discovery expression archive
  - expected SHA-256: `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`
  - inner full expression NPZ SHA-256: `4c50f1de2446b07bbf3199bba80ebc89749c8104cb7668664ed705dbfc579d92`
- `/mnt/data/FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.parts.sha256.csv`
  - part-hash ledger.
- `/mnt/data/checkpoints.zip`
  - SHA-256: `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c`
- `/mnt/data/t1_checkpoint_u0200.zip`
  - SHA-256: `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c`
- `/mnt/data/expression.zip`
  - SHA-256: `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4`
- `/mnt/data/66e64913-959f-4a7c-bbfe-6ff906fb281d.npz`
  - preserve by exact bytes; determine semantic role from project provenance before use.
- `/mnt/data/t1_checkpoint_u0200.zip`
- `/mnt/data/WSL execution issue.txt`

## Derived local full-population working files from this chat/runtime

These were generated from the authenticated reader-fit metadata and are small enough to regenerate; they are not substitutes for the missing full-reader expression substrate.

- `/mnt/data/fullpop/foundation_metadata_rows.sqlite`
  - expected SHA-256: `a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913`
- `/mnt/data/fullpop/FULL_POPULATION_LEXICOGRAPHIC_OPTIMUM_V1.json`
- `/mnt/data/fullpop/FULL_POPULATION_SCHEDULE_MATERIALIZATION_V1.json`
- `/mnt/data/fullpop/V5_FULL_POPULATION_MULTIPLICITY_LEDGER_V1.bin`
  - raw SHA-256: `e05f4a524748cf427b1c3e899a5b672641566c772aa91da8a2a56dae2b9a3c97`
  - domain-bound SHA-256: `23a5c52e2b472604a9e32c71e114b4752094950180c8d155c7ee45dd95ce8c23`
  - do not need to duplicate into handoff; deterministic replay exists.
- `/mnt/data/fullpop/optimize_full_coverage_schedule.py`
- `/mnt/data/fullpop/materialize_full_population_schedule_fast.py`

## Missing critical physical substrate

The production full-reader corrected expression cache is not currently bound in this runtime.

Expected historical root:
`D:\Jepa project\data\cache\stage81a3r_corrected_real_train`

Required closure:
- 42 corrected TRAIN counts/meta shard pairs
- hashes must match loader manifest SHA-256 `2413390355a42365f6575800ae5f83ab373d05490e8e4567d419366e4ed5b328`
- historical Level-4 representation: 8,915 blocks over 4,553,407 cells × 41,238 addresses
- binder: `scripts/v5_anticheat/bind_full104_expression_blocks_v4.py`
- required terminal: `PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`

Forbidden substitutes: 50K discovery archive, synthetic expression, reader_validation/oracle, DEV/SEALED, pathology, or recomputed different-byte shards without separate re-authorization.

## Recovery rule for new chat

1. Check whether each exact local path is still available.
2. Verify SHA-256 before use.
3. Prefer GitHub for code, contracts, manifests, small evidence and handoff files.
4. Do not duplicate large immutable assets into new handoff ZIPs.
5. If a required large asset is absent, report the exact missing path/hash and fail closed rather than substituting a smaller object.
