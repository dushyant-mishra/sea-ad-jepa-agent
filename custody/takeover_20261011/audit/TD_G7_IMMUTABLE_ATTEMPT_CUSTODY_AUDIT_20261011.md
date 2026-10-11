# TD G7 immutable-attempt custody audit

Date: 2026-10-11

Status: `PREQUALIFICATION_BLOCKER__BUNDLE_WITH_COUNTERPART_AUTH_REPAIR__NO_VALUE_READ`

Affected superseded candidate:
`a509c59238bcdc60b88fa265e7e4473760a41025`

## Finding

Standalone G6 V2 spends its output namespace immediately using `G6_EXECUTION_START.json`, so any later failure leaves durable evidence and the same namespace cannot be reused.

Standalone G7 V2 currently checks only whether the final `--out` receipt path already exists. If G7 raises before the final receipt is written, that path remains absent and the same logical attempt path can be reused.

This conflicts with the frozen standalone-V2 design rule that failed attempts are preserved exactly and later retries require a fresh namespace/attempt identity.

No G7 execution has occurred, so no historical result or current evidence is affected.

## Required successor behavior

Before any G7 value-bearing work is permitted, the successor must spend an immutable attempt identity.

Recommended narrow behavior:

1. Treat `--out` as the final receipt path as today.
2. Derive a deterministic sidecar start marker, for example `<out>.start.json`.
3. Reject execution if either the final receipt or the start marker already exists.
4. After runtime authorization + same-authority G6 PASS are validated, but before any S174/physical count values are opened, write the start marker containing:
   - schema/status `STARTED_NOT_A_PASS`;
   - exact authority trace;
   - exact G6 receipt SHA;
   - `biological_replay_authorized=false`;
   - `target_selection_authorized=false`;
   - `td60_authorized=false`;
   - `training_authorized=false`.
5. Any later exception leaves the start marker in place and therefore spends the attempt permanently.
6. A successful final receipt does not erase or overwrite the start marker.

## Required regression tests

Add focused tests proving:
- an initially unused G7 output path creates the start marker before any value loader is reachable;
- a failure after the marker is written leaves it in place;
- a retry using the same output/marker is rejected;
- pre-existing final receipt is rejected;
- pre-existing start marker without final receipt is also rejected;
- no start marker is falsely labeled PASS or value/biology/training authority.

## Combined successor scope

Bundle this with the already-frozen counterpart-auth sequencing repair:
- authenticate physical H5AD and S174 count shard before either counterpart count source is opened;
- physical-H5 authentication failure with natural overlap must prevent S174 count loading.

Do not change scientific thresholds, overlap definition, replay addresses, G1b authority, Sample-A geometry, G6 normalization, or comparison tolerance.

## Boundary

This audit creates no value authorization and reads no corrected expression value.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
