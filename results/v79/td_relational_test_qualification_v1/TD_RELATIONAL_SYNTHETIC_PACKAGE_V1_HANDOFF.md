# TD relational synthetic test-qualification package V1 — handoff

Status: `SYNTHETIC_PACKAGE_QUALIFIED_FOR_BLINDED_TD_TEST_OF_TEST_CONSUMPTION__TD_EXECUTOR_NOT_RUN`

## Package identity

- package ID: `JEPA_TD_RELATIONAL_SYNTHETIC_V1_20261013`
- synthetic branch: `synthetic/td-relational-test-package-v1-20261013`
- prospective contract commit: `304e7e8c3219f5416b6d8dfb1a7a67eb19c63936`
- generator commit: `21219a9a2a2c023271b92a9d3e8e200f37c740eb`
- package/content-manifest SHA-256: `cb3587d635ce087fcc2b12c4a19f95de4bee7c9002498576eaca9a5e92a87cf5`
- controller-truth SHA-256: `5582b719e8e070c661dea9560983e8d971341ea28b47d324edec035c6304bd6b`
- core directory digest SHA-256: `802388849c5efada325ef84b1290a1324b9345d5af96143757646f5c780cd3cb`
- file-ledger SHA-256: `205813eeb4cb27620fa03fa65b22e15e072a77c31db95338020cc61fd95f1222`
- synthetic qualification receipt SHA-256: `3f7151aed4af31d161e06c9afdb2b5f5cb32658bb42b841e30b417140cad4ce4`
- canonical archive SHA-256: `55cb5fbcce3c7a6ffc4c68d4b6f870beb16984d5be144fe5a460a31f6d9b495e`
- canonical archive size: `46784` bytes
- immutable realization ID: recorded in `content_manifest.json`

## Canonical package transport

The exact frozen archive is stored in the persistent ChatGPT Library at:

`/Jepa project/TD qualification/JEPA_TD_RELATIONAL_SYNTHETIC_V1_20261013.tar.xz`

Library file ID:

`file_000000000a5c81f59bacecb95ba6fd57`

The uploaded Library object was materialized back to a fresh local path and compared byte-for-byte with the qualified archive. SHA-256 remained:

`55cb5fbcce3c7a6ffc4c68d4b6f870beb16984d5be144fe5a460a31f6d9b495e`

## Exact-generator verification

The archive core was independently regenerated from the exact repository generator at blob `026e5d2078b9707aad5fc8b099606707ebf4c11f` / commit `21219a9a...`.

All 15 generator-owned core files matched the archive byte-for-byte; `file_ledger.json` and `synthetic_qualification_receipt.json` were excluded from that regeneration comparison because they are packaging/evidence records layered after core generation.

Focused synthetic package tests: `9 passed`.

No TD executor was run during this verification.

## Capability ledger

All requested PR #316 capabilities are present as distinct opaque challenges and are classified honestly as new prospective relational worlds because historical assets did not already expose an explicit controller-separated C2 relational truth object in the exact PR316 blinded distance interface.

| capability | coverage |
|---|---|
| `REL_BROAD_MESO_POSITIVE` | `SATISFIED_NEW_PROSPECTIVE_WORLD` |
| `REL_FINE_RECURRENT_POSITIVE` | `SATISFIED_NEW_PROSPECTIVE_WORLD` |
| `REL_RARE_LOCAL_ISLAND_POSITIVE` | `SATISFIED_NEW_PROSPECTIVE_WORLD` |
| `REL_MULTI_ISLAND_POSITIVE` | `SATISFIED_NEW_PROSPECTIVE_WORLD` |
| `REL_DONOR_RESTRICTED_POSITIVE` | `SATISFIED_NEW_PROSPECTIVE_WORLD` |
| `REL_SOURCE_VISIBILITY_STRESS` | `SATISFIED_NEW_PROSPECTIVE_WORLD` |
| `REL_TECHNICAL_TWIN_NEGATIVE` | `SATISFIED_NEW_PROSPECTIVE_WORLD` |
| `REL_NULL_NEGATIVE` | `SATISFIED_NEW_PROSPECTIVE_WORLD` |
| `REL_UNDERPOWERED_POSITIVE` | `SATISFIED_NEW_PROSPECTIVE_WORLD` |

## Package contents

The archive contains:

- `TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V1.json`
- `TD_RELATIONAL_ADAPTER_PAYLOAD_INDEX_V1.json`
- `fit_view_manifest.json`
- `capability_ledger.json`
- `content_manifest.json`
- `controller_truth.json`
- `file_ledger.json`
- `synthetic_qualification_receipt.json`
- nine opaque `fit_views/*.json`

Fit views expose only the lawful PR316 executor surface:

`source, panel_id, z_distances, x_distances, y_distances, donor_ids, operator_ids, global_rows, focal_mask, neighbor_pool_mask, null_y_identity_maps, min_focal_anchors_per_donor`.

They do not expose capability names, expected verdicts, rare-state truth, technical-twin identity, controller truth, or planted relation labels.

## Synthetic-side qualification

The package qualification receipt records PASS for:

- all nine capabilities present;
- all fit-view hashes correct;
- controller-truth hash correct;
- all authority flags false;
- source-visibility stress preserves identical latent biology;
- technical twin has no biological relational truth;
- null challenge has no biological relational truth;
- underpowered true challenge has only four recurring donors;
- no real TD outcomes used for tuning.

This qualifies the synthetic world/package only. It does **not** qualify the TD gate.

## TD consumption

TD should:

1. obtain the exact Library archive above and verify archive SHA-256;
2. extract it read-only;
3. authenticate `TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V1.json` against package SHA-256;
4. authenticate each opaque fit view using the binding;
5. build the existing PR316 read-only adapter payloads from the extracted fit views;
6. run the TD executor blind;
7. only afterward open `controller_truth.json` and adjudicate test-of-test qualification.

The synthetic lane must not run or adjudicate those TD steps.

## Lane integrity / authority

No code or result in PR #316, PR #313, or PR #314 was modified by this work.

No real TD execution occurred. No target selection, TD60, Stage4, pathology opening, or JEPA training authority is created.

Terminal:

`TD_RELATIONAL_SYNTHETIC_V1_PACKAGE_FROZEN_AND_SYNTHETICALLY_QUALIFIED__NINE_OF_NINE_CAPABILITIES__BLINDED_FIT_VIEWS__CONTROLLER_TRUTH_SEPARATE__TD_EXECUTOR_NOT_RUN__PR316_PR313_PR314_UNTOUCHED__REAL_TD_OFF__TRAINING_OFF`
