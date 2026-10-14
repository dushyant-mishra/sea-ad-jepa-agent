# Unified TD Qualification and Downstream Custody V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the schema-first custody system that makes known-truth certification and sealed human TD execution use one authenticated producer → artifact → executor chain, emits an immutable Target Qualification Bundle, and certifies exact downstream consumption without changing current human/training authority.

**Architecture:** Implement focused `scripts/v5/td_unified/` modules and machine schemas that share canonical authentication, authority-state, population-access, receipt-lineage, and mode-equivalence primitives. `TD_EXECUTION_MANIFEST_V1` is the root identity; `TD_QUALIFICATION_REGISTRY_V1` records demonstrated producer/artifact/executor authority; `KNOWN_TRUTH_CASEBUNDLE_V1` and external `TRUTH_BUNDLE_V1` exercise exact production paths; `TARGET_QUALIFICATION_BUNDLE_V1` is the only TD→downstream handoff; `DOWNSTREAM_CERTIFICATION_CONTRACT_V1` verifies exact bundle consumption and inherited obligations.

**Tech Stack:** Python 3.11; stdlib `json`, `hashlib`, `dataclasses`/`typing`, `pathlib`; NumPy only where existing production producer interfaces require it; pytest 9.x; existing `scripts/v5` TD executors/producers; GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-14-unified-td-qualification-downstream-custody-architecture-v1.md`; binding amendment `docs/superpowers/specs/2026-10-14-unified-td-qualification-downstream-custody-architecture-v1-1-hostile-review-amendment.md`; execution pivot `docs/superpowers/specs/2026-10-14-production-synthetic-to-unified-td-execution-pivot.md`. Accepted design head: `3064ca545f0c94859ea989cd49a04fcbd5b9a303`; acceptance comment: `6174861625`.

## Global Constraints

- Binding project authority remains exactly `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
- No task opens current human candidate outcomes, chooses a target/representation, authorizes TD60/Stage4, or enables synthetic/real training.
- For the current TD manifest, held-out evaluation is deterministic cross-fitting within `reader_fit`; `reader_validation` and `reader_oracle` remain protected and cannot be opened merely to rescue estimability.
- A digest string is never authority: canonical payload bytes must be reserialized, digests recomputed, and all authority-bearing parents/dependencies recursively verified.
- Scientific identity binds exact payload/code/policy/input identities; PR numbers and branch tips are navigation metadata only.
- Canonical `qualification_stage` order is `SEMANTICS_ONLY → FIXTURE_SAME_INTERFACE → SAME_CODE_PATH → KNOWN_TRUTH_QUALIFIED → REAL_REFERENCE_READY → HUMAN_EXECUTABLE → HUMAN_EXECUTED → DOWNSTREAM_CERTIFIED → TRAINING_ELIGIBLE → TRAINING_AUTHORIZED`.
- Canonical `active_lineage_status` is one of `ACTIVE | SUPERSEDED | REVOKED_BY_DEFECT | REQUIRES_REQUALIFICATION`; only `ACTIVE` identities may enter a new execution manifest.
- Every authority object binds `authority_scope`; unit-level qualification can never imply pipeline/project authority.
- Development fixtures cannot establish final `KNOWN_TRUTH_QUALIFIED`; final qualification requires a separately sealed challenge realization/holdout and independent adjudication.
- Known-truth truth data remain physically/logically external to producer/executor/controller inputs and are consumed only after normal outputs are irrevocably frozen.
- No independent synthetic G2/G6/G7/G8/R1/geometry/increment executor or synthetic winner controller may be implemented.
- Existing Tasks 1–3 from PR #356 remain shared foundation work; this plan replaces the old independent interpretation of Tasks 4–12.
- Existing repaired TD gates are registered at demonstrated authority only; no old `PASS`, `GREEN`, `qualified`, or #369 system-battery result auto-promotes a unit under the V1.1 lifecycle.
- Every implementation task is RED-first, independently reviewable, and committed before the next task begins.

## Review Focus

- **Forged but well-formed identity:** a correct-looking 64-hex digest with altered payload/parent bytes must fail canonical verification, not be trusted as a string. Covered in Task 1.
- **Stale authority after defect:** a historically qualified receipt later marked `REVOKED_BY_DEFECT` must remain auditable but become unusable by manifests/readiness derivation. Covered in Task 3.
- **Protected-partition rescue attempt:** any producer that reads `reader_validation`/`reader_oracle` outside the bound current-TD policy must invalidate its receipt even if the numeric output is correct. Covered in Task 2.
- **Known-truth mode shortcut:** equivalent observable payloads entering known-truth and human wrappers must traverse the same scientific validators/producers/executors; any mode-conditioned scientific branch invalidates `SAME_CODE_PATH`. Covered in Task 5.
- **Downstream semantic widening:** a consumer that keeps the target ID but widens support, drops a falsifier, changes evidence/observation semantics, or substitutes representation semantics must fail exact-bundle certification. Covered in Task 8.

---

## File Structure

Create the focused package below; do not add gate-specific scientific logic to it.

```text
scripts/v5/td_unified/
  __init__.py                       package marker only
  canonical_v1.py                   canonical serialization/digest/lineage verification
  authority_v1.py                   qualification stage, lineage status, authority scope
  manifest_v1.py                    TD_EXECUTION_MANIFEST_V1 + population/access policy
  registry_v1.py                    TD_QUALIFICATION_REGISTRY_V1 + transitions/revocations/prerequisites
  challenge_custody_v1.py           development/sealed challenge commitments and exposure rules
  casebundle_v1.py                  KNOWN_TRUTH_CASEBUNDLE_V1 / TRUTH_BUNDLE_V1 validators
  mode_equivalence_v1.py            scientific execution trace + MODE_PATH_EQUIVALENCE_RECEIPT
  gate_registration_v1.py           exact repaired-unit registration without promotion
  target_bundle_v1.py               TARGET_QUALIFICATION_BUNDLE_V1 issuer/verifier
  downstream_contract_v1.py         exact bundle consumption + inherited-obligation receipts
  challenge_worlds_v1.py            reusable A–I world specifications/generation contracts
  rehearsal_v1.py                   real TD controller rehearsal orchestration only
  finalizer_v1.py                   qualification/rehearsal receipt finalization

schemas/target_discovery/unified_v1/
  scientific_receipt_v1.json
  authority_record_v1.json
  td_execution_manifest_v1.json
  population_access_policy_v1.json
  td_qualification_registry_v1.json
  sealed_challenge_manifest_v1.json
  known_truth_casebundle_v1.json
  truth_bundle_v1.json
  mode_path_equivalence_receipt_v1.json
  target_qualification_bundle_v1.json
  downstream_certification_contract_v1.json

results/target_discovery/unified_qualification_v1/
  (generated receipts only; no candidate outcomes)

tests/v5/td_unified/
  test_canonical_v1.py
  test_authority_v1.py
  test_manifest_v1.py
  test_registry_v1.py
  test_challenge_custody_v1.py
  test_casebundle_v1.py
  test_mode_equivalence_v1.py
  test_gate_registration_v1.py
  test_target_bundle_v1.py
  test_downstream_contract_v1.py
  test_challenge_worlds_v1.py
  test_rehearsal_v1.py
  test_finalizer_v1.py

.github/workflows/td-unified-qualification-v1.yml
```

Schemas are closed: unknown fields fail validation unless the schema explicitly declares an extensible metadata field. Scientific payloads use one canonical JSON encoding rule implemented in `canonical_v1.py`; tests and consumers must call that implementation rather than reproduce ad hoc `json.dumps` settings.

---

### Task 1: Canonical scientific identity and one authority model (A1 + A9 RED-first)

**Files:**
- Create: `scripts/v5/td_unified/__init__.py`
- Create: `scripts/v5/td_unified/canonical_v1.py`
- Create: `scripts/v5/td_unified/authority_v1.py`
- Create: `schemas/target_discovery/unified_v1/scientific_receipt_v1.json`
- Create: `schemas/target_discovery/unified_v1/authority_record_v1.json`
- Test: `tests/v5/td_unified/test_canonical_v1.py`
- Test: `tests/v5/td_unified/test_authority_v1.py`

**Interfaces:**
- Consumes: none beyond stdlib.
- Produces: `canonical_bytes(payload: Mapping[str, object]) -> bytes`; `canonical_sha256(payload) -> str`; `verify_scientific_receipt(receipt, object_resolver) -> VerifiedReceipt`; `QualificationStage`; `ActiveLineageStatus`; `AuthorityRecord`; `validate_authority_record(record) -> AuthorityRecord`.

- [ ] **Step 1: Write the A1 RED tests for canonical digest recomputation and parent-chain verification**

```python
def test_declared_digest_never_authenticates_mutated_payload(): ...
def test_valid_child_with_missing_or_invalid_parent_fails_closed(): ...
def test_receipt_binds_schema_producer_inputs_parents_output_manifest_registry_and_access(): ...
def test_duplicate_or_conflicting_parent_identity_is_rejected(): ...
```

Assertions must prove a caller-supplied correct-length digest cannot authenticate changed bytes, and recursive verification reaches a frozen root rather than trusting parent strings.

- [ ] **Step 2: Run the A1 tests and preserve RED**

Run: `python -m pytest -q tests/v5/td_unified/test_canonical_v1.py`
Expected: FAIL because `scripts.v5.td_unified.canonical_v1`/schemas do not yet exist.

- [ ] **Step 3: Write the A9 RED tests for the single canonical authority model**

```python
def test_only_canonical_ordered_qualification_stages_are_accepted(): ...
def test_only_four_active_lineage_statuses_are_accepted(): ...
def test_authority_scope_is_required_and_unit_stage_cannot_imply_project_training(): ...
def test_bare_pass_green_or_mechanics_qualified_is_not_a_stage(): ...
```

- [ ] **Step 4: Run the A9 tests and preserve RED**

Run: `python -m pytest -q tests/v5/td_unified/test_authority_v1.py`
Expected: FAIL because the authority model is not implemented.

- [ ] **Step 5: Implement canonical identity primitives**

Implement in `canonical_v1.py` the exact interfaces above. Canonicalization must reject non-JSON scientific values, duplicate/conflicting dependency identities, unknown receipt schema, missing payload bytes, and unverifiable lineage. SHA-256 is computed from canonical bytes; declared digest fields are comparisons only.

- [ ] **Step 6: Implement the canonical authority types and schemas**

Implement in `authority_v1.py` the exact V1.1 stage order, four lineage statuses, and required scope. Do not include a second authority enum.

- [ ] **Step 7: Run Task 1 tests GREEN**

Run: `python -m pytest -q tests/v5/td_unified/test_canonical_v1.py tests/v5/td_unified/test_authority_v1.py`
Expected: PASS.

- [ ] **Step 8: Commit Task 1**

```bash
git add scripts/v5/td_unified schemas/target_discovery/unified_v1/scientific_receipt_v1.json schemas/target_discovery/unified_v1/authority_record_v1.json tests/v5/td_unified/test_canonical_v1.py tests/v5/td_unified/test_authority_v1.py
git commit -m "feat: add unified TD canonical identity and authority model"
```

---

### Task 2: `TD_EXECUTION_MANIFEST_V1` and current-TD population access law (A4 RED-first)

**Files:**
- Create: `scripts/v5/td_unified/manifest_v1.py`
- Create: `schemas/target_discovery/unified_v1/td_execution_manifest_v1.json`
- Create: `schemas/target_discovery/unified_v1/population_access_policy_v1.json`
- Test: `tests/v5/td_unified/test_manifest_v1.py`

**Interfaces:**
- Consumes: Task 1 `canonical_sha256`, `verify_scientific_receipt`, `AuthorityRecord`.
- Produces: `PopulationAccessPolicy`; `ProducerAccessReceipt`; `TDExecutionManifest`; `build_current_td_access_policy(...) -> PopulationAccessPolicy`; `validate_manifest(payload, resolver) -> TDExecutionManifest`; `validate_producer_access(manifest, receipt) -> None`.

- [ ] **Step 1: Write the A4 RED tests for manifest-bound split/access semantics**

```python
def test_current_td_policy_crossfits_only_within_reader_fit(): ...
def test_reader_validation_access_cannot_rescue_estimability(): ...
def test_reader_oracle_access_is_protected_until_later_authority_transition(): ...
def test_producer_receipt_must_enumerate_actual_partitions_and_access_classes(): ...
def test_numeric_success_with_forbidden_partition_access_is_invalid(): ...
def test_held_out_token_has_no_authority_without_bound_policy(): ...
```

The frozen current-TD policy must encode deterministic held-out/cross-fitted evaluation within `reader_fit`; validation/oracle value access is denied for the current manifest.

- [ ] **Step 2: Write manifest identity RED tests**

```python
def test_manifest_binds_exact_code_policy_schema_registry_and_population_identities(): ...
def test_branch_or_pr_number_cannot_serve_as_scientific_identity(): ...
def test_moved_decision_bearing_identity_requires_new_manifest_digest(): ...
```

- [ ] **Step 3: Run Task 2 tests and preserve RED**

Run: `python -m pytest -q tests/v5/td_unified/test_manifest_v1.py`
Expected: FAIL because manifest/access-policy implementation is absent.

- [ ] **Step 4: Implement `PopulationAccessPolicy` and producer access receipts**

The current-TD constructor must pin `reader_fit` cross-fitting and protected `reader_validation`/`reader_oracle`; do not generalize those protected partitions into a rescue path.

- [ ] **Step 5: Implement `TDExecutionManifest` validation and canonical identity**

Bind exact canonical registry, observation/support contracts, controller code/policy, candidate/endpoint/source registries, qualification registry, population/access/cross-fitting/protected-partition policy identities, and per-unit code/policy/artifact/metric/reference identities. Navigation metadata is optional and non-authoritative.

- [ ] **Step 6: Run Task 2 tests GREEN**

Run: `python -m pytest -q tests/v5/td_unified/test_manifest_v1.py tests/v5/td_unified/test_canonical_v1.py tests/v5/td_unified/test_authority_v1.py`
Expected: PASS.

- [ ] **Step 7: Commit Task 2**

```bash
git add scripts/v5/td_unified/manifest_v1.py schemas/target_discovery/unified_v1/td_execution_manifest_v1.json schemas/target_discovery/unified_v1/population_access_policy_v1.json tests/v5/td_unified/test_manifest_v1.py
git commit -m "feat: bind unified TD manifest and population access law"
```

---

### Task 3: `TD_QUALIFICATION_REGISTRY_V1`, revocation, independence and prerequisite graphs (A2 + A5 + A6 RED-first)

**Files:**
- Create: `scripts/v5/td_unified/registry_v1.py`
- Create: `schemas/target_discovery/unified_v1/td_qualification_registry_v1.json`
- Test: `tests/v5/td_unified/test_registry_v1.py`

**Interfaces:**
- Consumes: Task 1 authority/canonical primitives; Task 2 manifest/access objects.
- Produces: `RegistryUnit`; `PrerequisiteRecord`; `RevocationReceipt`; `PromotionReceipt`; `TDQualificationRegistry`; `derive_real_reference_ready(unit, prerequisites, resolver) -> bool`; `promote_unit(...) -> RegistryUnit`; `revoke_or_supersede(...) -> RegistryUnit`.

- [ ] **Step 1: Write A2 RED tests for immutable historical evidence plus active revocation**

```python
def test_historical_promotion_receipt_remains_immutable_after_revocation(): ...
def test_revoked_known_truth_unit_cannot_enter_new_manifest(): ...
def test_code_or_policy_change_creates_new_registry_identity_without_stage_inheritance(): ...
def test_supersession_binds_successor_and_requalification_scope(): ...
```

- [ ] **Step 2: Write A5 RED tests for independent qualification/adjudication**

```python
def test_scientific_unit_cannot_self_issue_human_semantics_qualification(): ...
def test_promotion_requires_distinct_qualification_controller_identity(): ...
def test_human_executable_requires_independent_promotion_receipt(): ...
```

- [ ] **Step 3: Write A6 RED tests for dependency-complete real-reference readiness**

```python
def test_ready_boolean_cannot_override_missing_prerequisite(): ...
def test_one_revoked_reference_blocks_real_reference_ready(): ...
def test_every_prerequisite_must_match_manifest_producer_policy_access_and_stage(): ...
def test_unsatisfied_prerequisite_remains_visible_in_registry_output(): ...
```

- [ ] **Step 4: Run Task 3 tests and preserve RED**

Run: `python -m pytest -q tests/v5/td_unified/test_registry_v1.py`
Expected: FAIL because registry implementation is absent.

- [ ] **Step 5: Implement registry identities, promotion and revocation**

Promotion must be one stage at a time, require `ACTIVE`, recompute all receipt identities, and reject green-CI/prose status as authority evidence.

- [ ] **Step 6: Implement prerequisite-graph readiness derivation**

There is no authoritative aggregate `ready=true`; readiness is derived from the complete active prerequisite records each validation call.

- [ ] **Step 7: Run Task 3 tests GREEN**

Run: `python -m pytest -q tests/v5/td_unified/test_registry_v1.py tests/v5/td_unified/test_manifest_v1.py`
Expected: PASS.

- [ ] **Step 8: Commit Task 3**

```bash
git add scripts/v5/td_unified/registry_v1.py schemas/target_discovery/unified_v1/td_qualification_registry_v1.json tests/v5/td_unified/test_registry_v1.py
git commit -m "feat: add unified TD qualification registry"
```

---

### Task 4: Sealed qualification challenge custody (A3 RED-first)

**Files:**
- Create: `scripts/v5/td_unified/challenge_custody_v1.py`
- Create: `schemas/target_discovery/unified_v1/sealed_challenge_manifest_v1.json`
- Test: `tests/v5/td_unified/test_challenge_custody_v1.py`

**Interfaces:**
- Consumes: Task 1 canonical receipts; Task 2 manifest identity; Task 3 registry authority.
- Produces: `DevelopmentChallengeManifest`; `SealedQualificationCommitment`; `SealedQualificationReveal`; `commit_final_qualification(...)`; `verify_reveal(...)`; `record_qualification_exposure(...)`.

- [ ] **Step 1: Write A3 RED tests for development-versus-final qualification separation**

```python
def test_development_challenges_cannot_promote_known_truth_qualified(): ...
def test_final_commitment_freezes_family_realization_seed_expected_class_policy_budget_and_adjudicator(): ...
def test_at_least_one_holdout_remains_hidden_until_outputs_are_frozen(): ...
def test_reveal_mismatch_or_early_reveal_is_hard_failure(): ...
def test_failed_world_cannot_be_removed_or_replaced_after_exposure(): ...
def test_post_exposure_repair_requires_new_qualification_identity_and_new_sealed_set(): ...
```

- [ ] **Step 2: Run Task 4 tests and preserve RED**

Run: `python -m pytest -q tests/v5/td_unified/test_challenge_custody_v1.py`
Expected: FAIL because challenge custody implementation is absent.

- [ ] **Step 3: Implement development and sealed challenge custody objects**

Commitments expose only lawful public commitment material; hidden specifications/nonces remain controller-side. Exposure records are append-only and identity-bound.

- [ ] **Step 4: Run Task 4 tests GREEN**

Run: `python -m pytest -q tests/v5/td_unified/test_challenge_custody_v1.py tests/v5/td_unified/test_registry_v1.py`
Expected: PASS.

- [ ] **Step 5: Commit Task 4**

```bash
git add scripts/v5/td_unified/challenge_custody_v1.py schemas/target_discovery/unified_v1/sealed_challenge_manifest_v1.json tests/v5/td_unified/test_challenge_custody_v1.py
git commit -m "feat: seal unified TD qualification challenges"
```

---

### Task 5: `KNOWN_TRUTH_CASEBUNDLE_V1`, `TRUTH_BUNDLE_V1` and executable mode equivalence (A7 RED-first)

**Files:**
- Create: `scripts/v5/td_unified/casebundle_v1.py`
- Create: `scripts/v5/td_unified/mode_equivalence_v1.py`
- Create: `schemas/target_discovery/unified_v1/known_truth_casebundle_v1.json`
- Create: `schemas/target_discovery/unified_v1/truth_bundle_v1.json`
- Create: `schemas/target_discovery/unified_v1/mode_path_equivalence_receipt_v1.json`
- Test: `tests/v5/td_unified/test_casebundle_v1.py`
- Test: `tests/v5/td_unified/test_mode_equivalence_v1.py`

**Interfaces:**
- Consumes: Tasks 1–4 canonical/access/custody objects.
- Produces: `KnownTruthCaseBundle`; `TruthBundle`; `ScientificExecutionTrace`; `ModePathEquivalenceReceipt`; `validate_casebundle(...)`; `validate_truth_separation(...)`; `trace_scientific_path(wrapper, observable_payload) -> ScientificExecutionTrace`; `certify_mode_path_equivalence(...) -> ModePathEquivalenceReceipt`.

- [ ] **Step 1: Write CaseBundle/TruthBundle RED tests for physical/logical separation**

```python
def test_truth_fields_are_rejected_from_casebundle_payload_tree(): ...
def test_casebundle_preserves_measured_zero_four_state_observation_and_library_mass(): ...
def test_casebundle_uses_same_partition_access_semantics_as_current_human_manifest(): ...
def test_truth_is_read_only_after_normal_td_output_is_frozen(): ...
```

- [ ] **Step 2: Write A7 RED tests for machine-testable mode equivalence**

```python
def test_equivalent_observable_payloads_have_same_scientific_trace(): ...
def test_mode_specific_metric_support_reference_or_status_branch_invalidates_same_code_path(): ...
def test_truth_adjudication_difference_is_excluded_from_scientific_trace(): ...
def test_equivalence_receipt_binds_observable_trace_producer_executor_validator_and_branch_audit_digests(): ...
```

- [ ] **Step 3: Run Task 5 tests and preserve RED**

Run: `python -m pytest -q tests/v5/td_unified/test_casebundle_v1.py tests/v5/td_unified/test_mode_equivalence_v1.py`
Expected: FAIL because bundle/equivalence implementations are absent.

- [ ] **Step 4: Implement the gate-facing CaseBundle and external TruthBundle validators**

The CaseBundle schema carries canonical addresses, donor/source/operator hierarchy, four observation states, stored/unmaterialized library mass, candidate support/evidence rights, counts/depth and nuisance/context metadata. It never embeds expected verdicts or truth labels.

- [ ] **Step 5: Implement scientific execution tracing and equivalence certification**

Trace exact validators, access checks, producer/serializer/receipt-validator/executor entry points and decision-bearing branch identities. `SAME_CODE_PATH` promotion consumes this receipt; prose equivalence is insufficient.

- [ ] **Step 6: Run Task 5 tests GREEN**

Run: `python -m pytest -q tests/v5/td_unified/test_casebundle_v1.py tests/v5/td_unified/test_mode_equivalence_v1.py`
Expected: PASS.

- [ ] **Step 7: Commit Task 5**

```bash
git add scripts/v5/td_unified/casebundle_v1.py scripts/v5/td_unified/mode_equivalence_v1.py schemas/target_discovery/unified_v1/known_truth_casebundle_v1.json schemas/target_discovery/unified_v1/truth_bundle_v1.json schemas/target_discovery/unified_v1/mode_path_equivalence_receipt_v1.json tests/v5/td_unified/test_casebundle_v1.py tests/v5/td_unified/test_mode_equivalence_v1.py
git commit -m "feat: add unified known-truth bundles and mode equivalence"
```

---

### Task 6: Register current repaired TD units at demonstrated authority only

**Files:**
- Create: `scripts/v5/td_unified/gate_registration_v1.py`
- Test: `tests/v5/td_unified/test_gate_registration_v1.py`
- Generated later: `results/target_discovery/unified_qualification_v1/INITIAL_GATE_REGISTRY_V1.json`

**Interfaces:**
- Consumes: Task 3 registry; Task 5 mode-equivalence receipt type; exact repaired heads below.
- Produces: `current_repaired_unit_descriptors() -> tuple[UnitDescriptor, ...]`; `register_initial_repaired_units(...) -> TDQualificationRegistry`.

**Exact navigation/evidence heads to freeze as inputs, not authority shortcuts:**

| Unit | Evidence head | Initial full-unit stage | Blocking reason under V1.1 |
|---|---|---|---|
| G8 | `95dd474a02ce571722df9e8f08b42e81af2e8736` | `FIXTURE_SAME_INTERFACE` | observation operator repaired, but statistical estimand/reference producer unresolved; no A7 receipt |
| G6 | `4110d4478c3353d86740dd135d62460ff7a7611f` | `FIXTURE_SAME_INTERFACE` | substantive measurement-margin producer, produced qualification receipt and metric-scale contract missing; no A7 receipt |
| G9/S1/S2 | `8d6b23a18051f64463ee9b2649f4fe5fc7123f0d` | `FIXTURE_SAME_INTERFACE` | support/alignment/displacement/null producer pipeline incomplete; eigengap open; no A7 receipt |
| R1 | `949d76ff03cb57c5a88fef9efdb79fced9154024` | `FIXTURE_SAME_INTERFACE` | human Y-cell identity null producer missing; relation diagnostic is not human producer; no A7 receipt |
| G2 | `42df903d6190b7aa1b8eb65d810ab813cd327445` | `FIXTURE_SAME_INTERFACE` | candidate-specific static baseline/strata policy and real reference producer missing; no A7 receipt |
| G7 | `5a711f9a4ea0328445a05dadc1e011efb16a3c13` | `FIXTURE_SAME_INTERFACE` | decision mechanics exist, but full content-hash evidence-right/support producer chain is not demonstrated under E3/A7 |
| R4/C6/C4 increment | `b7c317c640aa231a7d5ec1fa12271a39bfee86e6` | `FIXTURE_SAME_INTERFACE` | decision mechanics only; candidate endpoints/support/reference producers unresolved; no A7 receipt |
| G12 scope guard | `01ebdb9384b42d5cfae3de03c2adf5b6b327ee81` | `FIXTURE_SAME_INTERFACE` | runtime scope guard only; candidate-specific support/human outcome execution absent |
| TD system battery V3 | `651d7a5a1d4f4047d5ac875cc603f9151c2fed36` | `FIXTURE_SAME_INTERFACE`, scope `PIPELINE:TD` | system mechanics/firewall test-of-test only; does not promote constituent units |

These are intentionally conservative proposed initial registrations. A task reviewer may lower a stage if exact evidence does not support even interface compatibility; no reviewer may raise a stage without the V1.1 promotion receipt required for that stage.

- [ ] **Step 1: Write RED tests that prohibit promotion-by-association**

```python
def test_369_system_pass_does_not_promote_constituent_units(): ...
def test_old_pass_or_qualified_strings_do_not_map_to_known_truth_qualified(): ...
def test_initial_units_have_active_status_and_no_human_or_training_scope(): ...
def test_stage_cannot_exceed_fixture_same_interface_without_a7_equivalence_receipt(): ...
```

- [ ] **Step 2: Write RED tests for exact head movement fail-closed behavior**

```python
def test_moved_registered_code_identity_requires_new_unit_identity(): ...
def test_registration_recomputes_source_payload_identity_instead_of_trusting_pr_metadata(): ...
```

- [ ] **Step 3: Run Task 6 tests and preserve RED**

Run: `python -m pytest -q tests/v5/td_unified/test_gate_registration_v1.py`
Expected: FAIL because gate registration is absent.

- [ ] **Step 4: Implement initial repaired-unit descriptors and registration**

Descriptors may contain PR/branch navigation metadata but authority derives only from exact registered payload/code/policy identities and verified receipts. Register missing producers/prerequisites explicitly rather than filling them with synthetic substitutes.

- [ ] **Step 5: Run Task 6 tests GREEN**

Run: `python -m pytest -q tests/v5/td_unified/test_gate_registration_v1.py tests/v5/td_unified/test_registry_v1.py`
Expected: PASS.

- [ ] **Step 6: Commit Task 6**

```bash
git add scripts/v5/td_unified/gate_registration_v1.py tests/v5/td_unified/test_gate_registration_v1.py
git commit -m "feat: register repaired TD units without authority promotion"
```

---

### Task 7: `TARGET_QUALIFICATION_BUNDLE_V1`

**Files:**
- Create: `scripts/v5/td_unified/target_bundle_v1.py`
- Create: `schemas/target_discovery/unified_v1/target_qualification_bundle_v1.json`
- Test: `tests/v5/td_unified/test_target_bundle_v1.py`

**Interfaces:**
- Consumes: exact Task 2 manifest digest; Task 3 registry digest; verified producer/gate/reference/falsifier/controller receipts.
- Produces: `TargetQualificationBundle`; `issue_target_bundle(...) -> TargetQualificationBundle`; `verify_target_bundle(bundle, resolver) -> VerifiedTargetBundle`.

- [ ] **Step 1: Write RED tests for lawful `TARGET=NONE` and selected-target bundles**

```python
def test_target_none_is_first_class_bundle_not_error(): ...
def test_selected_target_bundle_requires_semantics_addresses_support_evidence_estimability_sources_endpoints_receipts_controls_limitations_and_forbidden_interpretations(): ...
def test_bundle_recomputes_manifest_registry_controller_and_parent_receipt_lineage(): ...
def test_bundle_cannot_claim_scope_beyond_qualified_support_or_estimability(): ...
```

- [ ] **Step 2: Run Task 7 tests and preserve RED**

Run: `python -m pytest -q tests/v5/td_unified/test_target_bundle_v1.py`
Expected: FAIL because target bundle implementation is absent.

- [ ] **Step 3: Implement target bundle issuance and verification**

`TARGET=NONE` still binds manifest/registry/controller/falsifier evidence showing why no target was promoted. A selected target exports inherited negative controls and downstream regression obligations, not just identity.

- [ ] **Step 4: Run Task 7 tests GREEN**

Run: `python -m pytest -q tests/v5/td_unified/test_target_bundle_v1.py tests/v5/td_unified/test_canonical_v1.py`
Expected: PASS.

- [ ] **Step 5: Commit Task 7**

```bash
git add scripts/v5/td_unified/target_bundle_v1.py schemas/target_discovery/unified_v1/target_qualification_bundle_v1.json tests/v5/td_unified/test_target_bundle_v1.py
git commit -m "feat: add immutable TD target qualification bundle"
```

---

### Task 8: `DOWNSTREAM_CERTIFICATION_CONTRACT_V1` exact consumption (A8 RED-first)

**Files:**
- Create: `scripts/v5/td_unified/downstream_contract_v1.py`
- Create: `schemas/target_discovery/unified_v1/downstream_certification_contract_v1.json`
- Test: `tests/v5/td_unified/test_downstream_contract_v1.py`

**Interfaces:**
- Consumes: Task 7 exact verified bundle plus downstream teacher/student/representation/evaluation receipts.
- Produces: `InheritedObligation`; `DownstreamCertificationReceipt`; `certify_downstream_consumption(bundle, execution_receipts, obligation_receipts) -> DownstreamCertificationReceipt`.

- [ ] **Step 1: Write A8 RED tests for exact bundle consumption**

```python
def test_downstream_recomputes_exact_target_bundle_digest(): ...
def test_widened_support_or_estimability_scope_fails_closed(): ...
def test_changed_target_relation_observation_or_evidence_semantics_fails_closed(): ...
def test_dropped_falsifier_or_negative_control_fails_closed(): ...
def test_substituted_producer_executor_reference_or_representation_identity_fails_closed(): ...
def test_every_inherited_obligation_has_an_exercised_test_receipt(): ...
```

- [ ] **Step 2: Write RED tests for permanent historical hostile obligations**

The obligation set must represent normalization/query/hidden-total/support leakage, wrong-cell pairing, donor/source leakage, fake rich teacher, teacher/student oracle confusion, evidence starvation, target-semantics drift, stable-subspace versus unstable-axis interpretation, and unlawful support widening.

- [ ] **Step 3: Run Task 8 tests and preserve RED**

Run: `python -m pytest -q tests/v5/td_unified/test_downstream_contract_v1.py`
Expected: FAIL because downstream contract is absent.

- [ ] **Step 4: Implement exact-consumption certification**

The contract must not implement JEPA training. It validates receipts from the real downstream construction/evaluation path and can advance only to the scope/stage proven by those receipts; it never toggles project training authority.

- [ ] **Step 5: Run Task 8 tests GREEN**

Run: `python -m pytest -q tests/v5/td_unified/test_downstream_contract_v1.py tests/v5/td_unified/test_target_bundle_v1.py`
Expected: PASS.

- [ ] **Step 6: Commit Task 8**

```bash
git add scripts/v5/td_unified/downstream_contract_v1.py schemas/target_discovery/unified_v1/downstream_certification_contract_v1.json tests/v5/td_unified/test_downstream_contract_v1.py
git commit -m "feat: bind downstream certification to exact TD bundle"
```

---

### Task 9: Reusable known-truth challenge families A–I

**Files:**
- Create: `scripts/v5/td_unified/challenge_worlds_v1.py`
- Test: `tests/v5/td_unified/test_challenge_worlds_v1.py`

**Interfaces:**
- Consumes: Task 4 sealed challenge custody; Task 5 CaseBundle/TruthBundle schemas.
- Produces: `ChallengeWorldSpec`; `build_development_world(world_id, identity) -> (KnownTruthCaseBundle, TruthBundle)`; `commit_sealed_world_family(...) -> SealedQualificationCommitment`.

- [ ] **Step 1: Write RED tests for the nine minimum challenge families**

```python
def test_world_a_clean_identifiable_biology_has_no_shortcut_truth_in_casebundle(): ...
def test_world_b_nuisance_only_truth_requires_target_none(): ...
def test_world_c_source_confounded_requires_noncompensation(): ...
def test_world_d_sparse_lawful_truth_requires_not_estimable(): ...
def test_world_e_structural_absence_cannot_zero_fill(): ...
def test_world_f_measurement_artifact_links_counts_and_library_mass(): ...
def test_world_g_leakage_trap_places_shortcut_only_in_observable_channel_under_test(): ...
def test_world_h_stable_subspace_rotating_axes_refuses_axis_interpretation(): ...
def test_world_i_malformed_artifact_preserves_numbers_but_breaks_authority_identity(): ...
```

- [ ] **Step 2: Write RED tests for candidate neutrality and realistic population/support geometry**

World generation must support ragged donor/source/operator/support layouts including source-only addresses, zero-operator addresses, rare donor strata, and source asymmetry without treating those empirical support facts as latent biological truth.

- [ ] **Step 3: Run Task 9 tests and preserve RED**

Run: `python -m pytest -q tests/v5/td_unified/test_challenge_worlds_v1.py`
Expected: FAIL because challenge worlds are absent.

- [ ] **Step 4: Implement reusable world specifications/generation contracts**

Use identity-keyed RNG and shared observation semantics from retained Tasks 1–3. Development worlds are inspectable; final qualification worlds are generated/held under Task 4 sealed custody.

- [ ] **Step 5: Run Task 9 tests GREEN**

Run: `python -m pytest -q tests/v5/td_unified/test_challenge_worlds_v1.py tests/v5/td_unified/test_casebundle_v1.py tests/v5/td_unified/test_challenge_custody_v1.py`
Expected: PASS.

- [ ] **Step 6: Commit Task 9**

```bash
git add scripts/v5/td_unified/challenge_worlds_v1.py tests/v5/td_unified/test_challenge_worlds_v1.py
git commit -m "feat: add unified TD known-truth challenge families"
```

---

### Task 10: Full TD known-truth rehearsal through exact registered production units

**Files:**
- Create: `scripts/v5/td_unified/rehearsal_v1.py`
- Test: `tests/v5/td_unified/test_rehearsal_v1.py`
- Modify only if interface adapters are required and separately reviewed: existing `scripts/v5/td_*` modules; do not copy their decision logic into `td_unified`.

**Interfaces:**
- Consumes: manifest, registry, CaseBundle, challenge custody/worlds, exact registered producers/executors, TargetPortfolio/controller interfaces, target-bundle issuer.
- Produces: `TDRehearsalReceipt`; `run_known_truth_rehearsal(manifest, registry, casebundle, unit_resolver, controller) -> TDRehearsalReceipt`.

- [ ] **Step 1: Write RED tests proving incomplete units remain blocked rather than substituted**

```python
def test_rehearsal_refuses_synthetic_analogue_when_registered_producer_is_missing(): ...
def test_rehearsal_cannot_run_unit_above_its_active_registry_stage(): ...
def test_revoked_unit_blocks_pipeline_rehearsal(): ...
```

- [ ] **Step 2: Write RED end-to-end tests for controller semantics**

```python
def test_nuisance_only_world_reaches_real_controller_and_emits_target_none_bundle(): ...
def test_identifiable_world_can_emit_selected_target_bundle_only_when_all_required_units_are_qualified(): ...
def test_sparse_world_preserves_not_estimable_without_false_fail_or_forced_winner(): ...
def test_source_confounded_world_cannot_be_rescued_by_pooling(): ...
def test_malformed_artifact_dies_before_controller_authority(): ...
def test_numerical_failure_never_becomes_biological_fail_or_lawful_abstention(): ...
```

If current unit stages make the identifiable-target rehearsal impossible, the test must assert a lawful blocked prerequisite state rather than fabricate promotion. The first complete selected-target run occurs only after required units receive real promotion receipts.

- [ ] **Step 3: Run Task 10 tests and preserve RED**

Run: `python -m pytest -q tests/v5/td_unified/test_rehearsal_v1.py`
Expected: FAIL because rehearsal orchestration is absent.

- [ ] **Step 4: Implement orchestration around exact production interfaces**

The module may route/authenticate/call exact registered production units and the existing TD controller. It may not reimplement gate arithmetic, support laws, thresholds, falsifiers, TargetPortfolio rules, or winner selection.

- [ ] **Step 5: Add independent truth adjudication after output freeze**

Truth adjudication compares the frozen rehearsal/controller/Target Qualification Bundle output to the external TruthBundle. It cannot repair, rerun, seed-shop, replace worlds, or change registry stages during the run.

- [ ] **Step 6: Run Task 10 tests GREEN at the authority currently available**

Run: `python -m pytest -q tests/v5/td_unified/test_rehearsal_v1.py tests/v5/td_unified/test_gate_registration_v1.py`
Expected: PASS, including lawful blocked outcomes for units not yet promotable.

- [ ] **Step 7: Commit Task 10**

```bash
git add scripts/v5/td_unified/rehearsal_v1.py tests/v5/td_unified/test_rehearsal_v1.py
git commit -m "feat: add unified TD known-truth rehearsal orchestration"
```

---

### Task 11: Finalization, generated receipts and unified CI

**Files:**
- Create: `scripts/v5/td_unified/finalizer_v1.py`
- Create: `tests/v5/td_unified/test_finalizer_v1.py`
- Create: `.github/workflows/td-unified-qualification-v1.yml`
- Generate only after tests pass: `results/target_discovery/unified_qualification_v1/**`

**Interfaces:**
- Consumes: all prior tasks.
- Produces: canonical manifest/registry/challenge/equivalence/rehearsal/bundle/downstream receipt index plus authority snapshot; no candidate outcome artifact.

- [ ] **Step 1: Write RED tests for finalizer fail-closed custody**

```python
def test_finalizer_recomputes_every_payload_and_parent_digest(): ...
def test_finalizer_rejects_revoked_or_moved_dependencies(): ...
def test_finalizer_rejects_unrevealed_or_mismatched_sealed_exam_commitment(): ...
def test_finalizer_records_unsatisfied_real_prerequisites_instead_of_promoting_them(): ...
def test_finalizer_global_authority_remains_off(): ...
```

- [ ] **Step 2: Run finalizer tests and preserve RED**

Run: `python -m pytest -q tests/v5/td_unified/test_finalizer_v1.py`
Expected: FAIL because finalizer/workflow is absent.

- [ ] **Step 3: Implement `finalizer_v1.py`**

Emit canonical receipt index with exact design head `3064ca545f0c94859ea989cd49a04fcbd5b9a303`, exact accepted architecture file digests, exact current manifest/registry identities, active/revoked status, unsatisfied prerequisites, challenge custody state, and global authority false.

- [ ] **Step 4: Add unified GitHub Actions workflow**

Workflow must run all `tests/v5/td_unified/` tests, then existing exact-head regression/adapter tests required by the registered manifest, then finalizer validation. It must not download/open human candidate outcomes or protected validation/oracle values.

- [ ] **Step 5: Run the complete local unified suite GREEN**

Run: `python -m pytest -q tests/v5/td_unified`
Expected: PASS.

- [ ] **Step 6: Run focused regressions for currently registered repair surfaces**

Run the exact test files required by the manifest for #364–#369-era registered evidence. Expected: PASS without changing their scientific code or authority classification.

- [ ] **Step 7: Generate non-human unified qualification receipts**

Generate only manifests/registries/custody/equivalence/rehearsal diagnostic receipts that are lawful at current stages. Do not emit a human execution receipt or claim `REAL_REFERENCE_READY` unless the prerequisite graph proves it.

- [ ] **Step 8: Re-run finalizer validation on generated bytes**

Run: `python -m pytest -q tests/v5/td_unified/test_finalizer_v1.py`
Expected: PASS using the exact generated receipt bytes.

- [ ] **Step 9: Commit Task 11**

```bash
git add scripts/v5/td_unified/finalizer_v1.py tests/v5/td_unified/test_finalizer_v1.py .github/workflows/td-unified-qualification-v1.yml results/target_discovery/unified_qualification_v1
git commit -m "ci: qualify unified TD custody pipeline"
```

---

### Task 12: Whole-pipeline hostile review checkpoint before any human execution plan

**Files:**
- Create after independent review: `docs/agent/UNIFIED_TD_QUALIFICATION_V1_IMPLEMENTATION_AUDIT_<DATE>.md`
- No production code changes in the audit commit unless defects are found; defects return to the owning task and create new reviewed identities.

**Interfaces:**
- Consumes: exact branch head, Task 11 receipts/workflow evidence.
- Produces: independent implementation-audit verdict only.

- [ ] **Step 1: Freeze the exact implementation head and receipt index for review**

Record commit, tree, workflow run, canonical receipt-index digest, manifest digest, registry digest, and design head.

- [ ] **Step 2: Independently audit A1–A9 against executable evidence**

The reviewer must specifically attempt digest forgery, stale-receipt reuse, post-exposure retuning, protected-partition access, self-qualification, hidden missing prerequisites, mode-dependent branching, downstream semantic widening, and authority-scope escalation.

- [ ] **Step 3: Independently audit initial gate classifications**

Confirm every current repaired unit is at or below demonstrated stage and that #369/system battery does not promote constituent units by association.

- [ ] **Step 4: Independently audit rehearsal semantics**

Require a lawful `TARGET=NONE`/blocked demonstration at current authority and verify selected-target rehearsal cannot run until its prerequisite units are actually promoted.

- [ ] **Step 5: Publish the audit receipt and stop**

No human candidate outcomes, real tournament execution, or training authorization follows automatically. Any next human-execution step requires a separate owner-approved authority transition under the registry/manifest system.

---

## A1–A9 Test Coverage Matrix

| Amendment | RED-first owning task | Required proof before GREEN |
|---|---|---|
| A1 canonical authentication | Task 1 | recomputation + recursive parent verification; SHA strings alone fail |
| A2 revocation/supersession | Task 3 | immutable history + stale active authority unusable |
| A3 sealed final qualification | Task 4 | development/final split, hidden holdout, no retuning/replacement |
| A4 population/access law | Task 2 | `reader_fit` cross-fitting; validation/oracle protected; actual access receipts |
| A5 independent qualification | Task 3 | self-qualification impossible; distinct controller/reviewer receipts |
| A6 dependency-complete readiness | Task 3 | every prerequisite explicit/active/current; no coarse ready override |
| A7 mode path equivalence | Task 5 | executable trace equality; mode scientific branch invalidates SAME_CODE_PATH |
| A8 downstream exact consumption | Task 8 | exact bundle digest + all inherited obligations exercised unchanged |
| A9 one authority model | Task 1 | one ordered stage + orthogonal lineage + scope; no competing enums |

## Required Stop Gates During Implementation

- **STOP U1 — before any sealed final known-truth qualification exposure:** requires owner/controller authorization after development tests and challenge commitment are frozen.
- **STOP U2 — before any promotion to `KNOWN_TRUTH_QUALIFIED`:** requires independent adjudication/review receipt satisfying A3/A5/A7.
- **STOP U3 — before any promotion to `REAL_REFERENCE_READY`:** requires the complete A6 prerequisite graph to be active and exact.
- **STOP U4 — before any human candidate execution:** requires a frozen manifest, `HUMAN_EXECUTABLE` active unit states, current-TD access policy, and separate owner authorization.
- **STOP U5 — before downstream `TRAINING_ELIGIBLE` or any project training authorization:** requires exact Target Qualification Bundle consumption and downstream certification; `TRAINING_AUTHORIZED` remains a separate explicit owner decision.

## Plan Self-Review Result

- **Spec coverage:** V1 §§0–18 and V1.1 A1–A9 map to Tasks 1–12; no old synthetic Tasks 4–12 execution authority remains.
- **Step scan:** each implementation task is RED test → RED run → one implementation action → GREEN run → commit; complex authority domains are separated at fresh-review boundaries.
- **Type consistency:** canonical identities/authority records flow Task 1 → manifest Task 2 → registry Task 3 → CaseBundle/equivalence Task 5 → registration Task 6 → Target Bundle Task 7 → downstream Task 8 → rehearsal/finalizer Tasks 10–11.
- **Review Focus:** all five high-risk classes are explicitly tested in their owning tasks.
- **Proportion:** the plan fixes interfaces, files, tests and authority decisions but leaves function bodies/algorithms to implementers except where the spec pins exact state/order semantics.

## Execution Boundary

This plan authorizes implementation planning only until it is reviewed. It does not itself authorize Task 1 implementation, sealed challenge exposure, human execution, target/representation selection, TD60, Stage4, or training.
