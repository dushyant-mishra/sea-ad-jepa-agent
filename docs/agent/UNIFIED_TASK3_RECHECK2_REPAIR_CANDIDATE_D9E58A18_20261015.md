# Unified Task 3 second-recheck repair candidate — 2026-10-15

Status: `TASK3_REPAIR_CANDIDATE_GREEN__INDEPENDENT_RECHECK_REQUIRED`

This note records the successor repair after Macha's second rejection of Unified Task 3 at exact reviewed head:

`68df31584d17f91da2635cdf8e03bbe93695f9d1`

Second-review verdict:

`REJECT_UNIFIED_TASK3`

`TASK3_REMAINS_OPEN__UNIFIED_TASK4_REMAINS_BLOCKED`

Global authority remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Frozen authority unchanged

- Task 0: `e37a22b8059c0a4a93a789a8ca916fb7acde9fe3`
- Task 1: `799d2e235901dfad9ce3b305c767a1c989e362f6`
- Task 2: `c7dfff1cee608e4a101855d42cf0af08491c2aaf`

No frozen Task 0-2 production file was modified by this repair.

## Second-review blocker set

Closed before this repair and not reopened unless regressed:
- B1 authority scope/stage law
- B4 caller cache trust
- B6 self-mutating qualification CI

Focused open defects from the second Macha review:
- N1 CRITICAL — Task 3 did not re-run frozen Task 2 manifest/population validators.
- N2 CRITICAL — `KNOWN_TRUTH_QUALIFIED` could be declared at genesis without sealed-challenge evidence.
- B3-V IMPORTANT — content validator not registry-bound/independent.
- B3-E IMPORTANT — prerequisite evidence issuer not registry-bound.
- B3-R IMPORTANT — privileged actor registry authority unanchored.
- B5-F IMPORTANT — fresh custody could forget a prior revocation of the same unit identity.

## RED proof first

RED branch:
`red/unified-task3-recheck2-20261015`

Draft PR #398.

Exact RED commit:
`2db07505b7958d568ac4e22c77e7e4ebef19cbde`

CI:
- run `38820819233`
- job `116716702161`
- token permission: `Contents: read`
- focused result: **6 failed, 74 passed**

The six failures were the intended N1/N2/B3-V/B3-E/B3-R/B5-F repair targets.

## Exact repair candidate

Repair PR #399.

Exact candidate:
`d9e58a18da5bcfc95d9b9e7484e5686d403c55d4`

Pinned review branch:
`candidate/unified-task3-recheck2-green-d9e58a18-20261015`

Do not review a moving PR head in place of this exact SHA.

## Repair summary

### N1 — frozen Task 2 binding

`REAL_REFERENCE_READY` / `HUMAN_EXECUTABLE` promotion now re-runs frozen Task 2 `manifest_v1` validation rather than trusting the string `AUTHENTICATED_READER_SPLIT`. A real raw reader-split resolver is required for authority. Synthetic fixtures can still exercise diagnostic mechanics but cannot impersonate real reader population authority.

### N2 — no KTQ genesis declaration

`RegistryHistoryCustody` genesis is capped at `SAME_CODE_PATH`. `KNOWN_TRUTH_QUALIFIED` or later cannot be introduced as a convenient genesis snapshot; the sealed-challenge transition must occur inside anchored history.

### B3-V — validator identity

Content validators must resolve through the actor registry as `CONTENT_VALIDATOR` and must be independent of the scientific producer/executor.

### B3-E — evidence issuer identity

`PROCESS_ISOLATION` and `CROSS_PROCESS_LEDGER_CUSTODY` evidence require an `issuer_identity_sha` resolving as `PREREQUISITE_EVIDENCE_ISSUER`, independent of producer/executor.

### B3-R — privileged actor policy

Privileged qualification roles are constrained by the frozen Task 3 privileged-actor policy. Producer/executor remain unit-scoped; controller/reviewer/validator/evidence-issuer roles cannot be producer-minted substitutes.

### B5-F — same-process fresh-custody revocation reset

All `RegistryHistoryCustody` instances inside one qualification process consult a shared revocation anchor keyed by exact unit identity. A new custody object cannot restart the same unit identity after that identity was revoked in the same process.

**Important limitation:** this B5-F anchor is process-local and mutable process state. It is not cross-process persistence and does not close Task 2 residual R4. The focused independent reviewer must decide whether this closes the exact Task 3 B5-F blocker or whether B5-F itself already requires external/persistent anchoring. If rejected, externalize/pin the revocation anchor; do not add another in-memory workaround.

## Exact-head GREEN evidence

All evidence below is on candidate `d9e58a18...`.

### Unified Task 3 registry
- run `38822597023`
- job `116722460841`
- token: `Contents: read`
- focused `tests/v5/td_unified/test_registry_v1*.py`: **80 passed**
- full `tests/v5/td_unified`: **183 passed**

### Frozen Task 2 manifest/access regression
- run `38822597029`
- job `116722460745`
- token: `Contents: read`
- focused Task 2 manifest/access: **31 passed**
- full `tests/v5/td_unified`: **183 passed**

### Task 3 B6 workflow policy
- run `38822597077`
- job `116722480698`
- result: **PASS**

### Unified synthetic integration
- run `38822597115`
- job `116722461036`
- result: **PASS**
- pinned qualification runtime: PASS
- synthetic integration tests: PASS
- deterministic non-authorizing receipt fixture: PASS

## Diff boundary

Compared with rejected candidate `68df3158...`, the repair touches only:
1. `.github/workflows/unified-task3-registry.yml`
2. `scripts/v5/td_unified/registry_v1.py`
3. `scripts/v5/td_unified/task3_trust_roots_v1.py`
4. Task 3 registry tests under `tests/v5/td_unified/`

Frozen Task 0-2 production code is unchanged.

## Independent recheck required

Macha should review only exact SHA:

`d9e58a18da5bcfc95d9b9e7484e5686d403c55d4`

Focus only:
- N1
- N2
- B3-V
- B3-E
- B3-R
- B5-F

The reviewer should preserve/add hostile probes independently and must scrutinize the process-local nature of B5-F. Acceptance requires explicit per-blocker closure and no equivalent new authority/custody bypass.

Do not modify the candidate during review. If rejected, preserve RED evidence and identify exact blocker(s). If accepted, record the exact reviewed SHA before any freeze action.

## Gate

Task 3 remains open pending independent recheck.

Task 4 remains blocked.

This note grants no target, representation, protected-value, Stage 4, execution, or training authority.
