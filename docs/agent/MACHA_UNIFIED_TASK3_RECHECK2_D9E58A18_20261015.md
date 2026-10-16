# Macha focused re-check 2 — Unified Task 3 at `d9e58a18`

**Date:** 2026-10-15.
**Role:** independent hostile reviewer of controller work; non-controlling.
**Scope:** the six items open at `68df3158` (N1, N2, B3-V, B3-E, B3-R, B5-F), plus regression checks of B1, B4 and B6.

No real, protected, biological, candidate, validation or oracle bytes were opened. The Task-2-valid world in the probe uses the synthetic 104/22/23 reader split from Task 2's own tests, with `FROZEN_READER_SPLIT_SHA256` monkeypatched exactly as those tests do.

## Verdict

`REJECT_UNIFIED_TASK3`

`TASK3_REMAINS_OPEN__UNIFIED_TASK4_REMAINS_BLOCKED`

**Closed:** N1, B3-E, B3-R, and regression B1/B4/B6.

**Still open:**
- **N2.** It is closed for history custody only. A history-free registry with no custody can still declare `KNOWN_TRUTH_QUALIFIED` and reach `REAL_REFERENCE_READY`.
- **B5-F.** The revocation anchor is keyed by an identity that includes the stage, and it is consulted only when a custody genesis is created.
- **B3-V.** The fix holds for direct prerequisites only, not for nested ones.

Together these let a unit **revoked by defect reach `REAL_REFERENCE_READY`** when it is checked against a Task-2-valid manifest.

## Head

| item | value |
|---|---|
| reviewed | `d9e58a18da5bcfc95d9b9e7484e5686d403c55d4`, pinned as `candidate/unified-task3-recheck2-green-d9e58a18-20261015` and as the PR #399 head |
| delta from `68df3158` | 15 human-authored commits. `registry_v1.py` is the facade; `task3_trust_roots_v1.py` is new. The legacy module and `actor_registry_v1.py` are unchanged. |
| frozen Task 0–2 code | unchanged |
| local tests | 183 passed (full), 80 passed (`test_registry_v1*`), 39 passed (Task 2 manifest suites). Run locally, not in CI, through the same wrapper as before, which pins the repo's `tests` package and changes no repo file. |
| preserved-test migration | H5 and H6 now run below `KNOWN_TRUTH_QUALIFIED`, because declaring that stage at genesis is refused. The tested properties are preserved: custody detects a fabricated receipt and a deleted revocation. Accepted. |

## Probe

`docs/agent/macha_task3_review_evidence_851544e8/task3_recheck2_probe.py` and its `.log`.

25 checks: **18 behaved as expected, 7 were BAD**, plus 7 NOTE rows.

Positive control: frozen Task 2 `validate_manifest` accepts the probe's world manifest.

## Per-item status

### N1 — CLOSED

At `REAL_REFERENCE_READY` / `HUMAN_EXECUTABLE`, `promote_unit` now re-runs frozen Task 2 `validate_manifest(raw_resolver=…)` and requires the manifest's access policy to equal the unit's. All three probes are refused:
- the PR fixture manifest, which is not Task-2-valid;
- a valid manifest supplied with no raw resolver;
- altered split bytes.

**NOTE.** `derive_real_reference_ready` still returns `ready=True` on the non-Task-2 fixture. Its docstring calls it diagnostic. Carry-forward: no consumer may treat it as authority; rename it or add the Task 2 check.

### N2 — PARTIAL (blocking, CRITICAL)

What works: custody genesis now refuses any declaration of `KNOWN_TRUTH_QUALIFIED` or later, so `HUMAN_EXECUTABLE` is unreachable.

**Attack.** `promote_unit` requires custody only for `HUMAN_EXECUTABLE`, or when the registry already carries history. I built a history-free registry that declares G8 and REF at `KNOWN_TRUTH_QUALIFIED`, with no `SEALED_CHALLENGE_REVIEW` evidence, against a Task-2-valid manifest. It was promoted to **`REAL_REFERENCE_READY`** with no custody at all.

`REAL_REFERENCE_READY` is the stage at which this head enforces real-reference authority. The declared-stage path is therefore still open for it.

**Smallest repair.**
- Require matching history custody for every promotion whose destination is `REAL_REFERENCE_READY` or later. Equivalently, require that the unit's current stage, and the stage of every prerequisite target, is recorded in the presented custody.
- Because genesis is capped at `SAME_CODE_PATH` and promotion to `KNOWN_TRUTH_QUALIFIED` fails closed, `REAL_REFERENCE_READY` then fails closed until Task 4/5.

### B3-V — PARTIAL (blocking, IMPORTANT)

What works: a validator on a direct prerequisite that is not registered, or that is `producer:G8`, is refused.

**Attack.** `_require_registered_prerequisite_actors` checks only prerequisites whose `dependent_unit_id` is the promoted unit. Legacy readiness also evaluates nested prerequisites (`_evaluate_unit` recursion), but it checks their content receipts by role only. I gave REF's own `REAL_REFERENCE_READY` prerequisite P2 a receipt from an unregistered validator with `actor_id producer:G8`. That passes the gate, and G8 is promoted to **`REAL_REFERENCE_READY`**.

**Smallest repair.** Apply the registered-actor and independence check to every prerequisite in the closure that readiness traverses for the gate, or to every prerequisite in the registry for that gate.

### B3-E — CLOSED

`PROCESS_ISOLATION` / `CROSS_PROCESS_LEDGER_CUSTODY` evidence is refused in each of these cases:
- no `issuer_identity_sha`;
- the issuer is `producer:G8`, even when registered;
- the issuer is unregistered;
- the issuer is minted and registered by the producer (refused by the frozen privileged-actor policy).

Positive control: `HARNESS` passes.

Non-blocking: requirement classes are open strings, and only these two classes are bound to an issuer. Close the set of classes, or bind every non-`UNIT` class.

### B3-R — CLOSED for the stated attack

A producer-authored registry with minted controller and reviewer names is refused by `FROZEN_PRIVILEGED_ACTOR_IDS`.

**NOTE (R7 class).** The policy pins actor *names*, not role-identity digests. A producer-made object named `C1` is accepted. This is equivalent to the already-carried R7 point: identities are public names, not credentials. The pinned names (`C1`, `R1`, `validator-1`, `HARNESS`) are labels by convention and should be recorded as such.

Also non-blocking: the frozen policy is not applied in `revoke_or_supersede`. A minted controller can file a revocation, which only blocks use (it grants no authority) and pollutes the anchor.

### B5-F — PARTIAL (blocking, IMPORTANT; the combined impact is CRITICAL)

What works: the PR's exact attack is refused. That attack is a fresh custody built from the same genesis after a revocation.

**Attacks.** `_PROCESS_REVOCATION_ANCHOR` is consulted only in `RegistryHistoryCustody.__init__`, and it is keyed by `unit.canonical_sha256()`, which includes `qualification_stage` and `active_lineage_status`.

| attack | result |
|---|---|
| **Fork:** custody B created before custody A's revocation | keeps promoting the revoked identity |
| **No custody:** history-free registry with the anchored identity | promoted (no anchor check) |
| **Stage shift:** revoke at `FIXTURE_SAME_INTERFACE`, restart genesis at `SEMANTICS_ONLY`, re-promote | genesis accepted; re-promotion recreates the **exact anchored identity** in custody B |
| **Combined with N2:** unit `REVOKED_BY_DEFECT` under custody, same execution identity then declared `KNOWN_TRUTH_QUALIFIED` | reaches **`REAL_REFERENCE_READY`** |

**Smallest repair.**
- Key the anchor by the unit's execution identity *excluding* stage and lineage status: `unit_id`, manifest, access policy, code/policy/actor/semantic identities, and population and claim fields.
- Consult the anchor in every `promote_unit` (with or without custody) and at genesis.
- Add an entry for every revocation, including revocations filed without custody.
- The lawful route back is `reidentify_unit`, which creates a new identity.

**Adjudication of the disclosed anchor-persistence question.** A process-wide anchor that does not persist across processes is acceptable as a labelled interim for freezing Task 3, under two conditions:
1. Once N2 is repaired, nothing above `SAME_CODE_PATH` is reachable in Task 3, so non-persistence can affect only mechanical stages.
2. Binding R4 carry-forward: no stage at `KNOWN_TRUTH_QUALIFIED` or later may become reachable (Task 4/5) until revocation and history custody persist across processes, outside the producer process.

Non-persistence does not close R4. The NOTE rows confirm that a second process, or a call to `_PROCESS_REVOCATION_ANCHOR.clear()` inside the process, erases the anchor. **The keying and consultation defects above are blocking regardless of persistence.**

### Regression — B1, B4, B6 remain CLOSED

| item | result |
|---|---|
| B1 | facade and legacy refuse `HUMAN_EXECUTED → DOWNSTREAM_CERTIFIED` (Task 1 law) and `TRAINING_ELIGIBLE → TRAINING_AUTHORIZED` (`NO_TRAINING_AUTHORITY`) |
| B4 | a poisoned cache with an empty resolver is refused at `REAL_REFERENCE_READY` |
| B6 | 55 workflows scanned: none has write, commit or push; `unified-task3-registry.yml` now declares `contents: read` |

## Required-format answers

1. **Head:** `d9e58a18da5bcfc95d9b9e7484e5686d403c55d4`.
2. **A2 (lineage/history):** B1 is closed. N2 is closed under custody and open without custody. B5-F is partial.
3. **A5 (actor independence):** B3-E and B3-R are closed (R7 is noted). B3-V is closed for direct prerequisites and open for nested ones.
4. **A6 (prerequisite graph):** the graph checks hold; B4/R6 are closed. The nested-actor gap is B3-V.
5. **Task 2 binding:** **PASS** on promotion (N1 closed). The diagnostic readiness function remains non-authoritative.
6. **R1–R6:**
   - R1: the issuer gate is in place (B3-E). In-process tampering remains R1 class.
   - R2: direct validator gate is in place; nested gap is B3-V.
   - R3: closed (N1).
   - R4: open as disclosed, and bound by the adjudication above.
   - R5: pass.
   - R6: closed.
7. **Provenance:** single-custody H5/H6 hold. Revocation durability across custodies, stages and paths without custody fails (B5-F).
8. **Probes:** 25 checks, 18 as expected, 7 BAD, plus 7 NOTE rows.
9. **Carry forward:**
   - R7: identities are names, not credentials; pinned names are labels by convention.
   - R4: persistent cross-process custody is required before any stage at `KNOWN_TRUTH_QUALIFIED` or later can be reached.
   - The diagnostic `derive_real_reference_ready` must not be treated as authority.
   - `registry_v1_legacy.promote_unit` is a public path that bypasses every new gate. Make its mutating functions private, or add a test that only `registry_v1` imports it.
   - Apply the frozen actor policy to revocation.
   - Close the set of requirement classes.
10. **Freeze decision:** Task 3 may not be frozen at `d9e58a18`. The next re-check covers only N2 (promotion without custody), B5-F (fork, no-custody, stage-shift, combined) and B3-V (nested). The probes above should become failing tests first.

`TASK3_REMAINS_OPEN__UNIFIED_TASK4_REMAINS_BLOCKED`

Authority unchanged: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
