# S174 local cache transfer — custody handoff (2026-10-09)

**Terminal:** `PASS_S174_RAR_EXACTLY_MATCHES_G1B_AUTHORIZED_CORRECTED_CACHE`

Custody and transfer verification only. No S174 scientific finding changes, and nothing was regenerated or repaired.

## Archive

| field | value |
|---|---|
| path | `D:\Jepa project\data\cache\s174_rebuilt_real_train_v1.rar` |
| bytes | 47,964,366 |
| SHA-256 | `88067f2efb5d8a0168eb352f83bd9de88c3b929c95a8f8fa1c40a6e34c568a2f` |
| verified (UTC) | 2026-10-09T21:02:16Z |
| entries | 85 = 1 directory record (`s174_rebuilt_real_train_v1`, 0 bytes) + 84 files stored inside it |
| integrity test | `UnRAR.exe t` exit 0 (WinRAR UnRAR 4.00) |
| format | RAR 2.9 (RAR4), no solid archive |

UnRAR 4.00 prints member names without their directory, so a plain listing shows 85 bare names. Extraction shows the layout: one folder holding the 84 shard files.

## Canonical cache

- Root: `D:\Jepa project\data\cache\s174_rebuilt_real_train_v1`
- 84 files, 48,784,948 bytes: 42 shards, each a `counts.npz` / `meta.npz` pair.
- Exactly the expected set: no extra, missing or duplicate files.

## Result

84 of 84 files match exactly. For every file, the S174 authority digest, the live canonical file and the file extracted from the RAR have the same SHA-256 and the same byte size. Per-file rows are in `results/v77/s174_replay/S174_LOCAL_CACHE_TRANSFER_VERIFICATION_20261009.json`.

Authorities, read from the committed S174 records, not from the archive:

- **35 rebuilt HVS/SEA-AD shards:** `results/v77/S174_REBUILD_BUILD_RECEIPT_V1.json` (`68b07f0f…`). This equals the shard digests frozen in `S174_REBUILD_G1B_FREEZE_V1.json` (`0513421e…`), which cites this build receipt. G1b passed, including R7 (rebuilt cache bytes identical to the built artifact): `S174_REBUILD_G1B_RESULT_V1.json` (`c450815c…`).
- **7 NPH shards, carried over unchanged:** `results/v77/S174_REBUILD_FREEZE_V1.json` (`240b2b71…`).

## Method

- **Verifier:** `scripts/v77/verify_s174_cache_transfer.py` (code SHA-256 `9c68f60a…`).
- **Extraction:** into a new temporary directory outside the live cache, with never-overwrite. It refuses to run if the directory exists or overlaps the cache.
- **Fail-closed conditions:** archive test or extraction error, missing member, extra member, duplicate basename, byte or digest mismatch, a live cache that is not exactly the 84 expected files, or a listed entry that is neither a file nor a directory record.
- **Committed test:** `tests/v77/test_v77_s174_cache_transfer_receipt.py` checks that the receipt was produced by the committed verifier and that its expectations equal the committed authorities. The bytes themselves are local-only, because `data/` is not in git.

## At the destination

After transfer, check the RAR's SHA-256 (`88067f2e…`) before extracting. Then compare each extracted file with the 84 authority digests listed in the receipt. The verifier can be rerun there with `--rar`, `--cache` and `--extract-dir` pointed at local paths.

## Known nomenclature defect, recorded only

The corrected 14,417-address evaluation universe still carries the builder's fixed label `TRAIN_PREVALENCE05_19569`. This is a naming defect only. It is not renamed here: a rename would need builder review, a rerun and new downstream identity receipts.

## Boundaries

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`. The original S174 branch is not modified, and nothing is merged.
