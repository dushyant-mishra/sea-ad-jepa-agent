# Unified Task 3 re-check 3 repair ledger — 2026-10-15

## Status

`TASK3_CANDIDATE_GREEN__INDEPENDENT_RECHECK_REQUIRED`

This ledger does **not** accept or freeze Task 3. Unified Task 4 remains blocked.

Global authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Authoritative rejected base

- Macha-reviewed rejected candidate: `d9e58a18da5bcfc95d9b9e7484e5686d403c55d4`
- Macha review branch head carrying re-check 2 artifacts: `e0e1b775`
- Verdict: `REJECT_UNIFIED_TASK3`
- Gate: `TASK3_REMAINS_OPEN__UNIFIED_TASK4_REMAINS_BLOCKED`

The re-check 2 scope left only N2, nested B3-V, and B5-F revocation variants open. Previously closed B1, B4, B6, Task 2 binding, evidence issuers, and pinned privileged actors were not reopened by this repair.

## RED-first preservation

RED commit:

`a1a42db3b55a17d2bc22070578a65816cea7213b`

Added `tests/v5/td_unified/test_registry_v1_macha_recheck3.py` covering:

1. N2 — `REAL_REFERENCE_READY` without matching custody.
2. Nested B3-V — nested content validator outside the registered/independent actor policy.
3. Nested B3-V through the promotion path.
4. B5-F — a second custody created before revocation.
5. B5-F — promotion after revocation with no custody.
6. B5-F — stage shifting to recreate a revoked execution identity.
7. B5-F + N2 — revoked identity declared `KNOWN_TRUTH_QUALIFIED` and then advanced toward `REAL_REFERENCE_READY`.

Trustworthy RED CI:

- workflow: `Unified Task 3 registry`
- run: `38843154046`
- job: `116787601832`
- result: focused Task 3 suite failed on the preserved hostile cases; full suite was skipped after focused failure.
- workflow permission surface remained read-only.

## Repair candidate

Pinned exact candidate branch:

`candidate/unified-task3-recheck3-green-117dd51d-20261015`

Exact candidate SHA:

`117dd51dea827e734b299982da93991b934bdc8f`

The moving repair PR is #401 on branch `repair/unified-task3-recheck3-20261015`. Reviewers must review the pinned candidate SHA above, not the moving documentation head.

## N2 repair

Every promotion to `REAL_REFERENCE_READY` or later now requires a matching `RegistryHistoryCustody` anchored to the exact pre-promotion registry state. A history-free registry can no longer declare `KNOWN_TRUTH_QUALIFIED` units and cross the real-reference authority boundary without custody.

The existing frozen Task 2 manifest/population validation is still rerun at the real-reference boundary.

## Nested B3-V repair

Prerequisite actor validation now walks the complete prerequisite closure traversed by the readiness gate, rather than filtering only prerequisites directly owned by the promoted unit.

For each traversed prerequisite, the repair checks the registered actor policy and validates content validators / evidence issuers against the producer and executor of that prerequisite's dependent unit. Nested producer-as-validator and unregistered-validator paths are therefore evaluated before promotion.

## B5-F revocation repair

A labelled process-local revocation anchor is added as a stopgap only. Its identity deliberately excludes:

- `qualification_stage`
- `active_lineage_status`

Therefore a revoked execution identity cannot be recreated merely by restarting one stage lower or by changing lineage status.

Every promotion checks that process-local revocation anchor before proceeding. Every revocation records the revoked execution identity in that anchor, including low-stage revocations that do not otherwise require custody.

`RegistryHistoryCustody` genesis also refuses identities already present in the process-local revocation anchor. This closes the within-process fork, no-custody, stage-shift, and revoked-identity-to-KTQ/RRR variants covered by the re-check.

### R4 remains OPEN

This process-local revocation anchor is explicitly **not** persistent cross-process custody and does not close R4. It is only the stopgap allowed by the Macha re-check 2 ruling. Cross-process revocation persistence remains a later hard requirement before any authority boundary that the independent review rules as dependent on R4.

No statement in this ledger upgrades the stopgap into durable custody.

## Test isolation

The synthetic pytest suite deliberately reuses identical fixture execution identities across independent tests. Because the stopgap is process-local by design, an autouse fixture clears only the test-process revocation anchor between pytest tests. It does not clear the anchor within a test, so fork/restart hostile cases retain the intended within-process semantics.

This is test isolation, not a production escape hatch.

## Additional every-revocation regression

`tests/v5/td_unified/test_registry_v1_macha_recheck3_revocation_record.py` proves that a low-stage revocation performed without a custody object is nevertheless entered into the process-local anchor and prevents a fresh custody from starting over the original execution identity within that process.

## Exact candidate CI evidence

For exact SHA `117dd51dea827e734b299982da93991b934bdc8f`:

- `Unified Task 3 registry`
  - run `38843717395`
  - job `116789358076`
  - focused Task 3 registry + hostile self-audit: PASS
  - full unified Task 0–3 regression: PASS
- `TD unified Task 2 manifest access`
  - run `38843717378`
  - job `116789357776`
  - Task 2 manifest/access suite: PASS
  - whole unified Task 0–2 regression folder: PASS
- `unified synthetic integration v1`
  - run `38843717386`
  - job `116789358039`
  - PASS

B6 was already closed by the independent re-check. The exact candidate does not alter the Task 3 registry workflow relative to rejected head `d9e58a18...`: the workflow blob SHA is `8e95a8286bfef8560579ab1197b5ab67cb6ee8c4` at both heads, and its repository permission remains `contents: read`.

## Diff audit from rejected base

`d9e58a18da5bcfc95d9b9e7484e5686d403c55d4` → `117dd51dea827e734b299982da93991b934bdc8f` is six commits ahead and changes only:

- `scripts/v5/td_unified/registry_v1.py`
- `tests/v5/td_unified/conftest.py`
- `tests/v5/td_unified/test_registry_v1_macha_recheck3.py`
- `tests/v5/td_unified/test_registry_v1_macha_recheck3_revocation_record.py`

Frozen Task 0–2 production code, `registry_v1_legacy.py`, and the Task 3 registry workflow are unchanged in the net diff.

## Carry-forward items not claimed closed

The following remain explicit carry-forward items and are not silently promoted to resolved status:

- R4: revocation/custody persistence across processes.
- R7: actor identities remain names/objects rather than cryptographic proof of who acted.
- `derive_real_reference_ready` remains diagnostic and must never itself count as authority.
- `registry_v1_legacy.promote_unit` remains a public legacy path and must not become an authority path.
- Frozen actor policy should be applied to revocation authority as part of the remaining hardening.
- Requirement classes should ultimately be closed/enumerated rather than leaving issuer semantics open-ended.

## Required independent re-check

Macha/Claude should inspect exact SHA `117dd51dea827e734b299982da93991b934bdc8f` and focus on the re-check 2 residuals rather than restarting the entire project audit:

1. N2: can any unit cross into `REAL_REFERENCE_READY` or later without matching custody?
2. B3-V: can a nested prerequisite traversed by readiness evade registered and independent validator / issuer checks?
3. B5-F fork: can a custody created before a revocation later advance the revoked execution identity?
4. B5-F no-custody: can dropping custody/history regain promotion eligibility?
5. B5-F stage shift: can changing qualification stage or lineage status recreate a revoked execution identity?
6. B5-F combined path: can a revoked execution identity be redeclared at `KNOWN_TRUTH_QUALIFIED` and then reach `REAL_REFERENCE_READY`?
7. Every-revocation rule: does every revocation hit the stopgap anchor for the lifetime of the qualification process?

Any newly discovered equivalent authority/custody bypass should still be reported, but acceptance must not be inferred from internal GREEN CI alone.

## Freeze decision

No freeze yet.

`TASK3_CANDIDATE_GREEN__INDEPENDENT_RECHECK_REQUIRED`

`TASK3_REMAINS_OPEN__UNIFIED_TASK4_REMAINS_BLOCKED`
