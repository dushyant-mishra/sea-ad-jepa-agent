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

The remaining Task 3 workflows used for this gate are verification-only. The RED CI job reported `GITHUB_TOKEN` permission `Contents: read`.

## Preserved RED baseline

PR #392 was reopened only to trigger read-only `pull_request` verification after GitHub App-authored content commits did not auto-start Actions.

- exact branch head under test content: `51cdd4bea030be17242de7f81e9880dec802c6a7`
- GitHub pull-request merge ref: `d4e8fc991ded83d906369f02e530887865654877`
- workflow: `Unified Task 3 registry`
- run ID: `38792404844` (run #115)
- job ID: `116620027363`
- command: `python -m pytest -q tests/v5/td_unified/test_registry_v1*.py`
- result: `11 failed, 53 passed in 0.39s`
- full unified step: skipped because the focused RED gate failed first, as intended

The eleven failures were the expected defect classes, not import/collection defects:

- B1 / H1: UNIT scope advanced beyond `HUMAN_EXECUTED` without refusal.
- B2 / H2: `SAME_CODE_PATH -> KNOWN_TRUTH_QUALIFIED` succeeded without the required closed evidence/reviewer gate.
- B3: all five hostile controller identity variants were accepted: trailing whitespace, leading whitespace, case alias, fullwidth-colon alias, and a newly self-minted controller id.
- B4 / H4: a warmed positive caller cache survived replacement with an empty dependency resolver.
- B4 / H3: a caller-poisoned cache authenticated otherwise missing dependencies.
- B5 / H6: deleting revocation history and restoring the unit to `ACTIVE` allowed re-promotion.
- B5 / H5: a fabricated `REAL_REFERENCE_READY` pre-state/receipt enabled `HUMAN_EXECUTABLE`.

Two existing exact-equality actor-independence checks remained green: reviewer actor equal to controller and reviewer actor equal to producer are already refused. Those passing controls must remain passing during repair.

## Binding next repair order

1. Preserve this RED evidence and keep B6 disarmed.
2. Repair B1 by enforcing frozen Task 1 authority validation on every promotion and retaining `NO_TRAINING_AUTHORITY` as a hard restriction.
3. Repair B2 with a closed per-stage evidence-gate table; undefined evidence types fail closed. `KNOWN_TRUTH_QUALIFIED` and `HUMAN_EXECUTED` cannot be promoted merely because the caller asks.
4. Repair B3 with a frozen identity-bound actor registry, strict canonical ASCII actor IDs, role grants, and registry-based independence checks. Free-string normalization alone is insufficient because self-minted identities must also fail.
5. Repair B4 by using only internal per-call or resolver-context-bound memoization. Caller-provided cache entries are never authority.
6. Repair B5 by replay-validating promotion/revocation history from an authenticated genesis and requiring an external current-head anchor; internal receipt consistency alone is insufficient.
7. Remove the dead `asserted_ready` and `prerequisite_evidence_verifier` parameters.
8. Run focused and complete inherited regressions on one exact candidate head.
9. Obtain a focused independent Macha B1-B6 recheck before any Task 3 freeze.

## Authority boundary

This RED baseline grants no new authority. Task 4 implementation remains blocked. No protected biological, candidate, validation, holdout, or oracle values were opened for this work. No Task 0-2 frozen source was modified.
