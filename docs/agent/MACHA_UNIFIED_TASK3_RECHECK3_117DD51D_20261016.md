# Macha focused re-check 3 — Unified Task 3 at `117dd51d`

Date: 2026-10-16.

Role: independent hostile reviewer of controller work. Non-controlling.

Scope, as set at `d9e58a18`: N2 (no-custody promotion), nested B3-V, the four B5-F variants and the every-revocation rule, with regression checks on everything closed earlier.

No real, protected, biological, candidate, validation or oracle bytes were opened. The probe uses the synthetic reader split from the Task 2 tests, with `FROZEN_READER_SPLIT_SHA256` monkeypatched exactly as those tests do.

## Verdict

`ACCEPT_UNIFIED_TASK3`

`TASK3_MAY_BE_FROZEN__UNIFIED_TASK4_MAY_BEGIN_PROSPECTIVELY`

Every item in scope is closed, and every earlier closure still holds. The registry's authority stages all fail closed:
- `KNOWN_TRUTH_QUALIFIED` needs a `SEALED_CHALLENGE_REVIEW` receipt, which does not exist yet.
- Genesis is capped at `SAME_CODE_PATH`.
- `REAL_REFERENCE_READY` and later need matching history custody.

The two BAD rows below are repair-targeted attacks on the revocation key. They reach only mechanical stages, which carry no authority. They become **binding preconditions** on whichever task first makes `KNOWN_TRUTH_QUALIFIED` reachable (C1).

This acceptance grants no target, representation, Stage 4, protected-value, human-execution or training authority.

## Head

| item | value |
|---|---|
| reviewed code | `117dd51dea827e734b299982da93991b934bdc8f` (pinned `candidate/unified-task3-recheck3-green-117dd51d-20261015`) |
| PR #401 head | `2448cbce`, which adds only `…RECHECK3_REPAIR_LEDGER_20261015.md` |
| delta from `d9e58a18` | 6 human-authored commits. Code changes are in `registry_v1.py` only. New files: `tests/v5/td_unified/conftest.py` (test isolation that resets the anchor for each test) and two recheck-3 test files. No earlier test file changed. |
| unchanged | frozen Task 0–2 code, `registry_v1_legacy.py`, `actor_registry_v1.py`. `unified-task3-registry.yml` is blob `8e95a828…`, identical to the copy reviewed at `d9e58a18`, `contents: read`. |
| RED-first | at `a1a42db3`, `test_registry_v1_macha_recheck3.py` has **7 failed**, exactly the 7 paths that were BAD at `d9e58a18` (verified locally) |
| tests, CI | **CI-confirmed** on head `117dd51d`: run 38843717395 (Unified Task 3 registry), 38843717378 (Task 2 manifest access) and 38843717386 (unified synthetic integration), all `success` |
| tests, local | 191 passed (full `tests/v5/td_unified`), 88 passed (`test_registry_v1*`). Run locally, not CI, through the wrapper that pins the repo's `tests` package. |

## Probe

`docs/agent/macha_task3_review_evidence_851544e8/task3_recheck3_probe.py` and its `.log`.

28 checks: **26 behaved as expected, 2 were BAD**, plus 6 NOTE rows.

## Items in scope — all CLOSED

| item | attack | result |
|---|---|---|
| N2 | declared `KNOWN_TRUTH_QUALIFIED`, Task-2-valid manifest, no custody → `REAL_REFERENCE_READY` | refused: "requires external history custody anchor" |
| N2 | the same registry as a custody genesis | refused (genesis cap) |
| N2 | lawful custody at `SAME_CODE_PATH` → `KNOWN_TRUTH_QUALIFIED` | refused (`SEALED_CHALLENGE_REVIEW` not implemented); this is the only route to `REAL_REFERENCE_READY`, so it is closed |
| N2 | declared `REAL_REFERENCE_READY`, no custody → `HUMAN_EXECUTABLE` | refused |
| B3-V nested | unregistered validator `producer:G8` at depth 2 and depth 3 | refused by both the actor gate and `promote_unit` (closure walk `_gate_prerequisite_closure`) |
| B5-F | the PR's exact fresh-custody attack | refused at genesis |
| B5-F | fork: custody B created before the revocation | refused at promotion |
| B5-F | no custody | refused at promotion |
| B5-F | stage shift | refused at genesis; the key now excludes stage and lineage status |
| B5-F | combined with N2: revoked identity declared `KNOWN_TRUTH_QUALIFIED` → `REAL_REFERENCE_READY` | refused |
| every revocation | low-stage revocation with no custody, then promotion or a fresh genesis | both refused |
| every revocation | supersession, then promotion of the superseded unit | refused |

## Regression — still CLOSED

| item | result |
|---|---|
| N1 | the PR fixture manifest is refused. The frozen Task 2 binding refuses a missing raw resolver and passes the valid world (positive control). |
| B3-E / B3-R | minted controller, reviewer and issuer are refused by `FROZEN_PRIVILEGED_ACTOR_IDS` |
| B1 | facade and legacy both enforce the Task 1 law and `NO_TRAINING_AUTHORITY` |
| B4 | a poisoned cache with an empty resolver gives not ready |
| B6 | 55 workflows: none can write, commit or push |

## BAD rows — non-blocking, binding as C1

1. A revoked identity re-enters, under a fresh custody, at `FIXTURE_SAME_INTERFACE` when it adds one cosmetic `authority_restrictions` token (`COSMETIC_V2`). Every code, policy, actor and manifest identity field is unchanged.
2. The same happens when it only **reorders** those tokens.

**Cause.** `_revocation_identity` hashes the whole unit payload minus stage and lineage, so `authority_restrictions` (order-sensitive, open uppercase vocabulary) is part of the key. My `d9e58a18` repair text named the fields for the key and did not include restrictions.

**Why it does not block.** No authority stage can be reached. Mechanical stages carry no evidence policy, and the same code can enter them anyway as a new unit.

## Binding carry-forward

**C1 — precondition before any stage at `KNOWN_TRUTH_QUALIFIED` or later becomes reachable (Task 4 or later). All four parts are required:**
- (a) Key revocations by the defect-bearing execution identity: `unit_id`, manifest, access policy, the Task 2 execution-identity row, actor identities, population and claim fields. Exclude `authority_restrictions` and `authority_scope`, or use their canonical sorted closed-vocabulary form.
- (b) Check the anchor for every unit in the prerequisite closure, not only the promoted unit. A NOTE row shows that a prerequisite target revoked in custody A stays `ACTIVE` in a forked custody B; this is latent today.
- (c) Make revocation and history custody persist across processes, outside the producer process (R4).
- (d) Add these two BAD rows and the target-fork NOTE as failing tests first.

**C2 — R4 OPEN.** The process-local anchor is a labelled stopgap: a second process, or `_PROCESS_REVOCATION_ANCHOR.clear()`, erases it (NOTE rows).

**C3.** Downstream consumers of Task 3 authority must use the `registry_v1` facade, must require `RegistryHistoryCustody.validate_current`, and must not import `registry_v1_legacy`. `legacy.promote_unit` still reaches `REAL_REFERENCE_READY` without custody (NOTE). Add an import-guard test in Task 4.

**C4.** `derive_real_reference_ready` is diagnostic only, not authority.

**C5 — R7.** Actor identities are public names, not credentials. The pinned privileged names (`C1`, `R1`, `validator-1`, `HARNESS`) are conventions. Human execution requires signed or harness-attested actor actions.

**C6.** Apply the frozen privileged-actor policy in `revoke_or_supersede`. A minted controller can revoke, which pollutes the anchor and blocks units but grants no authority.

**C7.** Close the vocabulary of requirement classes, and bind an issuer to every non-`UNIT` class.

**C8.** `RegistryUnit` construction should apply Task 1 `validate_authority_record`.

**C9 — R1.** In-process tampering with custody private state remains possible.

**R5** is preserved: pooled donor-level claims only; `PER_FOLD_SOURCE_STRATIFIED` stays blocked.

## Required-format answers

1. **Head:** `117dd51dea827e734b299982da93991b934bdc8f`.
2. **A2 (lineage/history):** PASS. One-stage steps; Task 1 law; stage-evidence gates fail closed; genesis cap; custody required for `REAL_REFERENCE_READY` and later; anchored revocation.
3. **A5 (actor independence):** PASS. Closed actor registry, frozen privileged names, and registered independent validators and issuers across the full closure (R7 carried).
4. **A6 (prerequisite graph):** PASS, including R6.
5. **Task 2 binding:** PASS. Frozen `validate_manifest` runs with the raw split at the authority boundary.
6. **R1–R6:**
   - R1: governance-level gate in place; in-process tampering carried as C9.
   - R2: PASS.
   - R3: PASS.
   - R4: OPEN (C1c, C2).
   - R5: PASS.
   - R6: PASS.
7. **Provenance:** PASS. Custody detects fabricated, deleted and forked history; revocation is anchored in-process, with C1 binding.
8. **Probes:** 28 checks, 26 as expected, 2 BAD (non-blocking, C1), 6 NOTE.
9. **Residual carry-forward:** C1–C9 above, plus R5.
10. **Freeze decision:** Task 3 may be frozen at code identity `117dd51dea827e734b299982da93991b934bdc8f`. The ledger commit `2448cbce` is docs-only. Unified Task 4 may begin prospectively, RED-first, carrying C1–C9. **C1 must be satisfied before Task 4 (or any later task) makes `KNOWN_TRUTH_QUALIFIED` or a later stage reachable.**

`TASK3_MAY_BE_FROZEN__UNIFIED_TASK4_MAY_BEGIN_PROSPECTIVELY`

Authority unchanged: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
