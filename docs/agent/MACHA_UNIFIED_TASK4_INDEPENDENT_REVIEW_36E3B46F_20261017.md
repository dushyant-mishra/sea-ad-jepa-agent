# Macha independent hostile review — Unified Task 4 custody candidate `36e3b46f` (PR #421)

Date: 2026-10-17.

Role: independent hostile reviewer of controller work. Non-controlling.

All probes are synthetic DEVELOPMENT fixtures. No protected, biological, real, candidate, validation or oracle bytes were opened. No probe mutates a module-private registry (`_LIFECYCLE_DIGESTS`, `_REGENERATION_EXECUTIONS`) or monkeypatches a module global. Every attack uses only the public types and public functions.

## Verdict

`REJECT_TASK4_CUSTODY_CANDIDATE`, for `36e3b46f1ca44465864a11872b459b5d108d6a67`.

**What works:**
- The PR #417 echo attack is refused.
- The PR #419 globals-substitution attack is refused (it is in the CI-green suite).
- Plain `replace()` token copies are refused.
- The genuine harness keeps FINAL closed, and the C1–C9 barrier fails closed even with a forged authoritative store.
- Task 3's `KNOWN_TRUTH_QUALIFIED` is still closed.
- Task 4 does not import the legacy registry.
- No Task 0–3 file is modified; the diff only adds files.

**What fails.** The lifecycle-provenance boundary and the FINAL fail-closed boundary both accept **subclasses** of the public types. Each override method returns lawful-looking values, and the module then trusts the caller-supplied fields. Through that route:
- DEVELOPMENT custody completes with fabricated outputs and no real exposures;
- a FINAL campaign runs all the way to hidden-material reveal;
- an output is frozen for a world that was never exposed;
- hidden material is revealed that differs from the commitment.

Separately, a campaign identity can be created again in the same process, which resets its exposure accounting.

Any acceptance would have covered only DEVELOPMENT/fail-closed custody mechanics; that claim is the part these attacks break.

## Head and evidence

| item | value |
|---|---|
| reviewed | `36e3b46f…` (PR #421 head; PR #418 head is the same SHA), base: frozen Task 3 `117dd51d` |
| delta | 111 commits, all human-authored. **Only new files** (`git diff --name-status` shows no M/D/R). |
| CI (confirmed on `36e3b46f`) | Task 4 `39083379145` success; Task 1 `39083379077`, Task 2 `39083379092`, Task 3 registry `39083379094` and synthetic `39083379087` all success. Task 0 migration `39083379080`, Task 0 B1–B5 `39083379098` and **Task 3 B6 policy `39083379103` failure** (see T4-B4). |
| local | 297 passed, 16 failed, 1 skipped on Windows / Python 3.9 (local, not CI). All 16 failures are `OSError: [Errno 9]` from the custody store's `os.fsync` on read-only handles (see T4-B5). |
| probe | `docs/agent/macha_task4_review_evidence_36e3b46f/task4_probe1.py` and its `.log`: 14 checks, **9 expected, 5 BAD**, plus 2 NOTE |

## Blocking findings

### T4-B1 — CRITICAL: subclass overrides defeat lifecycle provenance

**Locus.** `challenge_custody_v1.py`:
- `_assert_lifecycle_current` uses `isinstance` and `campaign.to_payload()`.
- Every transition reads `campaign.state` and the accounting fields from the caller's object.
- `_issued_exposure_is_exact` calls `exposure.identity_tuple()`, then uses `exposure.realization_id`.
- `_validate_bound_definition` calls `definition.to_payload()`, then uses `definition.hidden_spec_commitment`.
- Sealed sets are duck-typed (a `SimpleNamespace` copy is accepted; NOTE row).

**Attack A1.** Starting from a lawful campaign at `REALIZATION_SET_SEALED` with nothing exposed:
1. Define `ShadowCampaign(QualificationCampaign)` whose `to_payload()` returns that lawful payload.
2. Copy the fields, but set `state=ALL_REQUIRED_OUTPUTS_FROZEN` and fabricate the issued exposures, frozen outputs and terminal statuses.
3. Call `reveal_hidden_material`, then `verify_regeneration`, then `finalize_custody`.

Result: **`CUSTODY_COMPLETE`**, with a receipt saying `exposures_consumed=2` and an evidence package listing invented outputs. `issue_exposure` was never called.

This is the "fabricated advanced campaign lifecycle" class of attack (rejected predecessor `b5ed724c`). The token-copy test only tries `replace()`, which keeps the exact class, so it never tests this route.

**Attack A3.** `ShadowExposure.identity_tuple()` returns r0's issued tuple while `realization_id="r1"`. An output is frozen for r1, which was never exposed, and the hidden material is then revealed (`exposed=('r0',)`, frozen r0 and r1).

**Attack A4.** `ShadowDefinition.to_payload()` returns the committed payload while `hidden_spec_commitment` is set to a different spec. Reveal accepts the uncommitted hidden material. The plain-mismatch control is refused, which confirms this is the subclass route.

**Why validation is insufficient.** Frozen Task 1 law requires exact-type dispatch (Task 1 B1 was rejected for type confusion). Here the identity digest is computed by a method the attacker supplies, and the state the checks read comes from fields the attacker supplies.

**Smallest repair.**
- Require exact types (`type(x) is QualificationCampaign / ExposureRecord / SealedChallengeDefinition / SealedRealizationSet`) at every entry point.
- Compute digests with module-owned functions over `dataclasses.fields` of the exact type, never with instance methods.
- Better: keep the last lawful campaign object, issued `ExposureRecord`s, definition and sealed set inside the process-local registry, keyed by token. Treat the caller's object as a handle, so forged fields have no effect.
- Add A1, A3, A4 and the duck-typed set as RED tests.

### T4-B2 — CRITICAL: FINAL fail-closed bypass through a harness subclass

**Locus.** `_guard_final` checks `isinstance(authority_harness, Task4AuthorityHarness)` and then calls `authority_harness.current_status()`.

**Attack A2.** `ShadowHarness(Task4AuthorityHarness)` overrides `current_status()` to return `None`. It creates a FINAL campaign and drives it through:
1. `seal_definition`;
2. `seal_realization_set` with arbitrary rows;
3. both exposures and output freezes;
4. terminal accounting;
5. `reveal_hidden_material`.

Result: `namespace=FINAL`, `promotion_authority=CUSTODY_ONLY`, `state=HIDDEN_MATERIAL_REVEALED`. In the control, the genuine harness is refused (`Task4BarrierError`). `verify_regeneration` and `finalize_custody` still refuse FINAL, but the claim "FINAL transitions re-resolve current authority; caller-created GREEN status objects are never accepted" is false.

**Smallest repair.**
- Require `type(authority_harness) is Task4AuthorityHarness`.
- In `_guard_final`, call the module-level `evaluate_task4_preauthority_barrier(...)` and `require_task4_preauthority_barrier_green(...)` on the harness's fields, not the overridable method.
- Add an exact-type check for `Task4BarrierStatus` in `require_task4_preauthority_barrier_green`.
- Add A2 as a RED test.

### T4-B3 — IMPORTANT: a campaign identity can be created twice, resetting exposure accounting

**Locus.** `create_campaign` records no campaign identity it has already issued. Each call mints a fresh `_lifecycle_token` with zero exposures.

**Attack A5.**
1. Campaign A ("same-identity") exposes r0, freezes an output, and records `TECHNICAL_FAILURE`.
2. `create_campaign("same-identity", same dependencies)` returns B with the **same `campaign_identity` and the same `sealed_root`**.
3. B re-exposes both worlds to another method and reaches **`CUSTODY_COMPLETE`** with r0 `EVALUATED`.

The result is two custody receipts for one identity and one sealed exam, and A's exposed failed world is gone. This breaks the plan's requirements that a "failed world cannot be removed or replaced after exposure" and that "post-exposure repair requires [a] new qualification identity and new sealed set".

`test_fresh_ledger_restart_cannot_reuse_same_campaign_identity` only shows that a *different* genesis ledger gives a different identity; it never tests reusing the same identity. The test name claims a protection the code does not provide.

The NOTE row shows that a second process can also re-create the identity. That limitation is disclosed as process-local, and its fix belongs to R4.

**Smallest repair.**
- `create_campaign` refuses any `campaign_identity` it has already issued in this process. That covers the in-process case; the cross-process case needs the persistent custody store's `CAMPAIGN`/`EXPOSURE` events, which are not wired up yet and must be before FINAL.
- Rename or rewrite the misleading test, and add A5 as a RED test.

### T4-B4 — IMPORTANT (custody hygiene): three inherited CI gates permanently RED

`tests/v5/td_unified/conftest.py`, added in Task 3 at `8beef2bb`, imports `registry_v1`, and that import chain pulls in NumPy. The Task 0 migration, Task 0 B1–B5 and **Task 3 B6 workflow-policy** workflows install only pytest, so they have failed with `ModuleNotFoundError: numpy` on every run since `8beef2bb`. The B6 workflow history shows failure on every recorded head.

The B6 policy tests do still run, and pass, inside the full-suite workflows (Task 3 registry and Task 4), so no coverage was lost. But a permanently red dedicated safety gate that gets waved off as "known" is not acceptable custody.

**This was my miss.** When I accepted Task 3 at `117dd51d`, I verified only the three cited runs.

**Smallest repair.** Pin `numpy==1.26.4` in those three workflows, or import the registry lazily inside the conftest fixture. Either is infrastructure only and changes no production code.

### T4-B5 — IMPORTANT (portability and durability): custody store fails on the canonical Windows workspace

`PersistentCustodyStore` calls `os.fsync` on files it opened `"rb"` (lines 103–104 and 284–285). Windows raises `EBADF` for this (confirmed: `rb` fails, `ab` and `r+b` succeed), so 16 Task 4 store tests fail locally. AGENTS.md makes the Windows workspace canonical.

Also, `os.replace` of the head file is not followed by an fsync of the directory, so on POSIX the rename is not durable across a crash.

**Smallest repair.** Fsync through a writable handle, then fsync the parent directory on POSIX after `os.replace`. Add a Windows CI leg, or at minimum a portable test.

## Non-blocking / carry-forward

- `test_revoked_identity_target_fork_cannot_evade_anchor` tests the cosmetic-restriction case, not a target fork. Rename it. C1(b), anchor checks across the prerequisite closure, is still unimplemented. That is acceptable only while `KNOWN_TRUTH_QUALIFIED` is unreachable, which it is.
- C1(a) is present in design: `revocation_subject_identity` excludes `authority_restrictions`.
- C1(c)/R4: the store is a mechanism only. It never returns `authoritative=True`, and it is not wired to the campaign lifecycle.
- `task4_requirement_policy_v1.validate_requirement_evidence` takes issuer roles from a caller-supplied `actor_context` mapping (C5/R7 class). It is not wired into authority; when it is, it must use the frozen actor registry plus attested actions.
- The C1–C9 barrier correctly hard-codes C5–C9 as `FAIL`. Its only weakness is the harness bypass in T4-B2.

## Freeze decision

Task 4 may not be frozen at `36e3b46f`. Repair T4-B1 to T4-B5 RED-first, with A1–A5 and the duck-typed set as tests. A focused re-check of those items then suffices.

Authority unchanged: `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
