# V78 corrected-S174 cache custody search — 2026-10-09

Status: **BLOCKED BEFORE SCIENTIFIC EXECUTION**

This is a non-authorizing custody record for draft PR #242. It records the search for the exact corrected S174 TRAIN cache bytes required to build `V78_MARGINAL_AUTHORITY_V1` directly from authenticated real TRAIN data.

## Required bytes

The canonical V78 F3 authority requires the exact corrected S174 cache produced by `scripts/v77/rebuild_s174_train_cache.py`:

- 42 `*.counts.npz` shards;
- 42 paired `*.meta.npz` shards;
- exact shard digests already recorded by the S174 rebuild receipts;
- the frozen 41,238-address registry;
- the authenticated shard→matrix→operator bridge.

Summary/calibration JSON, envelope statistics, FULL104, historical discovery expression, or regenerated approximations are **not substitutes**.

## Custody that is already closed

- corrected evaluation universe SHA-256: `e950e967dd593b253837017f8bda5c5a683d975074728f4b8fe20c27272b9763`;
- registry SHA-256: `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`;
- class authority SHA-256: `a4f5e325a54014d87d6380f81ce48922a6558f05ffafdaf7c59c1dc3ae705014`;
- 42 unique corrected shard stems mapped to frozen operator indices 0–41 by `results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json`;
- semantic ruling: corrected S174 `source_library` is a per-cell physical library total and must never be used as operator identity.

## Search performed

The following current-project/runtime custody surfaces were inspected for the physical corrected S174 cache bytes:

1. `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`
2. `expression.zip`
3. `checkpoints.zip`
4. `t1_checkpoint_u0200.zip`
5. `v77-runtime-snapshot.zip`
6. `v77-runtime-snapshot-v2.zip`
7. reassembled discovery-expression ZIP custody
8. current conversation / Project files
9. available Library search surfaces
10. GitHub S174 rebuild/replay/custody artifacts

The V77 runtime snapshot contains S174 rebuild code, freeze/build/verify receipts, replay outputs, and compact custody payloads, but **does not contain any corrected `*.counts.npz` or paired `*.meta.npz` cache shards**.

The calibration bundle contains registry/support/metadata authorities and a large metadata SQLite object, but not the corrected S174 cache shards.

The expression bundle contains discovery sampling/operator metadata, not the corrected S174 cache.

Project/Library search returned references and historical statements about corrected TRAIN shards, but no materializable physical shard set.

## Ruling

As of this checkpoint, the exact physical corrected S174 cache bytes are unavailable in the active execution environment. Therefore:

- `V78_MARGINAL_AUTHORITY_V1` may not be produced canonically yet;
- F0–F3 scientific execution remains blocked as a whole;
- F0–F2 may not be run early merely because their code does not consume the F3 authority;
- no summary-derived or reconstructed marginal authority is permitted;
- no parameter, endpoint, or threshold may be changed to bypass this custody requirement.

The correct next action is to continue completing and testing all data-independent V78 code paths while the preexecution gate remains fail-closed. Scientific execution becomes eligible only after the exact corrected shards are physically present and authenticate against the frozen S174 receipts.
