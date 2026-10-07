# JEPA TD56–TD59 historical panel recovery receipt — 2026-10-07

Status: `EXACT_HISTORICAL_PANEL_LINEAGE_RECOVERED__NO_REAL_RNA_EXECUTION_AUTHORITY`

## Purpose

Recover the exact historical molecular membership used by the TD56→TD59 relational target-discovery lineage before any corrected-value replay. This receipt is panel/provenance recovery only; no real-RNA biological result was recomputed.

## Recovered authorities

From the Library-owned `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`:

- `FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz`
  - observed SHA-256: `852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537`
  - expected historical SHA-256: same
  - shape: `42 x 41,238`
  - state names: `STRUCTURALLY_UNMEASURED`, `MEASURED_SCALAR`, `MEASURED_COLLISION_UNRESOLVED`
- `FOUNDATION_SUPPORT_ADDRESS_RECURRENCE.csv`
  - observed SHA-256: `8f90c91e333eba6b58c39767069addef72bb4d9d6015ad8de14e7ff383c092da`
  - expected historical SHA-256: same

Using the exact historical generator semantics from commit `3971b2ec391a512074adf8cc82933ae25888e46a`:

`common = (states == MEASURED_SCALAR).all(axis=0)`

and writing the historical columns in canonical address order:

- recovered common-core rows: `17,186`
- recovered common-core CSV SHA-256: `8aa8dfebb481aa2e60b12ab0f581ba1a36063b6c12dc2d8514d5fe7a20ad07ac`
- expected historical common-core SHA-256: same

Therefore the exact original 17,186-address membership has been recovered, not approximated or regenerated from a new support definition.

## Historical ranking

The exact historical ranking is:

`sort(common_addresses, key = SHA256("TD56S|gene|<address_index>"))`

The complete TD56–TD59 lineage occupies positions `0..9215`, exactly 9,216 historical addresses.

A local recovery manifest was produced with columns:

- `td56_gene_rank_position`
- `historical_screen_block`
- `molecular_address_index`
- `molecular_address_id`
- `symbol`

Local manifest SHA-256:

`b1287b46b2fb0d402ed656b4a370d3aac589d2f27a961edda0b590c69d1b605f`

The 9,216-address manifest is a replay-custody object only. It is not a production vocabulary or target dimension.

## Position allocation

| Screen | Positions | Genes |
|---|---:|---:|
| TD56 / TD57A / TD58 | 0..1023 | 1,024 |
| TD57B | 1024..3071 | 2,048 |
| TD57C | 3072..6143 | 3,072 |
| TD59 | 6144..9215 | 3,072 |

## Cross-check against original working artifacts

Library archive:

`JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip`

Recovered historical metadata artifacts and observed SHA-256:

- `td50_HVS.npz`: `d6d30cb5ef791fdaaa6f751ee6d802f8e64e062ab641a48194dfc9b596609aeb` — 1,129 A rows
- `td50_NPH52.npz`: `9de0c199414db0705d25cce18cb5007915bcf527c245ed039e2f966437c790fe` — 1,310 A rows
- `td50_SEA_AD.npz`: `ab4fa37a2596de609b4245e82dec0ba7e4a43f95d03421acd46c5814eaaa57d4` — 22,561 A rows

These exactly match the hashes hard-bound in the historical TD59 executor.

The recovered 9,216 ranking was also checked against the original opened TD57B/TD57C JSON outputs:

- TD57B Panel0 X: exact
- TD57B Panel0 Y: exact
- TD57B Panel1 X: exact
- TD57B Panel1 Y: exact
- TD57C Panel0 Z: exact
- TD57C Panel0 X: exact
- TD57C Panel0 Y: exact

## TD59 independent hash verification

Using the recovered positions 6144..9215 and the exact TD59 pair-selection preimage from the preserved executor, all six prospectively frozen TD59 gene hashes and all six prospectively frozen pair-address hashes reproduce exactly.

Panel 0:

- Z gene: `f09455c4f5c120785608eda0c870bb299951814e895bbb7ff9d4dcf94b5680b2` — MATCH
- Z pairs: `806553cdacc4d1e3214a2d61880b8795ca4a0637f3762280750cfb502dcd36ed` — MATCH
- X gene: `a365be9aa9ccfc80adddfeb080f8fc6b0c0bc515554bace7076b5cf31a990ae5` — MATCH
- X pairs: `5d9f539d723117bffebfbcd57feefb9b880c50bc4c0aaab55dc9c9f9411a99fd` — MATCH
- Y gene: `124246edc85f082477fb354f6f20c09752a08a1e079c509a6f94648658b31bd3` — MATCH
- Y pairs: `eb6182759465df0e719bc793781ce0964e9a766761508ebe7bb192eda05defad` — MATCH

Panel 1:

- Z gene: `2e1b171e833e248c9107b3f619df66f8ea33677bec7832aad58c6885ba4ae7be` — MATCH
- Z pairs: `960741f9b74118e8991cb859e3f044176afa8151eed3dace3f7b98102198db84` — MATCH
- X gene: `8ef683be715f471f2a0f95531183416d75613eac43c745aa0ab10c7b59db6fa5` — MATCH
- X pairs: `d28d1bd09181bbfd24ca3d737a95a6d911ace6906a5e94d6bbdf133bbc33e0da` — MATCH
- Y gene: `e3dc6ad8c685155458c978d7c5127f26536098a88a10a5d87a6ac127b1689959` — MATCH
- Y pairs: `bc81c334afdcf169a0e4636ec5f76da51e248b4ac35821e26b2a71b8dbe4599f` — MATCH

This independently closes the exact historical panel-membership question through TD59.

## What remains open

Panel identity is no longer the blocker.

The next replay dependency is corrected expression rematerialization for the exact historical `A_NATURAL_MIXTURE` rows `0..24,999`, using matrix-native physical feature identity for these exact 9,216 historical addresses.

The historical 50K normalized matrix cannot supply corrected HVS/SEA-AD gene values because it is the contaminated substrate being replayed.

Macha/S174 corrected identity/decoder logic should be reused where applicable, but the V77 rebuilt cache cannot substitute for the exact historical A-row population.

## Boundaries

No target result is reopened by this receipt.

`REAL_RNA_REPLAY = NOT_AUTHORIZED`
`STAGE_A_EXECUTION = NOT_AUTHORIZED`
`TRAINING = OFF`
`TARGET_WINNER = NONE`
`REPRESENTATION_WINNER = NONE`
