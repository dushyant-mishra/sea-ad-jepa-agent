# JEPA iterative owner audit and custody protocol V1 — 2026-10-15

Status: `CONTROLLING_PROCESS_CUSTODY__NON_AUTHORIZING`

Binding authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Purpose

This protocol defines how the lane owner works from this point forward. It exists so scientific and engineering work is repeatedly challenged while it is being built, and so a future successor can inherit the lane without reconstructing history from chat or repeating settled audits.

## Iterative work law

Every substantive task is performed in repeated cycles rather than a single implementation pass:

1. classify the claim or change as `ALREADY_AUDITED`, `SUPERSEDED`, `OPEN`, or `CHANGED_INPUT_REQUIRES_REQUALIFICATION`;
2. recover and reuse the controlling historical evidence before designing new work;
3. write discriminating RED/hostile checks for genuinely open or changed interfaces;
4. verify the RED failure is for the intended reason;
5. make the smallest lawful repair/implementation;
6. run focused GREEN;
7. run inherited regression/compatibility tests;
8. perform a hostile self-audit against scientific semantics, leakage, authority and custody;
9. repair any new finding and repeat the cycle until clean;
10. verify exact branch/head/workflow identities;
11. seek logically independent review where the qualification contract requires it;
12. freeze the accepted exact head and update durable custody/handoff surfaces.

Passing tests are evidence, not scientific authority. A controller self-audit does not substitute for an independent reviewer where independence is required.

## Continuous no-repeat custody

After every meaningful audit, repair, implementation, qualification or rejection, update the durable repository surfaces so the work is not repeated later.

Preserve, as applicable:
- exact commit/head and parent lineage;
- governing plan/spec identity;
- scripts and test files;
- machine-readable ledgers/manifests;
- RED evidence and hostile probes;
- GREEN/regression workflow IDs and test counts;
- result artifacts and receipts;
- scientific interpretation and authority ceiling;
- negative results and closed experiments;
- superseded/rejected authority states;
- unresolved questions and next lawful action;
- independent-review verdicts;
- environment/runtime/GPU evidence when relevant;
- data/artifact provenance and hashes.

PR #322 is the canonical audit/custody surface. PR #323 is the successor/navigation handoff surface. Both must be refreshed after meaningful accepted state changes.

## Historical evidence reuse rule

Do not restart an audit merely because the active conversation changed.

Before opening any new audit, answer:
1. what exact claim is being qualified;
2. where its prior audit/evidence lives;
3. whether the relevant bytes and scientific inputs are unchanged;
4. whether population/support/TQB/model/runtime/authority context changed;
5. what new failure mode is not already covered.

If the relevant bytes and authority context are unchanged, reuse the historical audit. Requalification is justified only for changed inputs/interfaces/authority context or a concrete newly discovered defect.

## Data and result custody

Small/public machine-readable data, scripts, fixtures and results needed for reproducibility should be committed when lawful and appropriate.

Large, private, controlled, or local-only assets must not be duplicated into public Git merely for convenience. Preserve them through exact artifact identity, SHA-256, byte size, source/path custody, acquisition/provenance record and the execution environment that holds them.

Protected candidate outcomes, `reader_validation`, and `reader_oracle` must not be opened merely to improve documentation or custody.

## Scientific separation laws

Always preserve:
- mechanics evidence != biological evidence;
- synthetic known truth != human biological truth;
- measured zero != unsupported;
- unsupported != unresolved;
- validation/oracle cannot rescue fit estimability;
- source failure cannot average away;
- support cannot be manufactured;
- address parity != evidence parity;
- stable subspace != stable individual axes;
- data exposure/history must be recorded rather than silently relabelled as pristine validation.

## Current immediate state

Task 0 repair after Macha findings B1–B5 is PR #384.

Exact repaired candidate currently under independent re-check:
`db92f80d128c37b99aa7d2c169eaf44447fa2164`

Controller exact-head evidence on that repaired state:
- B1–B5 repair verification: GREEN;
- original Task 0 migration audit: GREEN;
- inherited unified synthetic integration: GREEN.

This does not independently accept Task 0. Macha must re-check B1–B5 on the exact repaired head.

Unified Task 1 remains blocked until Task 0 is independently accepted and frozen.

Old synthetic Tasks 1–2 remain reusable substrate at:
`ff597faf2182522a320ec5322f8db9b67c9c6094`

Their reuse must be by adaptation/wrapping into the merged workflow, never by silently treating the old tasks as completed unified tasks.

## Successor rule

A future agent starts from the latest PR #322/#323 read-first surfaces, exact live heads and machine ledgers. It should not perform project archaeology from scratch unless the durable custody itself is demonstrably incomplete or contradictory.
