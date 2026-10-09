# Synthetic dataset lane handoff update — repaired S174 substrate distinction — 2026-10-09

Status: **V78 EXECUTION REMAINS FAIL-CLOSED; HISTORICAL STAGE81A3R ZIP IS NOT THE CURRENT REPAIRED-S174 EXECUTION SUBSTRATE.**

This handoff supersedes the earlier interpretation that `/Jepa project/stage81a3r_corrected_real_train.zip` could directly close the current V78 F3 byte-custody gate.

## What was re-audited

Two persistent Library assets are distinct custody objects:

1. Historical Stage81A3R corrected TRAIN archive
   - `/Jepa project/stage81a3r_corrected_real_train.zip`
   - bytes: `50647044`
   - SHA-256: `3b86097d514f1cc2d84b19fd289344e0634356359462173a9b2b0f7541dd7e48`
   - 42 count + 42 meta shards
   - exact match to its historical frozen loader-manifest lineage (`2413390355a42365f6575800ae5f83ab373d05490e8e4567d419366e4ed5b328`).

2. Macha S174-rebuilt TRAIN archive
   - `/Jepa project/s174_rebuilt_real_train_v1.rar`
   - bytes: `47964366`
   - SHA-256: `88067f2efb5d8a0168eb352f83bd9de88c3b929c95a8f8fa1c40a6e34c568a2f`
   - count identity root: corrected calibration SHA-256 `f6ba2c725a5437cc8455fff418027d36efe9ea9430fbd0a5765df62dedca6068`
   - paired-meta identity root: V78 semantic digest `b876e13526f51d5a4199ca750ad09065c5ab8a20aeca39dff3d8c385f2241f46`.

## Direct byte cross-authentication

The Stage81A3R ZIP was extracted and every one of its 42 count shards and 42 meta shards was independently SHA-256 checked against the current repaired-S174 receipts used by the V78 gate.

Result:

- count shards matching repaired S174: **7/42**;
- meta shards matching repaired S174: **7/42**;
- paired stems matching on both sides: **7/42**;
- paired stems differing: **35/42**.

The seven matching stems are:

- `01a8084c32680dfb`
- `5a1c193be7cd49cc`
- `65db086233248c4c`
- `697169906cb1a773`
- `728ef515d050d789`
- `868d05542e5e7cf2`
- `e5ef92fa6bf68bb4`

Therefore these two archives are **not byte-equivalent corrected-cache packages**.

## V78 consequence

The current PR #242 gate correctly rejects historical loader-manifest-only provenance. The canonical V78 F3 authority must bind the Macha repaired-S174 lineage: corrected calibration, paired-meta semantic digest, repaired archive SHA, operator bridge, and all physical shard bytes.

The Stage81A3R archive remains valid historical custody and remains useful for reconstructing its own earlier lineage, but it may not be substituted for the current repaired S174 cache merely because filenames/stems overlap.

Accordingly:

- prior statements that the Stage81A3R ZIP alone resolved the current V78 raw-byte blocker are superseded;
- the compact authority previously derived from that historical ZIP is not sufficient for current canonical V78 execution;
- F0–F3 scientific execution remains blocked until the Macha repaired cache is physically readable and authenticates 42/42 count + 42/42 meta shards under the current gate;
- no V78 scale, arm definition, seed, endpoint, or threshold changes are authorized by this correction.

Machine-readable current-lane receipt: `results/v78/V78_S174_SUBSTRATE_DISTINCTION_V1.json` on PR #242.

## Hard boundaries

No JEPA/real-data training. No E4. No target-discovery changes. No 353-ID repair. No TEST/Morabito. No 500K/Stage4. No post-outcome retuning.
