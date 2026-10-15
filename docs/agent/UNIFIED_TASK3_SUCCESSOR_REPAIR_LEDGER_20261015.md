# Unified Task 3 successor repair ledger — 2026-10-15

Status: `TASK3_REJECTED_OPEN_REPAIR_REQUIRED`

This ledger records successor custody after the independent Macha rejection of Unified Task 3. It is not an acceptance, freeze, training authorization, target decision, representation decision, or Task 4 authorization.

## Read-first authority

- durable lane audit: PR #322 at `31e33f57f1e456e28f93250493d45da5ee4ffa7a`
- frozen Task 0: `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`
- frozen Task 1: `799d2e235901dfad9ce3b305c767a1c989e362f6`
- frozen Task 2: `c7dfff1cee608e4a101855d42cf0af08491c2aaf`
- rejected Task 3 candidate: `851544e8dc2a3881193a4d5bbcf07933e1d61149`
- independent Macha review head: `869ca777a498181c519ccfc04b8bf5db0f2888c7`
- binding verdict: `REJECT_UNIFIED_TASK3` / `TASK3_REMAINS_OPEN__UNIFIED_TASK4_REMAINS_BLOCKED`
- global authority: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Successor custody actions

T3-B6 was contained before any production repair, exactly as ordered by the independent review.

1. Deleted `.github/workflows/task3-red6-actor-repair.yml` at commit `229317559f69929a72678ceebc1bdd43a0b62f65`.
2. Deleted `.github/workflows/apply-task3-cycle4-hardening.yml` at commit `6d6a0a315575ba61320b3fb7cac767d467219a49`.
3. Verified both paths absent at the branch head after deletion.
4. Wrote the successor rejection-preservation plan at `docs/superpowers/plans/2026-10-15-unified-task3-rejection-preservation.md`, commit `88922bb5650d148b6f9e2c9a1c85fdce0ffdc570`.
5. Imported Macha H1-H6 and the actor-alias/self-mint attacks into `tests/v5/td_unified/test_registry_v1_macha_rejection.py`, commit `51cdd4bea030be17242de7f81e9880dec802c6a7`.
6. Decoupled H1 from the B2 evidence gate so each blocker remains independently observable, commit `1fa6960f194e51acc02784b67116bd38ede073b6`.

The remaining Task 3 workflows used for these gates are verification-only. The RED and partial-GREEN CI jobs reported `GITHUB_TOKEN` permission `Contents: read`.

## Preserved RED baseline

PR #392 was reopened only to trigger read-only `pull_request` verification after GitHub App-authored content commits did not auto-start Actions.

- corrected RED test head: `1fa6960f194e51acc02784b67116bd38ede073b6`
- workflow: `Unified Task 3 registry`
- run ID: `38792956739` (run #120)
- job ID: `116621940528`
- command: `python -m pytest -q tests/v5/td_unified/test_registry_v1*.py`
- result: `11 failed, 53 passed`

The eleven failures were the expected defect classes, not import/collection defects:

- B1 / H1: UNIT scope advanced beyond `HUMAN_EXECUTED` without refusal.
- B2 / H2: `SAME_CODE_PATH -> KNOWN_TRUTH_QUALIFIED` succeeded without the required closed evidence/reviewer gate.
- B3: all five hostile controller identity variants were accepted: trailing whitespace, leading whitespace, case alias, fullwidth-colon alias, and a newly self-minted controller id.
- B4 / H4: a warmed positive caller cache survived replacement with an empty dependency resolver.
- B4 / H3: a caller-poisoned cache authenticated otherwise missing dependencies.
- B5 / H6: deleting revocation history and restoring the unit to `ACTIVE` allowed re-promotion.
- B5 / H5: a fabricated `REAL_REFERENCE_READY` pre-state/receipt enabled `HUMAN_EXECUTABLE`.

Two existing exact-equality actor-independence checks remained green: reviewer actor equal to controller and reviewer actor equal to producer are already refused. Those passing controls must remain passing during repair.

## B1 + B4 repair batch

The first production repair batch was intentionally limited to T3-B1 and T3-B4. The implementation plan is `docs/superpowers/plans/2026-10-15-unified-task3-b1-b4-repair.md`.

Production repair commit: `425460c7582eed985893483cdc2d8bfbb389b2bd`.

### T3-B1 mechanical closure

Every proposed promotion now constructs a frozen Task 1 `AuthorityRecord` and calls `validate_authority_record` before the stage is changed. `NO_TRAINING_AUTHORITY` also has an explicit hard refusal at `TRAINING_ELIGIBLE` / `TRAINING_AUTHORIZED`. This makes the frozen UNIT-scope ceiling executable at the Task 3 promotion boundary rather than merely documentary.

### T3-B4 mechanical closure

Readiness/dependency memoization is now owned by the top-level call. The legacy caller `verification_cache` parameter is temporarily retained for API compatibility but is neither seeded into nor written back from the authentication context. A fresh internal cache is used for recursive readiness checks, and HUMAN_EXECUTABLE dependency authentication also uses a fresh call-owned cache.

### Exact-head partial-GREEN evidence

On exact production-repair head `425460c7582eed985893483cdc2d8bfbb389b2bd`:

- `Unified Task 3 registry` run `38793456626`, job `116623672455`
- focused result: `8 failed, 56 passed`
- B1/H1: PASS
- B4/H3 caller-poisoned cache: PASS
- B4/H4 warmed-cache/resolver-swap: PASS
- remaining failures: B2/H2, five B3 alias/self-minted identity attacks, B5/H5, B5/H6 only

The frozen Task 2-specific workflow on the same PR did not show a Task 2 regression:

- run `38793456638`, job `116623672911`
- dedicated Task 2 manifest/access suite: `31 passed in 0.27s`
- its broader command `python -m pytest -q tests/v5/td_unified` then inherited the eight intentionally unresolved Task 3 hostile RED tests and reported `159 passed, 8 failed in 0.73s`
- those eight failures are exactly B2, five B3 identity attacks, H5 and H6

Therefore B1 and B4 are mechanically closed on this candidate head, but Task 3 remains rejected because B2, B3 and B5 are open and no independent exact-head Macha recheck has accepted the successor.

## B2 stage-evidence repair batch

The B2 repair was deliberately implemented as a fail-closed custody rule, not by manufacturing evidence inside Task 3.

- implementation plan: `docs/superpowers/plans/2026-10-15-unified-task3-b2-stage-evidence-repair.md`, commit `1b6081ca58996f6cec09b5d95cbe474094b47f5d`
- added the missing `HUMAN_EXECUTABLE -> HUMAN_EXECUTED` hostile test at `tests/v5/td_unified/test_registry_v1_macha_b2_human_executed.py`, commit `ea3565173d9557c44098aba5f6bce36df3947a48`
- pre-repair read-only RED proof: `Unified Task 3 registry` run `38793994245`, job `116625508611`, result `9 failed, 56 passed`
- production repair commit: `1f466fd5c00535e250fd3a8eb46032e9a810fddd`

### T3-B2 mechanical closure

`registry_v1.py` now uses a closed destination-stage evidence policy. Mechanical stages are explicitly identified; `REAL_REFERENCE_READY` and `HUMAN_EXECUTABLE` continue through their already implemented gates; `KNOWN_TRUTH_QUALIFIED` requires an independent reviewer plus `SEALED_CHALLENGE_REVIEW`, which Task 3 does not implement, so it fails closed; `HUMAN_EXECUTED` requires an authenticated `HUMAN_EXECUTION_RECEIPT`, which Task 3 does not implement, so it fails closed. An unmapped or unknown destination-stage evidence policy also fails closed.

No sealed-challenge result, reviewer result, or human-execution result was fabricated to obtain GREEN. The repair records the absence of those evidence types as a binding refusal.

### Exact-head B2 partial-GREEN evidence

On exact production-repair head `1f466fd5c00535e250fd3a8eb46032e9a810fddd`:

- `Unified Task 3 registry` run `38794460817`, job `116627088995`
- focused result: `7 failed, 58 passed`
- B1/H1: PASS
- B2/H2 known-truth evidence-free promotion: PASS (refused)
- B2/H2 human-executed evidence-free promotion: PASS (refused)
- B4/H3 and H4 cache attacks: PASS
- remaining failures: five B3 actor alias/self-minted identity attacks plus B5/H5 and B5/H6 only
- token authority remained `Contents: read`

Frozen Task 2 remained mechanically intact on the same candidate:

- run `38794461107`, job `116627090736`
- dedicated Task 2 manifest/access suite: `31 passed in 0.23s`
- broader unified regression folder: `161 passed, 7 failed in 0.71s`
- all seven broader failures are the intentionally unresolved Task 3 B3/B5 hostile tests
- token authority remained `Contents: read`

Therefore B2 is mechanically closed on `1f466fd5...` without increasing scientific authority. Task 3 remains rejected because B3 and B5 are open and no independent exact-head Macha recheck has accepted the successor.

## Binding next repair order

1. Keep B6 disarmed and preserve the RED baseline.
2. B1: mechanically closed on `425460c...`; retain frozen Task 1 authority validation on every promotion and `NO_TRAINING_AUTHORITY` as a hard restriction.
3. B2: mechanically closed on `1f466fd5...`; keep unavailable or undefined stage evidence fail-closed and do not manufacture evidence inside Task 3.
4. Repair B3 with a frozen identity-bound actor registry, strict canonical ASCII actor IDs, role grants, and registry-based independence checks. Free-string normalization alone is insufficient because self-minted identities must also fail.
5. B4: mechanically closed on `425460c...`; caller cache entries remain non-authoritative.
6. Repair B5 by replay-validating promotion/revocation history from an authenticated genesis and requiring an external current-head anchor; internal receipt consistency alone is insufficient.
7. Remove the dead `asserted_ready` and `prerequisite_evidence_verifier` parameters after B1-B5 are closed.
8. Run focused and complete inherited regressions on one exact candidate head.
9. Obtain a focused independent Macha B1-B6 recheck before any Task 3 freeze.

## Authority boundary

These partial-GREEN repairs grant no new authority. Task 3 remains `REJECTED_OPEN_REPAIR_REQUIRED`. Task 4 implementation remains blocked. No protected biological, candidate, validation, holdout, or oracle values were opened for this work. No Task 0-2 frozen source was modified. The global authority remains `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
