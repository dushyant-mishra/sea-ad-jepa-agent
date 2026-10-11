# JEPA chat-surface custody sweep — 2026-10-10

Status: `CUSTODY_SWEEP_COMPLETE__NO_NEW_SCIENTIFIC_AUTHORITY__NO_TRAINING_AUTHORITY`

This package preserves the artifacts available in the 2026-10-10 ChatGPT project surface that are not appropriate to duplicate as raw heavy Git blobs, plus exact small audit/design records that are safe to commit.

Hard terminal remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Current target-discovery execution state

The self-audit-hardened G4/G5 execution at code freeze `b3ff8366f28280e7d3269c305efa6317a05c8834` has now failed twice in independent fresh namespaces, preserved on PR #252 and PR #254.

Recorded failure terminal:

`FAIL_TD_RELATIONAL_PREFLIGHT_DRIVER_AT_G4_G5_MAPPING_ENTRY__SAMPLE_A_GEOMETRY_MISMATCH__LABEL_LITERAL_A_VS_A_NATURAL_MIXTURE`

Both runs reached the exact manifest builder PASS (`PASS_EXACT_HISTORICAL_RELATIONAL_REPLAY_MANIFEST`, frozen manifest SHA `4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660`) and then stopped in the value-blind mapping loader before opening any H5AD or expression array.

Post-hoc metadata-only diagnosis preserved by the execution PRs:

1. code selects literal `sample == "A"`, while the frozen Sample-A label is `A_NATURAL_MIXTURE`;
2. even after correcting that literal, frozen Sample A spans 34 of the 35 S174-frozen H5AD matrices, so the present `all_35_h5_source_sha256_verified` gate requires separate adjudication rather than an automatic threshold edit.

No G6/G7 value read was run. PR #251 wrapper code remains superseded and DO NOT EXECUTE; standalone V2 is design-only.

## Local artifact policy

Raw immutable heavy assets are not duplicated into Git history when their exact bytes were already historically hash-bound. This sweep records byte size, SHA-256, archive member index, and embedded manifests where available.

Small exact records are committed verbatim under `custody/chat_surface_20261010/`.

### Heavy/reference-only assets

- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip` — 410,278,055 bytes — SHA-256 `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`.
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001` — 303,979,881 bytes — SHA-256 `b8163f53a27f7cb1b526f8311d1b46b599502596c5d0be74fa588747a4e72b2e`.
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002` — 303,979,880 bytes — SHA-256 `5bc2ec30fb374b15f1c5a4764e1856b0664c13513462ef2f7e224c4b6f856875`.
- assembled discovery-expression archive authority from the provided split manifest — 607,959,761 bytes — SHA-256 `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`.
- `checkpoints.zip` — 71,356,460 bytes — SHA-256 `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c`.
- `t1_checkpoint_u0200.zip` — 233,729,581 bytes — SHA-256 `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c`.
- `expression.zip` — 3,599,456 bytes — SHA-256 `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4`.
- `66e64913-959f-4a7c-bbfe-6ff906fb281d.npz` — 1,531,109 bytes — SHA-256 `001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70` — remains `PROVENANCE_MISMATCH_DO_NOT_USE`.

## Exact small records committed by this sweep

- `CHAT_LOCAL_ARTIFACT_INVENTORY_20261010.csv`
- `CHAT_LOCAL_ZIP_MEMBER_INDEX_20261010.csv`
- `FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.parts.sha256.csv`
- `FOUNDATION_CALIBRATION_BUNDLE_20260824__BUNDLE_SHA256_MANIFEST.csv`
- `FOUNDATION_CALIBRATION_BUNDLE_20260824__BUNDLE_STATUS.json`
- `checkpoints__checkpoint_manifest.json`
- `expression__FOUNDATION_DISCOVERY_EXPRESSION_AUDIT.json`
- `expression__FOUNDATION_DISCOVERY_SAMPLE_FREEZE.json`
- `OPERATOR_ADDRESS_STATE_NPZ_STRUCTURE_AUDIT_20261010.json`
- raw `Status and Repair Plan.txt`
- raw `WSL execution issue.txt`

The raw text files are preserved as historical reasoning/audit material only. They do not override newer frozen contracts or current PR-level authority.

## Authority interpretation

This custody sweep creates no target, no representation winner, no corrected biological replay PASS, no value-read authority, and no training authority. Where an uploaded historical artifact conflicts with newer audited state, the newer controlling handoff/PR record wins; the older bytes remain historical evidence.
