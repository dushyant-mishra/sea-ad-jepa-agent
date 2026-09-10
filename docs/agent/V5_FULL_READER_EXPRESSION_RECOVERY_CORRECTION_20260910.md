# V5 full-reader expression recovery correction — 2026-09-10

Status: `TRAIN_CACHE_RECOVERED_EXACTLY__FULL104_BLOCK_STORE_STILL_MISSING__NO_TRAINING_AUTHORITY`

## What the uploaded cache closes

The uploaded `stage81a3r_corrected_real_train.zip` is authentic. Its SHA-256 is
`3b86097d514f1cc2d84b19fd289344e0634356359462173a9b2b0f7541dd7e48` and it
contains the exact 42 corrected TRAIN counts/meta pairs required by the frozen
`foundation-train-loader-v1` manifest.

All 42 counts hashes and all 42 metadata hashes match the frozen loader manifest
whose SHA-256 is
`2413390355a42365f6575800ae5f83ab373d05490e8e4567d419366e4ed5b328`.
There are 4,726 physical TRAIN rows across the 42 shards and 41,238 address
columns. This is a real positive closure, but it is only TRAIN-cache byte
identity.

## What it does not close

The authenticated production reader-fit population contains 4,553,407 cells.
The recovered TRAIN cache contains 4,726 rows, a shortfall of 4,548,681 rows.
It therefore cannot be the FULL104 reader-fit expression store.

The first real invocation of
`scripts/v5_anticheat/build_full_reader_expression_identity_closure_v3.py`
exposed the semantic mismatch fail-closed at operator 0. The matrix had 128
physical TRAIN rows, while the full reader-fit metadata authority had 2,441 rows
for that matrix and reader-fit `local_row` values reached 8,703. Thus full-reader
metadata `local_row` is not an index into the TRAIN-only corrected shard.

The V1 recovery contract incorrectly sequenced "bind the 42 TRAIN shards" into
"open full reader_fit expression." That inference is now superseded. The
historical V3 script is preserved for provenance/tests but must not certify
production FULL104 closure.

## The actual remaining substrate

Historical authority records a separate Phase2/FULL104 Level-4 materialization:

- 4,553,407 reader-fit cells;
- 104 donors;
- 42 operators / 42 matrices;
- 41,238 addresses;
- 8,915 blocks, nominally 512 rows per block with a final partial block;
- historical block root:
  `outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/`;
- block-manifest SHA-256:
  `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`;
- committed manifest pin:
  `21ec629667eeda5a7d37d3f1d822fbf93b213325` / Git blob
  `c780e07f0cf811a75c7ce9c41425f1dba2ba8335`.

The production binder remains
`scripts/v5_anticheat/bind_full104_expression_blocks_v4.py`, whose required
terminal is `PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`.

Until that physical 8,915-block store is located and verified, the current
terminal is:

`STOP_FULL104_PHASE2_BLOCK_STORE_LOCATION_BINDING_MISSING`

No 50K subset, synthetic fixture, TRAIN cache, validation/oracle partition, or
recomputed different-byte substitute may satisfy that terminal.

`training_authorized: false`
