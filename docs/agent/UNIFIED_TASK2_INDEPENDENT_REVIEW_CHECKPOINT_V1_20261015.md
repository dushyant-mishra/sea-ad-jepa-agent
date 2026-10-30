# Unified Task 2 independent-review checkpoint — 2026-10-15

## Review candidate

Draft PR #388 exact head:
`2c391137bf0564d31d39efa1ec0a61e198dbf027`

Accepted/frozen Task 1 base:
`799d2e235901dfad9ce3b305c767a1c989e362f6`

Task 2 is NOT frozen. Unified Task 3 remains blocked pending fresh independent review of this exact head.

Global authority remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.

## Scope

Unified Task 2 implements `TD_EXECUTION_MANIFEST_V1` and current-TD population/data-access law only. Historical synthetic Task 2 remains reusable sealed-custody/RNG substrate and is not treated as completed Unified Task 2.

No target outcome, representation outcome, validation/oracle biological value, Stage 4 authority, or training authority was opened.

## Iterative controller audit history

Initial RED PR #387 head `bca25a15ce24cc0aed2cca119712a56b423dc79c`: 10 intended failures because `manifest_v1.py` was absent.

First GREEN head `3cb85ea2e498218729aa029f0de100fd90154f85`: 10 Task 2 tests + 27 frozen Task 1 tests passed.

Self-audit cycle 1 RED `3f421afc12f887418ed7c3d0dae18777ea22780c`: 4 intended failures. Closed exact policy identity, assignment-input identity, full manifest dependency surface, and fold-schema gaps. GREEN `852571312a5c17523bf45939de71d263d772596f`: 14 Task 2 + 27 Task 1 tests passed.

Self-audit cycle 2 RED `e4fb8c7111b835d95177ce9263da53433e780a69`: 5 intended failures. Closed donor/fold/phase access, protected generic-metadata, trusted assignment-basis string, role-only structural validation, and access-receipt schema gaps. GREEN `94477424c3dbe29f3e0ff89c97517cada0f4ad50`: 19 Task 2 + 27 Task 1 passed.

Self-audit cycle 3 RED `222535934bcafc6bbfabd13fb1be879637ddd345`: 6 intended failures. Closed self-reported-access weakness by adding `PopulationAccessSession`, `OBSERVED_ACCESS_LEDGER_V1`, receipt→ledger identity binding, exact event replay and forbidden-read invalidation. GREEN `5521196253746f2c0f7b80bd2548815557756985`: 25 Task 2 + 27 Task 1 passed.

Self-audit cycle 4 RED `785b1b0270a60f4db77b9da10db06ef05eab77d3`: 6 intended failures. Closed arbitrary caller-population authority by separating fixture mechanics from current-TD authority and requiring actual frozen reader-split bytes. GREEN content head `b77a1be272c7b37198195b82462a4cba608adbe7`: 31 Task 2 + 27 Task 1 passed.

Final review head `2c391137bf0564d31d39efa1ec0a61e198dbf027` changes only CI checkout history depth relative to GREEN4 content; this is required so inherited Task 0 B5 history-sensitive tests can execute.

## Exact-head verification

On exact head `2c391137bf0564d31d39efa1ec0a61e198dbf027`:

- Task 2 workflow run `38676212679`, job `116230286149`: SUCCESS.
  - focused Task 2 suite: **31 passed**;
  - whole `tests/v5/td_unified`: **95 passed**.
- frozen Task 1 workflow run `38676212687`: SUCCESS.
- inherited unified synthetic integration run `38676212758`: SUCCESS.

A prior 95-test attempt had 94 pass / 1 fail solely because shallow checkout prevented the inherited Task 0 B5 test from resolving its historical plan head. `fetch-depth: 0` repaired verification infrastructure; no Task 2 scientific code changed for that repair.

## Current population/access law

Current-TD authoritative policy is built only from actual reader-split raw bytes whose SHA-256 equals:
`efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511`.

It also binds canonical population registry SHA-256:
`50b29d7e1137c5a457fd0b528580030dedfbeff1b809e2b426f8f640ae38486d`.

The exact split is 149 donors: 104 `reader_fit`, 22 `reader_validation`, 23 `reader_oracle`.

Five donor-grouped folds are used only within `reader_fit`. Current authoritative assignment law is:
`DONOR_SHA256_ORDER_ROUND_ROBIN_V1`.

The earlier source-stratified prelaunch draft was prospectively superseded before any outcome-bearing Task 2 execution because an exact donor→source registry with equivalent custody was not bound. Generic source-stratified construction survives only as `FIXTURE_UNBOUND` mechanics and cannot satisfy current-TD population authority.

This was an outcome-blind pre-execution identity change, not a post-result optimization.

## Access enforcement

- validation/oracle expose partition identity only upstream;
- biological values, generic protected metadata, support summaries and calibration statistics are forbidden;
- reader-fit access is fold/phase/donor scoped;
- TRAIN cannot access held-out donors;
- EVAL cannot access training donors;
- producer access must be generated through the instrumented session and exact access ledger;
- receipt validation resolves and re-hashes that ledger and requires exact event equality;
- forbidden reads invalidate the session before values are returned;
- raw-file SHA-256 is recomputed from actual bytes;
- controller code Git-blob identity is recomputed from actual bytes;
- manifest semantic dependency identities are resolved/re-hashed and cross-role reuse is refused.

## Important runtime boundary

`PopulationAccessSession` is an application-level enforcement contract, not an OS/security sandbox. Same-process malicious Python could introspect private object state. Real protected partitions therefore must remain physically absent from the producer process; later runtime qualification must enforce storage/process boundaries where needed. Task 2 does not claim cryptographic or OS isolation.

## Independent-review gate

Next lawful action is a fresh independent Macha review of exact head `2c391137...`. Do not reopen Task 0/1 or rerun settled biological audits. Task 2 may be frozen only if the exact review accepts this head. Task 3 may not start before that freeze.
