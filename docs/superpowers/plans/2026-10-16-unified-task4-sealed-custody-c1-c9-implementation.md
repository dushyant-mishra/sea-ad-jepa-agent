# Unified Task 4 Sealed Custody + C1–C9 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the prospective Unified Task 4 custody subsystem on exact frozen Task 3 `117dd51dea827e734b299982da93991b934bdc8f`, preserving sealed-exam lifecycle semantics while making C1–C9 machine-enforced prerequisites and keeping all biological/Stage4/training authority off.

**Architecture:** Task 4 is split into seven focused production modules: registry authority adapter, durable custody ledger, actor attestation, closed requirement-class policy, authority barrier, campaign/sealing state machine, and publication/secret-scan support. Authority-bearing operations consume frozen Task 3 through `registry_v1`, never `registry_v1_legacy`, and persistent custody is reloaded/replayed across process boundaries before any qualifying transition. The first executable branch is RED-only; fixture mechanics remain explicitly non-authorizing.

**Tech Stack:** Python 3.11; Python standard library (`dataclasses`, `enum`, `hashlib`, `json`, `pathlib`, `tempfile`, `subprocess`, `typing`); existing unified Task 0–3 modules; pytest 9.1.1; JSON Schema files already used under `schemas/target_discovery/unified_v1`; GitHub Actions with `permissions: contents: read`. No new cryptographic package is required by this plan: production signing is an external signer/verifier interface and fixture signing is non-authorizing.

**Spec:** `docs/superpowers/specs/2026-10-15-unified-task4-sealed-challenge-custody-design.md` plus binding amendment `docs/superpowers/specs/2026-10-16-unified-task4-c1-c9-binding-amendment.md`

## Global Constraints

- Implementation branch starts from exact frozen Task 3 `117dd51dea827e734b299982da93991b934bdc8f`; frozen Task 0–3 production code is not modified.
- Global authority remains `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED` throughout Task 4 implementation and review.
- No final challenge secrets, final hidden nonces, final realization roots, protected biological values, candidate outcomes, reader-validation values, reader-oracle values, or real qualification worlds are generated in RED or fixture execution.
- `KNOWN_TRUTH_QUALIFIED` and all later registry stages remain unreachable unless the C1–C9 barrier is current and GREEN; Task 4 itself does not promote a unit into those stages.
- R4 remains OPEN until durable cross-process ledger replay and external head verification pass hostile tests and independent review.
- R7 remains OPEN until authority-bearing actor actions use authenticated external/harness attestations rather than names alone.
- Task 4 and later production code must use `scripts/v5/td_unified/registry_v1.py`; `registry_v1_legacy` is historical-only.
- `derive_real_reference_ready` is diagnostic only and can never satisfy an authority prerequisite.
- Task 2/3 R5 remains pooled donor-level only; no per-fold source-stratified claim is authorized.
- Task 4 qualification CI is read-only: `permissions: contents: read`, no auto-edit/commit/push.
- Every repaired authority gate gets sibling-route attacks covering construction, reload, replay, fresh process, nested prerequisites, revocation/supersession, legacy import, campaign fork/restart, alias/config substitution, and stale diagnostics where applicable.

## Review Focus

- **Interrupted durable append:** a process crash between event persistence and head publication must leave a recoverable, non-authoritative state rather than silently accepting either head.
- **Equivalent-but-different serialization:** canonical identity checks must reject cosmetic restriction/scope changes as revocation bypasses while still distinguishing genuinely changed defect-bearing dependencies.
- **External signer spoofing:** a caller-created signer/verifier object or name must not satisfy authoritative actor/signer attestation.
- **Nested prerequisite mutation after campaign creation:** revoking/superseding a depth-N prerequisite must block the next authority-bearing transition even when campaign metadata is unchanged.
- **Publication leakage through failures:** hidden fixture material must not appear in exception strings, CI-safe receipts, filenames, or serialized public commitment objects.

---

## File Structure

### New production modules

- `scripts/v5/td_unified/task4_registry_adapter_v1.py` — current-registry-only adapter; full prerequisite closure; construction-time Task 1 validation; diagnostic/authority separation; legacy import firewall helper.
- `scripts/v5/td_unified/task4_custody_store_v1.py` — defect-bearing revocation identity; append-only durable JSONL ledger; expected-head file; replay; external signer/verifier contracts; crash-safe append protocol.
- `scripts/v5/td_unified/task4_actor_attestation_v1.py` — authenticated action-attestation model and frozen privileged-role checks for promotion/revocation/custody actions.
- `scripts/v5/td_unified/task4_requirement_policy_v1.py` — closed requirement-class vocabulary and issuer/content-validation law.
- `scripts/v5/td_unified/task4_authority_barrier_v1.py` — evaluates C1–C9/R5 prerequisites; returns structured non-authorizing diagnostics; never promotes registry units.
- `scripts/v5/td_unified/challenge_custody_v1.py` — Task 4 campaign/seal/exposure/output-freeze/reveal/regeneration state machine and custody receipts.
- `scripts/v5/td_unified/task4_publication_guard_v1.py` — NO-ECHO/publication-surface secret scanning helpers.

### New schemas

- `schemas/target_discovery/unified_v1/qualification_campaign_v1.json`
- `schemas/target_discovery/unified_v1/sealed_challenge_definition_v1.json`
- `schemas/target_discovery/unified_v1/sealed_realization_set_v1.json`
- `schemas/target_discovery/unified_v1/exposure_ledger_v1.json`
- `schemas/target_discovery/unified_v1/method_output_freeze_receipt_v1.json`
- `schemas/target_discovery/unified_v1/sealed_qualification_reveal_v1.json`
- `schemas/target_discovery/unified_v1/sealed_custody_receipt_v1.json`
- `schemas/target_discovery/unified_v1/qualification_evidence_package_v1.json`
- `schemas/target_discovery/unified_v1/task4_actor_action_attestation_v1.json`
- `schemas/target_discovery/unified_v1/task4_persistent_custody_head_v1.json`

### New tests

- `tests/v5/td_unified/test_task4_red_c1_c9.py` — RED-only carry-forward attacks; first Task 4 commit.
- `tests/v5/td_unified/test_task4_registry_adapter_v1.py`
- `tests/v5/td_unified/test_task4_custody_store_v1.py`
- `tests/v5/td_unified/test_task4_actor_attestation_v1.py`
- `tests/v5/td_unified/test_task4_requirement_policy_v1.py`
- `tests/v5/td_unified/test_task4_authority_barrier_v1.py`
- `tests/v5/td_unified/test_challenge_custody_v1.py`
- `tests/v5/td_unified/test_challenge_custody_v1_hostile.py`
- `tests/v5/td_unified/test_task4_publication_guard_v1.py`
- `tests/v5/td_unified/test_task4_workflow_policy_v1.py`
- `tests/v5/td_unified/test_task4_performance_v1.py`

### Workflow

- `.github/workflows/unified-task4-custody.yml` — focused Task 4 + full unified regression; read-only token; full-history checkout.

---

### Task 1: Freeze-derived RED branch and preserve C1–C9 hostile failures

**Files:**
- Create: `tests/v5/td_unified/test_task4_red_c1_c9.py`
- Create: `.github/workflows/unified-task4-custody.yml`
- Do not create any Task 4 production module in this task.

**Interfaces:**
- Consumes: frozen `registry_v1.RegistryHistoryCustody`, `registry_v1.promote_unit`, `registry_v1.revoke_or_supersede`, `registry_v1.derive_real_reference_ready` from exact Task 3.
- Produces: a stable RED attack vocabulary and fixture builders that later Task 4 tests reuse; no authority object.

- [ ] **Step 1: Create execution branch from exact frozen Task 3**

Create `work/unified-task4-red-20261016` from `117dd51dea827e734b299982da93991b934bdc8f`.

Expected: branch ancestry is exact; no design-branch commits are in the execution branch.

- [ ] **Step 2: Write the RED C1 tests**

Add tests named:

```python
def test_revoked_identity_cannot_reenter_with_added_cosmetic_restriction(): ...
def test_revoked_identity_cannot_reenter_with_reordered_restrictions(): ...
def test_revoked_identity_target_fork_cannot_evade_anchor(): ...
def test_nested_revoked_prerequisite_depth2_blocks_authority(): ...
def test_nested_revoked_prerequisite_depth3_blocks_authority(): ...
def test_fresh_process_cannot_erase_revocation(): ...
def test_truncated_rechained_ledger_cannot_regain_authority(): ...
```

Each test must assert refusal of an authority-bearing Task 4 precondition; the first two preserve Macha's accepted-review BAD rows exactly.

- [ ] **Step 3: Write RED C3–C9 tests**

Add tests for:

```python
def test_task4_has_no_legacy_registry_import_route(): ...
def test_ready_diagnostic_cannot_be_used_as_authority(): ...
def test_actor_name_without_attestation_cannot_authorize_action(): ...
def test_revocation_requires_frozen_privileged_actor_policy(): ...
def test_unknown_requirement_class_fails_closed(): ...
def test_registry_unit_invalid_under_task1_law_is_refused_at_task4_boundary(): ...
def test_same_process_fixture_state_cannot_upgrade_to_authoritative_mode(): ...
```

- [ ] **Step 4: Add read-only Task 4 workflow**

Workflow requirements:

```yaml
permissions:
  contents: read
```

Checkout uses `fetch-depth: 0`. Workflow runs focused Task 4 tests and full `tests/v5/td_unified`. It contains no shell command that modifies, commits, or pushes repository files.

- [ ] **Step 5: Run focused RED**

Run:

```bash
python -m pytest -q tests/v5/td_unified/test_task4_red_c1_c9.py
```

Expected: failures correspond to the not-yet-existing Task 4 boundaries; no import/collection failure unrelated to the intended RED surface.

- [ ] **Step 6: Commit RED-only state**

```bash
git add tests/v5/td_unified/test_task4_red_c1_c9.py .github/workflows/unified-task4-custody.yml
git commit -m "test(task4): preserve C1-C9 authority attacks as RED"
```

Reviewer gate: confirm zero Task 4 production code and zero final secret material.

---

### Task 2: Registry authority adapter and legacy/diagnostic firewall

**Files:**
- Create: `scripts/v5/td_unified/task4_registry_adapter_v1.py`
- Create: `tests/v5/td_unified/test_task4_registry_adapter_v1.py`
- Modify: `tests/v5/td_unified/test_task4_red_c1_c9.py` only to point preserved attacks at the new public interface; do not delete attack semantics.

**Interfaces:**
- Consumes: `registry_v1` only; Task 1 `validate_authority_record` semantics through the existing frozen module path; Task 3 registry snapshots/resolvers.
- Produces:
  - `build_validated_registry_unit(payload: Mapping[str, object]) -> RegistryUnit`
  - `walk_authority_prerequisite_units(registry, unit_id: str, gate: str) -> tuple[str, ...]`
  - `validate_registry_snapshot_for_task4(registry, *, history_custody, authority_object_resolver, dependency_verifier) -> None`
  - `assert_no_legacy_registry_dependency(paths: tuple[Path, ...]) -> None`
  - `diagnostic_real_reference_ready(...) -> Mapping[str, object]` with explicit `authority_effect="NONE"`.

- [ ] **Step 1: Write failing adapter tests**

Tests must assert:

- construction refuses forbidden Task 1 scope/stage combinations;
- a nested revoked/superseded/requalification unit appears in the returned closure;
- current history custody must validate before Task 4 snapshot use;
- a forced `derive_real_reference_ready == true` diagnostic remains `authority_effect == "NONE"`;
- scanning Task 4 production paths detects direct and indirect `registry_v1_legacy` imports.

- [ ] **Step 2: Run focused tests and confirm RED**

```bash
python -m pytest -q tests/v5/td_unified/test_task4_registry_adapter_v1.py
```

Expected: FAIL because adapter module does not exist.

- [ ] **Step 3: Implement the adapter signatures**

`build_validated_registry_unit` validates the payload under frozen Task 1 law before constructing the Task 3 `RegistryUnit`. It does not patch frozen `registry_v1.py`.

`walk_authority_prerequisite_units` must traverse the same recursive dependency relation used by readiness and include the root unit.

- [ ] **Step 4: Run focused + frozen Task 3 regressions**

```bash
python -m pytest -q tests/v5/td_unified/test_task4_registry_adapter_v1.py tests/v5/td_unified/test_registry_v1*.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/v5/td_unified/task4_registry_adapter_v1.py tests/v5/td_unified/test_task4_registry_adapter_v1.py tests/v5/td_unified/test_task4_red_c1_c9.py
git commit -m "feat(task4): add registry authority adapter"
```

---

### Task 3: Defect-bearing revocation identity and persistent cross-process custody

**Files:**
- Create: `scripts/v5/td_unified/task4_custody_store_v1.py`
- Create: `tests/v5/td_unified/test_task4_custody_store_v1.py`
- Create: `schemas/target_discovery/unified_v1/task4_persistent_custody_head_v1.json`

**Interfaces:**
- Consumes: validated registry snapshots and prerequisite unit IDs from Task 2.
- Produces:
  - `revocation_subject_identity(unit_payload: Mapping[str, object]) -> str`
  - `CustodyEvent(kind: str, subject_id: str, payload_sha256: str, previous_head: str, sequence: int)`
  - `ExternalSigner` interface: `sign(message: bytes) -> bytes`, `signer_identity: str`
  - `ExternalVerifier` interface: `verify(message: bytes, signature: bytes, signer_identity: str) -> bool`
  - `PersistentCustodyStore.open(root: Path, *, verifier: ExternalVerifier, expected_head: str | None) -> PersistentCustodyStore`
  - `append_event(event_payload: Mapping[str, object], *, signer: ExternalSigner) -> str`
  - `assert_subject_not_revoked(subject_id: str) -> None`
  - `replay() -> CustodyReplayResult`.

- [ ] **Step 1: Write failing canonical-identity tests**

Assert the same `revocation_subject_identity` for payloads differing only by:

- restriction token order;
- duplicate-equivalent cosmetic restriction tokens;
- cosmetic restriction addition covered by the closed non-defect-bearing vocabulary;
- stage/lineage status.

Assert different identity when producer/executor code identity, manifest identity, policy identity, target/unit identity, or another explicitly defect-bearing dependency changes.

- [ ] **Step 2: Write failing persistence/restart tests**

Use a real subprocess to:

1. create store;
2. append revocation;
3. terminate process;
4. reload in a second process with published expected head;
5. assert the revoked subject remains blocked.

Also test stale expected head, truncation, reordered events, duplicate sequence, forked head, and a partially-written pending event.

- [ ] **Step 3: Run RED**

```bash
python -m pytest -q tests/v5/td_unified/test_task4_custody_store_v1.py
```

Expected: FAIL because the custody store does not exist.

- [ ] **Step 4: Implement crash-safe ledger protocol**

Persist canonical event bytes append-only. Publish a separate head record only after the event file is fsynced. `open()` refuses disagreement among event chain, signature verification, and caller-supplied externally published expected head. A pending/unpublished tail is recoverable only as non-authoritative evidence and cannot satisfy `expected_head`.

- [ ] **Step 5: Re-run C1 preserved attacks**

```bash
python -m pytest -q tests/v5/td_unified/test_task4_custody_store_v1.py tests/v5/td_unified/test_task4_red_c1_c9.py
```

Expected: persistent/fork/restriction C1 attacks PASS; actor/policy/barrier tests may remain RED until later tasks.

- [ ] **Step 6: Commit**

```bash
git add scripts/v5/td_unified/task4_custody_store_v1.py tests/v5/td_unified/test_task4_custody_store_v1.py schemas/target_discovery/unified_v1/task4_persistent_custody_head_v1.json tests/v5/td_unified/test_task4_red_c1_c9.py
git commit -m "feat(task4): add persistent revocation custody"
```

Reviewer gate: this closes only implemented R4 mechanics; no authority-stage promotion is added.

---

### Task 4: Actor attestation, revocation authority, and closed requirement classes

**Files:**
- Create: `scripts/v5/td_unified/task4_actor_attestation_v1.py`
- Create: `scripts/v5/td_unified/task4_requirement_policy_v1.py`
- Create: `tests/v5/td_unified/test_task4_actor_attestation_v1.py`
- Create: `tests/v5/td_unified/test_task4_requirement_policy_v1.py`
- Create: `schemas/target_discovery/unified_v1/task4_actor_action_attestation_v1.json`

**Interfaces:**
- Consumes: frozen Task 3 actor registry/policy resolver; external verifier identity from Task 3 custody layer.
- Produces:
  - `ActorActionAttestation(actor_identity_sha: str, role: str, action: str, subject_sha: str, sequence: int, signature: bytes, signer_identity: str)`
  - `validate_actor_action(attestation, *, actor_registry, frozen_policy, verifier) -> str` returning canonical authenticated actor ID;
  - `RequirementClass` closed enum;
  - `RequirementIssuerPolicy(requirement_class, allowed_roles, content_validation_required)`;
  - `validate_requirement_evidence(requirement, evidence, *, actor_context) -> None`.

- [ ] **Step 1: Write actor-attestation RED tests**

Reject name-only actor, caller-minted signer identity, signature from wrong signer, producer/executor acting as forbidden controller/revoker, Unicode/case/whitespace alias, and actor-registry substitution.

- [ ] **Step 2: Write requirement-class RED tests**

Reject unknown class, generic fallback, missing issuer, issuer wrong role, issuer identical to prohibited producer/executor, bare `{object_role: ...}` dictionary, and class/evidence mismatch.

- [ ] **Step 3: Implement minimum validation interfaces**

Do not introduce a private key or production signing secret in repository code. Fixture signatures use a dedicated non-authorizing test backend and must carry `promotion_authority = NONE`.

- [ ] **Step 4: Verify**

```bash
python -m pytest -q tests/v5/td_unified/test_task4_actor_attestation_v1.py tests/v5/td_unified/test_task4_requirement_policy_v1.py tests/v5/td_unified/test_task4_red_c1_c9.py
```

Expected: C5/C6/C7 preserved attacks PASS; remaining campaign/barrier attacks may still be RED.

- [ ] **Step 5: Commit**

```bash
git add scripts/v5/td_unified/task4_actor_attestation_v1.py scripts/v5/td_unified/task4_requirement_policy_v1.py tests/v5/td_unified/test_task4_actor_attestation_v1.py tests/v5/td_unified/test_task4_requirement_policy_v1.py schemas/target_discovery/unified_v1/task4_actor_action_attestation_v1.json tests/v5/td_unified/test_task4_red_c1_c9.py
git commit -m "feat(task4): authenticate actors and close requirement classes"
```

---

### Task 5: C1–C9 authority barrier evaluator

**Files:**
- Create: `scripts/v5/td_unified/task4_authority_barrier_v1.py`
- Create: `tests/v5/td_unified/test_task4_authority_barrier_v1.py`

**Interfaces:**
- Consumes: Task 2 registry adapter, Task 3 persistent custody, Task 4 actor attestation, Task 4 requirement policy.
- Produces:
  - `Task4BarrierStatus(overall: str, checks: Mapping[str, str], authority_effect: str, claim_scope: str)`
  - `evaluate_task4_preauthority_barrier(unit_id: str, registry, *, custody_store, expected_head, actor_context, authority_object_resolver, dependency_verifier, raw_resolver) -> Task4BarrierStatus`
  - `require_task4_preauthority_barrier_green(status: Task4BarrierStatus) -> None`.

- [ ] **Step 1: Write failing barrier tests**

Assert `overall != "GREEN"` when any one of C1–C9 is missing. Include a table-driven test that flips each check independently.

Assert `authority_effect == "NONE"` even when barrier is GREEN; the barrier is permission evidence for a later task, not a registry promotion function.

Assert `claim_scope == "POOLED_DONOR_LEVEL_ONLY"`.

- [ ] **Step 2: Add sibling-route tests**

For the same prohibited state, attack direct call, construction, deserialization, replay, fresh process, nested prerequisite, revoked/superseded dependency, legacy import, stale readiness diagnostic, and caller mode/config override.

- [ ] **Step 3: Implement evaluator**

No method in this module calls `promote_unit`. All authoritative registry/custody checks are re-resolved at evaluation time.

- [ ] **Step 4: Verify focused and inherited registry suites**

```bash
python -m pytest -q tests/v5/td_unified/test_task4_authority_barrier_v1.py tests/v5/td_unified/test_task4_red_c1_c9.py tests/v5/td_unified/test_registry_v1*.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/v5/td_unified/task4_authority_barrier_v1.py tests/v5/td_unified/test_task4_authority_barrier_v1.py tests/v5/td_unified/test_task4_red_c1_c9.py
git commit -m "feat(task4): add C1-C9 preauthority barrier"
```

---

### Task 6: Campaign, sealed definition, and finite realization set

**Files:**
- Create: `scripts/v5/td_unified/challenge_custody_v1.py`
- Create: `tests/v5/td_unified/test_challenge_custody_v1.py`
- Create schemas:
  - `qualification_campaign_v1.json`
  - `sealed_challenge_definition_v1.json`
  - `sealed_realization_set_v1.json`

**Interfaces:**
- Consumes: GREEN Task4 barrier evidence, persistent custody store, validated actor context; synthetic fixture challenge generator only.
- Produces:
  - `CampaignState` enum exactly: `CAMPAIGN_CREATED`, `DEFINITION_SEALED`, `REALIZATION_SET_SEALED`, `EXPOSURE_ACTIVE`, `ALL_REQUIRED_OUTPUTS_FROZEN`, `HIDDEN_MATERIAL_REVEALED`, `REGENERATION_VERIFIED`, `CUSTODY_COMPLETE`, `INVALIDATED`;
  - `QualificationCampaign` dataclass/payload;
  - `SealedChallengeDefinition` dataclass/payload;
  - `SealedRealizationSet` dataclass/payload;
  - `create_campaign(...) -> QualificationCampaign`;
  - `seal_definition(...) -> tuple[QualificationCampaign, SealedChallengeDefinition]`;
  - `seal_realization_set(...) -> tuple[QualificationCampaign, SealedRealizationSet]`.

- [ ] **Step 1: Write state-machine and namespace RED tests**

Test development namespace has `promotion_authority = "NONE"`; final namespace refuses debug nonce material; campaign ID cannot be reused with changed dependencies; a new ledger creates a new campaign; changed/ambiguous scientific challenge defaults to `NEW_QUALIFICATION_CAMPAIGN`.

- [ ] **Step 2: Write finite-exam RED tests**

Refuse incomplete inventory, lazy generation after first exposure, reordered inventory, changed content digest, changed budget, and caller-provided world list not regenerated from the sealed definition.

- [ ] **Step 3: Implement campaign + sealing interfaces**

Public commitment payload contains commitments only; hidden fixture nonce/spec bytes are not serialized into public objects.

- [ ] **Step 4: Verify**

```bash
python -m pytest -q tests/v5/td_unified/test_challenge_custody_v1.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/v5/td_unified/challenge_custody_v1.py tests/v5/td_unified/test_challenge_custody_v1.py schemas/target_discovery/unified_v1/qualification_campaign_v1.json schemas/target_discovery/unified_v1/sealed_challenge_definition_v1.json schemas/target_discovery/unified_v1/sealed_realization_set_v1.json
git commit -m "feat(task4): add sealed campaign and realization custody"
```

---

### Task 7: Exposure, output freeze, reveal, regeneration, and custody receipts

**Files:**
- Modify: `scripts/v5/td_unified/challenge_custody_v1.py`
- Modify: `tests/v5/td_unified/test_challenge_custody_v1.py`
- Create: `tests/v5/td_unified/test_challenge_custody_v1_hostile.py`
- Create schemas:
  - `exposure_ledger_v1.json`
  - `method_output_freeze_receipt_v1.json`
  - `sealed_qualification_reveal_v1.json`
  - `sealed_custody_receipt_v1.json`
  - `qualification_evidence_package_v1.json`

**Interfaces:**
- Consumes: Task 6 campaign/definition/realization objects and Task 3 persistent custody store.
- Produces:
  - `issue_exposure(...) -> ExposureRecord`
  - `freeze_method_output(...) -> MethodOutputFreezeReceipt`
  - `reveal_hidden_material(...) -> SealedQualificationReveal`
  - `verify_regeneration(...) -> RegenerationVerification`
  - `finalize_custody(...) -> tuple[SEALED_CUSTODY_RECEIPT_V1, QUALIFICATION_EVIDENCE_PACKAGE_V1]`.

- [ ] **Step 1: Write exposure-spend RED tests**

Every exposure consumes budget even if method crashes, output malformed, run abandoned, result unfavorable, wrapper renamed, or later software defect discovered.

- [ ] **Step 2: Write freeze/reveal RED tests**

Refuse early reveal, output mutation after freeze, late exposure after all outputs frozen, reveal mismatch, missing committed realization, selective finalization, and eligibility before own reveal.

- [ ] **Step 3: Write anti-reset/multiplicity RED tests**

Refuse method-name reset, campaign restart erasing prior exposure, unchanged successor reroll, reused family declared secret again, and additive stress replacing prior failures.

- [ ] **Step 4: Implement lifecycle transitions**

Every transition re-evaluates current registry/custody/barrier state. `INVALIDATED` has no automatic outgoing transition.

- [ ] **Step 5: Verify focused lifecycle tests**

```bash
python -m pytest -q tests/v5/td_unified/test_challenge_custody_v1.py tests/v5/td_unified/test_challenge_custody_v1_hostile.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/v5/td_unified/challenge_custody_v1.py tests/v5/td_unified/test_challenge_custody_v1.py tests/v5/td_unified/test_challenge_custody_v1_hostile.py schemas/target_discovery/unified_v1/exposure_ledger_v1.json schemas/target_discovery/unified_v1/method_output_freeze_receipt_v1.json schemas/target_discovery/unified_v1/sealed_qualification_reveal_v1.json schemas/target_discovery/unified_v1/sealed_custody_receipt_v1.json schemas/target_discovery/unified_v1/qualification_evidence_package_v1.json
git commit -m "feat(task4): add exposure freeze reveal and custody finalization"
```

---

### Task 8: Publication/secret guard and NO-ECHO failures

**Files:**
- Create: `scripts/v5/td_unified/task4_publication_guard_v1.py`
- Create: `tests/v5/td_unified/test_task4_publication_guard_v1.py`

**Interfaces:**
- Consumes: public commitment/receipt payloads, candidate log/artifact/path metadata, fixture hidden values.
- Produces:
  - `scan_publication_surface(*, secret_tokens: tuple[bytes, ...], repository_bytes: bytes, log_bytes: bytes, artifact_bytes: tuple[bytes, ...], receipt_bytes: tuple[bytes, ...], path_strings: tuple[str, ...]) -> None`
  - narrow `Task4CustodyRefusal(code: str)` whose public message contains code only and never attacker-controlled secret text.

- [ ] **Step 1: Write leakage RED tests**

Test realistic-size fixture secrets in public commitment payload, exception text, CI-like log, uploaded-artifact bytes, generated receipt, filename/path, and cache metadata.

- [ ] **Step 2: Write internal-error distinction test**

A programming error must remain distinguishable from lawful `Task4CustodyRefusal`; it cannot be converted into a successful fail-closed custody verdict.

- [ ] **Step 3: Implement guard**

Secret scanner accepts bytes, not decoded substrings only; scan raw serialized bytes where possible.

- [ ] **Step 4: Verify**

```bash
python -m pytest -q tests/v5/td_unified/test_task4_publication_guard_v1.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/v5/td_unified/task4_publication_guard_v1.py tests/v5/td_unified/test_task4_publication_guard_v1.py
git commit -m "feat(task4): guard publication surface and no-echo errors"
```

---

### Task 9: Inherited 13 attacks + expanded 36 attacks

**Files:**
- Modify: `tests/v5/td_unified/test_challenge_custody_v1_hostile.py`
- Add fixture helpers only under `tests/v5/td_unified/` as needed; no production shortcut fixtures.

**Interfaces:**
- Consumes: complete Task 4 public interface from Tasks 2–8.
- Produces: comprehensive hostile qualification evidence; no new production interface.

- [ ] **Step 1: Port all 13 inherited historical custody attacks through the Task 4 interface**

Preserve their semantics, translating obsolete generic “harder/easier” cases into the controlling `NEW_QUALIFICATION_CAMPAIGN` / independently reviewed additive-stress law.

- [ ] **Step 2: Implement the full 36 expanded attacks from the controlling Task 4 design**

Use one named test per attack or a table with explicit IDs `T4-A01` … `T4-A36`. No attack may be silently covered only by an unrelated earlier assertion.

- [ ] **Step 3: Add sibling-route variants for every authority-bearing state touched by a repaired attack**

At minimum include construction, reload, replay, fresh process, nested prerequisite, legacy path, stale diagnostic, and campaign restart where semantically applicable.

- [ ] **Step 4: Run hostile suite**

```bash
python -m pytest -q tests/v5/td_unified/test_challenge_custody_v1_hostile.py tests/v5/td_unified/test_task4_red_c1_c9.py
```

Expected: PASS with no xfail/skip for mandatory attacks.

- [ ] **Step 5: Commit**

```bash
git add tests/v5/td_unified/test_challenge_custody_v1_hostile.py tests/v5/td_unified/test_task4_red_c1_c9.py
git commit -m "test(task4): close inherited and expanded hostile attack matrix"
```

---

### Task 10: Reference/optimized replay equivalence and performance ceilings

**Files:**
- Modify: `scripts/v5/td_unified/task4_custody_store_v1.py`
- Create: `tests/v5/td_unified/test_task4_performance_v1.py`

**Interfaces:**
- Consumes: canonical ledger event format.
- Produces:
  - `replay_reference() -> CustodyReplayResult`
  - `replay_optimized() -> CustodyReplayResult`
  with byte-identical final canonical result/head for the same ledger.

- [ ] **Step 1: Write equivalence tests**

Assert identical semantic validation results, final head, subject-revocation state, exposure counts, and campaign state between reference and optimized replay.

- [ ] **Step 2: Write mutation tests against optimized path**

Ensure cache/index optimization does not skip signature, sequence, previous-head, subject, actor, or state-order validation.

- [ ] **Step 3: Define and test declared ceilings**

Use synthetic ledgers at historical-scale and a larger projected scale. Record the exact sizes and ceiling in test constants; failure is explicit if ceiling is exceeded on CI reference hardware after the ceiling is empirically set on the first GREEN candidate. Do not weaken semantic checks to meet the ceiling.

- [ ] **Step 4: Commit**

```bash
git add scripts/v5/td_unified/task4_custody_store_v1.py tests/v5/td_unified/test_task4_performance_v1.py
git commit -m "perf(task4): qualify deterministic custody replay"
```

---

### Task 11: Workflow policy, full regression, and candidate custody packet

**Files:**
- Modify: `.github/workflows/unified-task4-custody.yml`
- Create: `tests/v5/td_unified/test_task4_workflow_policy_v1.py`
- Create: `docs/agent/UNIFIED_TASK4_CANDIDATE_REVIEW_PACKET_20261016.md`
- Create: `results/target_discovery/unified_qualification_v1/UNIFIED_TASK4_CANDIDATE_STATE_V1.json`

**Interfaces:**
- Consumes: exact Task 4 implementation head and CI run identities.
- Produces: candidate review packet only; no acceptance/freeze authority.

- [ ] **Step 1: Write workflow policy tests**

Assert Task 4 workflow declares `contents: read`, full-history checkout, no write permission, and no `git commit`, `git push`, contents API mutation, or auto-repair script invocation.

- [ ] **Step 2: Run focused Task 4 suite**

```bash
python -m pytest -q tests/v5/td_unified/test_task4*.py tests/v5/td_unified/test_challenge_custody_v1*.py
```

Expected: PASS, zero mandatory skips/xfails.

- [ ] **Step 3: Run full unified regression**

```bash
python -m pytest -q tests/v5/td_unified
```

Expected: PASS.

- [ ] **Step 4: Run frozen Task 3/2/1 workflows and inherited synthetic integration on the exact same head**

Record exact run IDs and conclusions in the candidate state JSON. Do not substitute local results for required CI evidence.

- [ ] **Step 5: Confirm frozen-code diff**

Compare candidate against `117dd51dea827e734b299982da93991b934bdc8f`. Expected: no modification of frozen Task 0–3 production files; only Task 4 modules/schemas/tests/workflow/docs/results are added or changed.

- [ ] **Step 6: Build review packet**

Packet must state:

- exact candidate SHA;
- RED-only head + intended failures;
- all Task 4 GREEN run IDs;
- exact inherited regression run IDs;
- whether R4/R7/C9 are claimed closed and for what scope;
- all fixture/non-authorizing limitations;
- no final hidden material generated;
- global authority still unchanged;
- independent Macha exact-head review required before Task 5.

- [ ] **Step 7: Commit custody packet**

```bash
git add .github/workflows/unified-task4-custody.yml tests/v5/td_unified/test_task4_workflow_policy_v1.py docs/agent/UNIFIED_TASK4_CANDIDATE_REVIEW_PACKET_20261016.md results/target_discovery/unified_qualification_v1/UNIFIED_TASK4_CANDIDATE_STATE_V1.json
git commit -m "docs(task4): package exact-head candidate for independent review"
```

---

## Final Verification Before Claiming a Task 4 Candidate

Run on one exact head:

```bash
python -m pytest -q tests/v5/td_unified/test_task4*.py tests/v5/td_unified/test_challenge_custody_v1*.py
python -m pytest -q tests/v5/td_unified
```

Then require exact-head CI success for:

1. Unified Task 4 custody workflow;
2. frozen Task 3 registry regression;
3. frozen Task 2 manifest/access regression;
4. frozen Task 1 regression;
5. inherited unified synthetic integration;
6. Task 4 workflow-policy regression.

Before handoff, verify:

- no final challenge secrets/nonces/worlds exist in committed tree, CI logs, workflow artifacts, receipts, or paths;
- no Task 4/downstream production import of `registry_v1_legacy`;
- no Task 4 authority consumer treats `derive_real_reference_ready` as authority;
- every authority-bearing transition re-resolves current registry/custody state;
- every committed realization has explicit terminal accounting;
- exposure spend survives crash/abandon/rename/repair;
- R5 pooled-donor scope is present in the evidence-package schema;
- global state is still `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.

Only after those checks may the controller label the head:

`TASK4_CANDIDATE_GREEN__INDEPENDENT_REVIEW_REQUIRED`

It must not be labelled accepted/frozen until independent exact-head Macha review passes.