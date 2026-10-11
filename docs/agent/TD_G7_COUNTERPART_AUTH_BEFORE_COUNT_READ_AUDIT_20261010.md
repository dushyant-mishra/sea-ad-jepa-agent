# TD G7 counterpart-authentication-before-count-read audit

Date: 2026-10-10

Status: `PREQUALIFICATION_BLOCKER__PR263_CURRENT_HEAD_DO_NOT_QUALIFY__NO_VALUE_READ`

Affected candidate head:
`a509c59238bcdc60b88fa265e7e4473760a41025`

## Finding

The current G7 overlap loop correctly:
- re-hashes S174 metadata immediately before using `cell_id`;
- determines natural overlap;
- re-hashes S174 count shard immediately before opening S174 counts;
- later exact-hashes the physical H5AD before opening its value slot.

However, on an overlap matrix the current order is:

1. authenticate/use S174 metadata;
2. determine overlap;
3. authenticate and open S174 count values;
4. only afterward authenticate the physical H5AD;
5. then open physical H5AD values and compare.

Thus if the physical H5AD is missing or fails its exact SHA, G7 has already opened S174 count values unnecessarily.

This does not invalidate any executed result because G7 has never run. It is a least-privilege/value-read sequencing defect found before qualification.

## Required successor behavior

For every matrix with natural overlap, before either side's count values are opened:

1. authenticate S174 metadata and establish natural overlap;
2. resolve the physical H5AD authority;
3. exact-hash the physical H5AD and require its frozen SHA;
4. exact-hash the S174 counts shard and require its G1b frozen SHA;
5. only after both counterpart count sources are authenticated, open/read count values;
6. record both exact verified hashes in the G7 receipt.

No scientific comparison rule, tolerance, overlap definition, replay-address set, G1b authority, or Sample-A geometry may change.

## Required regression test

Add a focused test proving that when an overlap exists but physical H5AD authentication fails, the S174 count loader is never invoked / no S174 count values are opened.

Existing tests for S174 immediate reauth, duplicate IDs/indices, no-overlap behavior, physical H5 SHA and non-success exits remain required.

## Disposition

Current PR #263 head is superseded for qualification until this narrow sequencing defect is repaired and tests are added. Do not qualify or execute `a509c59238bcdc60b88fa265e7e4473760a41025`.

No runtime authorization exists. No G6/G7 execution occurred. No corrected value was read.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
