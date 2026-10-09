# Synthetic dataset lane handoff update — corrected S174 cache recovered — 2026-10-09

Status: **CUSTODY BLOCKER CLEARED / SCIENTIFIC EXECUTION STILL FAIL-CLOSED**

The exact corrected Stage81A3R TRAIN cache was recovered from the persistent Library at:

`/Jepa project/stage81a3r_corrected_real_train.zip`

Authenticated archive identity:

- size: `50,647,044` bytes
- SHA-256: `3b86097d514f1cc2d84b19fd289344e0634356359462173a9b2b0f7541dd7e48`
- archive members: `99`
- corrected shard payload: exactly `42 *.counts.npz` + `42 *.meta.npz`

The frozen production-loader manifest was recovered from the authenticated calibration bundle and rehashed to the expected authority:

`2413390355a42365f6575800ae5f83ab373d05490e8e4567d419366e4ed5b328`

Every corrected shard was independently hashed and matched against that manifest using the historical deterministic stem rule `sha256("corrected|" + matrix_id)[:16]`.

Verification result:

- matched shard pairs: `42/42`
- count-file hash mismatches: `0`
- meta-file hash mismatches: `0`
- total physical corrected shard bytes: `48,382,320`

Durable machine-readable receipt:

`custody/synthetic_dataset_20261008/S174_CORRECTED_TRAIN_CACHE_RECOVERY_CUSTODY_V1.json`

This clears the V78 raw-byte custody blocker only. It does **not** itself authorize scientific F0–F3 execution or any training. The next lawful step is to implement the canonical corrected-cache reader under RED→GREEN tests, build `V78_MARGINAL_AUTHORITY_V1` directly from these authenticated bytes, and require the preexecution gate to authenticate that derived authority before running the frozen F0–F3 tournament.

Hard boundaries remain unchanged: no JEPA training, no real-data training, no E4, no TEST/Morabito, no 500K/Stage4, no target-discovery changes, no 353-ID repair, and no post-outcome retuning.
