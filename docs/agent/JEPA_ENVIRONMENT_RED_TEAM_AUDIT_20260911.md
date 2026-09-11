# JEPA Environment Red-Team Audit — 2026-09-11

Status: `PASS_ENVIRONMENT_RED_TEAM_WITH_FULL104_REMOTE_ONLY_BOUNDARY__NO_TRAINING_AUTHORITY`

## Scope

This audit independently re-checks the local asset receipt using shell-native `stat`, `sha256sum`, concatenation hashing, and `unzip -t`; reviews the uploaded corrected TRAIN cache classification; and resolves the production FULL104/B2 verifier from repository history. It does not open protected validation/oracle data, execute S0-S4, fit a model, or authorize training.

## Independent shell verification

The following checks were rerun independently of the original receipt-generation code.

### Split discovery archive

- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001`
  - bytes: `303979881`
  - SHA-256: `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e`
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002`
  - bytes: `303979880`
  - SHA-256: `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875`
- assembled `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip`
  - bytes: `607959761`
  - SHA-256: `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`
- streaming `cat part001 part002 | sha256sum` reproduced the assembled SHA exactly.

These values agree with the supplied split manifest and the local environment receipt.

### ZIP integrity

`unzip -t` independently passed for all of:

- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip`
- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`
- `checkpoints.zip`
- `expression.zip`
- `t1_checkpoint_u0200.zip`
- `stage81a3r_corrected_real_train.zip`

### Independently repeated outer-file SHA-256 values

- calibration bundle: `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`
- checkpoints: `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c`
- expression: `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4`
- T1 u0200 archive: `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c`
- corrected real TRAIN: `3b86097d514f1cc2d84b19fd289344e0634356359462173a9b2b0f7541dd7e48`
- operator-address NPZ: `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70`

The operator-address NPZ remains `PROVENANCE_MISMATCH_DO_NOT_USE` under project governance. Re-hashing it does not repair provenance.

## Correction caught by red-team review

An earlier conversational summary misstated the two split-part sizes. The authoritative local receipt itself was correct. The correct part sizes are:

- part001: `303979881`
- part002: `303979880`

Their sum is exactly `607959761`, and their concatenated hash equals the assembled archive hash. No asset bytes were changed; this was a reporting/bookkeeping correction.

## Corrected TRAIN cache classification

`stage81a3r_corrected_real_train.zip` remains useful corrected TRAIN-cache evidence only:

- 42 counts NPZ shards
- 42 meta NPZ shards
- 42/42 matched pairs
- 4,726 NPZ rows
- 41,238 addresses
- 149 donors represented in metadata
- ZIP integrity PASS

It is not the 4,553,407-row FULL104 production expression substrate and does not close the 8,915-block production binding.

## FULL104 receipt search status

The earlier bounded archive-text/metadata scan did not find the exact terminal:

`PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`

This audit does not overclaim a second independent exhaustive content scan: a combined shell `zipgrep` attempt exceeded the environment command time limit after the integrity checks, so marker absence is grounded in the prior bounded scan rather than that timed-out shell attempt. Marker-like values such as `4553407`, `8915`, or `B2` in historical metadata are not closure receipts.

## Production FULL104 verifier resolved from repository history

The older `scripts/v5_anticheat/build_full_reader_expression_identity_closure_v3.py` must not be used as a substitute for production FULL104 closure from TRAIN-row space.

The production FULL104 cross-ledger binder on the V5 lineage is:

`scripts/v5_anticheat/bind_full104_expression_blocks_v4.py`

at:

`planning/v5-full-population-cheat-proofing-20260909 @ 1de20b1c222c7fb27fcef5ec1a4b798d5b26a534`

Its production geometry is hard-bound to:

- 4,553,407 cells
- 104 donors
- 42 operators
- 42 matrices
- 8,915 blocks
- 41,238 addresses
- sources `HVS`, `NPH52`, `SEA_AD`
- 512 block rows
- sample level 4

Its exact PASS terminal is:

`PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`

The same lineage contains `tests/test_bind_full104_expression_blocks_v4.py`, which exercises cross-ledger identity mismatch, invalid source-library semantics, source identity mismatch, duplicate selection-row/cell identity, and other fail-closed cases using synthetic fixtures only.

## Remote-only boundary

The >30GB FULL104 substrate is intentionally not available in this environment. Its absence from `/mnt/data` is not evidence that it is missing. Claude should execute the exact production binder only on the GPU-enabled laptop / attached hard-drive environment after authenticating the expected inputs and first checking whether the terminal receipt already exists.

## Prohibitions preserved

This audit does not authorize:

- S0-S4 production execution
- AT8 opening
- protected partition opening
- `reader_validation`
- oracle
- V21 freeze
- production training
- optimizer steps / EMA / training checkpoint creation

Standing rule: `IF_CONFIRMATION_DATA_COULD_CHANGE_A_DESIGN_CHOICE_DO_NOT_LOOK`.

## Terminal

`PASS_ENVIRONMENT_RED_TEAM_WITH_FULL104_REMOTE_ONLY_BOUNDARY__NO_TRAINING_AUTHORITY`
