# Stage81A3R Corrected Real TRAIN ZIP Receipt

Date: 2026-09-11
Source file verified in ChatGPT environment: `/mnt/data/stage81a3r_corrected_real_train.zip`
Status: `USEFUL_CORRECTED_TRAIN_CACHE_ONLY__NOT_FULL104__NO_TRAINING_AUTHORITY`

## File identity

- Size bytes: `50647044`
- SHA-256: `3b86097d514f1cc2d84b19fd289344e0634356359462173a9b2b0f7541dd7e48`
- ZIP integrity: `PASS` (`ZipFile.testzip()` returned `None`)
- ZIP entries: `99`
- Compressed payload bytes: `50619734`
- Uncompressed payload bytes: `58677713`

## Structural contents

Top-level directory: `stage81a3r_corrected_real_train/`

Entry types:

- `.npz`: `84`
- `.mtx`: `7`
- `.csv`: `7`
- directory entry/no extension: `1`

No formal package manifest, package-root SHA file, or FULL104 production closure receipt file was present by filename.

## Corrected TRAIN shard check

The NPZ shard structure matches the corrected TRAIN-cache signature already recorded in project governance:

- Counts shards: `42`
- Meta shards: `42`
- Matched counts/meta pairs: `42`
- Pair row/metadata/column mismatches: `0`
- All counts matrices: CSR
- All count matrices have `41238` columns / molecular addresses
- Total NPZ rows: `4726`
- Total NPZ nonzeros: `21582917`
- Unique donors across NPZ metadata: `149`

The seven Matrix Market count files are small class-level corrected TRAIN artifacts. Their metadata CSVs total `246` rows and their matrices all have `41238` columns. They are useful as small real-row mechanics fixtures, but they are not the FULL104 production expression store.

## FULL104/B2 marker search

Exact marker search over decompressed ZIP entries found the following markers absent:

- `PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`
- `STOP_FULL104_PHASE2_BLOCK_STORE_LOCATION_BINDING_MISSING`
- `FULL104`
- `4553407`
- `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`
- `PASS_EXACT_CORRECTED_TRAIN_CACHE_BYTE_BINDING_ONLY`

Red-team caveat: the string `8915` appears inside Matrix Market coordinate data as a column/address index, not as evidence of an 8,915-block FULL104 store. The string `B2` appears in cell IDs or binary compressed content, not as a B2 production closure receipt.

## Usefulness decision

Useful for:

- corrected TRAIN-cache byte/shape/metadata verification;
- exact-real-row loader and mechanics tests;
- anti-cheat smoke tests that require corrected real TRAIN rows;
- proving 42 counts/meta shard-pair alignment at 41,238-address shape.

Not useful for, and must not be treated as:

- FULL104 4,553,407-cell production expression store;
- 8,915-block Level-4 block-store closure;
- `PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`;
- T0 V21 freeze authority;
- S0-S4 execution authority;
- reader_validation/oracle opening authority;
- V5 production training authority.

## Terminal classification

`stage81a3r_corrected_real_train.zip` should be preserved as corrected TRAIN-cache evidence. It does not close the current FULL104/B2 production expression blocker and does not authorize protected-data access, target freeze, S0-S4 execution, or training.
