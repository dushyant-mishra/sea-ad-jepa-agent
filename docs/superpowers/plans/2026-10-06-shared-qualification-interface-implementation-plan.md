# Shared Qualification Interface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the machine-enforced shared qualification interface used by both future real-RNA qualification and V77/S127 synthetic qualification, without adding any training authority or runtime mutation path.

**Architecture:** Add a small, dependency-light `sea_ad_jepa.qualification` package that binds the exact merged PR #220 governance state and represents scientific protocol, visibility, feature identity, immutable batch identity, run lifecycle, authorities, q-safety, oracle unblinding, and provenance. This slice deliberately stops before #221/#222 runtime convergence and before implementing real or synthetic dataset adapters; it defines the interface those later plans must consume.

**Tech Stack:** Python >=3.11, standard-library `dataclasses`, `enum`, `hashlib`, `json`, `typing`, pytest; no new runtime dependencies.

**Spec:** `docs/agent/JEPA_SHARED_QUALIFICATION_PIPELINE_DESIGN_20261006.md` plus `docs/agent/JEPA_SHARED_QUALIFICATION_PIPELINE_FINAL_SAFEGUARDS_20261006.md` and the lifecycle correction recorded after that addendum.

## Global Constraints

- Scientific governance source is merged PR #220 at `main@f5a8ebeddbcd52a94274a7f72ecda1f71b82d777`.
- Bind the approved canonical V3 governance digest `ab0603b0a9c92c3680badc252205ddd27fa74ae83ef3ada4019b4dcf637b7611`; any successor governance requires an explicit successor protocol/version.
- `TRAINING=OFF`; `STAGE_A_EXECUTION=OFF`; `MULTIMODAL_TRAINING=OFF`; `500K=NOT_AUTHORIZED`; `STAGE4=NOT_AUTHORIZED`; `TEST=SEALED`; `MORABITO=PROTECTED`.
- No target winner, representation winner, estimand, biological dimensionality, or deciding real-data numeric threshold may be selected by this implementation.
- `width=160` is model capacity only and must not appear as scientific-dimensionality authority.
- Zero-update qualification is the default and must be implementable without importing the optimizer/runtime reconciliation modules.
- Oracle/evaluation information must remain physically downstream of ordinary qualification outputs.
- Every future change must be classifiable as science, mechanics, or both; this package owns scientific-interface mechanics only, not model optimization mechanics.
- Preserve historical negative findings and do not import V64/E2 scientific authority or historical checkpoints as current authority.

## Review Focus

1. **Derived visibility laundering:** a `SPLIT_ONLY`, `READOUT_ONLY`, `PROVENANCE_ONLY`, or `ORACLE_ONLY` parent must not be transformed into a model/preprocessing-visible descendant.
2. **Scientific identity under repacking:** microbatching/sharding/sparse-dense conversion/device or token packing must not change `batch_scientific_identity_digest`, while semantic content changes must.
3. **Authority collapse:** valid scientific experiment authority must not grant mutation authority; mechanics success must not elevate claim authority.
4. **Oracle feedback:** unblinding before frozen ordinary outputs, or retuning after unblinding, must fail/reclassify the result rather than remain prospective evidence.
5. **Pseudoreplication / identity mismatch:** feature-identity receipt mismatches and treating cells as independent biological units when the protocol declares donor-level inference must fail closed.

---

## File Structure

Create a new focused package:

- `src/sea_ad_jepa/qualification/__init__.py` — public non-authorizing interface exports only.
- `src/sea_ad_jepa/qualification/canonical.py` — deterministic canonical JSON/digest helpers.
- `src/sea_ad_jepa/qualification/protocol.py` — `QualificationProtocol`, execution mode, threshold status, representation roster, governance/runtime compatibility declarations.
- `src/sea_ad_jepa/qualification/visibility.py` — visibility classes, derived-field lineage and transitive firewall.
- `src/sea_ad_jepa/qualification/identity.py` — `FeatureIdentityReceipt`, `QualificationBatchIdentity`, scientific-vs-packing digest rules.
- `src/sea_ad_jepa/qualification/authorities.py` — three independent authority records and non-escalation validation.
- `src/sea_ad_jepa/qualification/lifecycle.py` — run identity, mode-aware state machine, failure states and event attachment rules.
- `src/sea_ad_jepa/qualification/oracle.py` — sealed oracle handle/unblinding receipt and one-way evaluation boundary.
- `src/sea_ad_jepa/qualification/qsafe.py` — machine-readable q-safety policy and required negative-control roster.
- `src/sea_ad_jepa/qualification/receipts.py` — end-to-end ordinary qualification/provenance receipt.

Tests:

- `tests/qualification/test_protocol_v1.py`
- `tests/qualification/test_visibility_v1.py`
- `tests/qualification/test_identity_v1.py`
- `tests/qualification/test_authorities_v1.py`
- `tests/qualification/test_lifecycle_v1.py`
- `tests/qualification/test_oracle_v1.py`
- `tests/qualification/test_qsafe_v1.py`
- `tests/qualification/test_receipts_v1.py`

CI:

- `.github/workflows/shared-qualification-interface-v1.yml`

Do not modify `src/sea_ad_jepa/v5/inactive_update_reference.py`, PR #221 guard code, or PR #222 guard code in this plan.

---

### Task 1: Canonical digests and exact-governance-bound `QualificationProtocol`

**Files:**
- Create: `src/sea_ad_jepa/qualification/__init__.py`
- Create: `src/sea_ad_jepa/qualification/canonical.py`
- Create: `src/sea_ad_jepa/qualification/protocol.py`
- Test: `tests/qualification/test_protocol_v1.py`

**Interfaces:**
- Produces: `canonical_digest(value: object) -> str`
- Produces: `ExecutionMode` with exactly `ZERO_UPDATE_QUALIFICATION`, `BOUNDED_MUTATION_REHEARSAL`
- Produces: `ThresholdStatus` with deciding/exploratory/unset fail-closed vocabulary
- Produces: frozen `QualificationProtocolV1` dataclass with `validate() -> None` and `digest() -> str`

- [ ] **Step 1: Write RED tests for exact governance binding and neutral scientific choices**

Tests must assert that a valid protocol binds the exact V3 digest, one of the four PR #220 representation families, explicit q-safety/operator/split/stability identifiers, explicit unit of inference, explicit estimand/threshold state, execution mode, claim ceiling, and protocol/runtime interface version fields. Mutating the governance digest, inventing a fifth representation family, selecting a real-data threshold while status is UNSET, or omitting the execution mode must fail.

- [ ] **Step 2: Run the focused RED tests**

Run: `python -m pytest -q tests/qualification/test_protocol_v1.py`
Expected: FAIL because package/interfaces do not exist.

- [ ] **Step 3: Implement canonical digesting and `QualificationProtocolV1` minimally**

Use sorted-key compact JSON for semantic digesting; reject non-finite floats and unsupported opaque objects rather than stringifying them. Keep unresolved science explicit (`UNSET_REQUIRES_APPROVAL`) instead of supplying defaults.

- [ ] **Step 4: Run GREEN tests**

Run: `python -m pytest -q tests/qualification/test_protocol_v1.py tests/governance/test_premise_qualification_v3_surface.py tests/governance/test_stage_a_v3_machine_contract.py`
Expected: all PASS; PR #220 governance tests remain unchanged.

- [ ] **Step 5: Commit**

`git commit -m "feat: bind shared qualification protocol to V3 governance"`

---

### Task 2: Visibility classes and transitive derived-feature firewall

**Files:**
- Create: `src/sea_ad_jepa/qualification/visibility.py`
- Test: `tests/qualification/test_visibility_v1.py`

**Interfaces:**
- Produces: `VisibilityClass` with exactly `MODEL_VISIBLE`, `PREPROCESSING_VISIBLE`, `LAWFUL_OPERATOR_CONTEXT`, `SPLIT_ONLY`, `READOUT_ONLY`, `PROVENANCE_ONLY`, `ORACLE_ONLY`
- Produces: frozen `FieldDeclaration(name, visibility, parent_names=())`
- Produces: `derive_field_visibility(child_name: str, parents: tuple[FieldDeclaration, ...], requested: VisibilityClass) -> FieldDeclaration`
- Produces: `assert_model_visible(field: FieldDeclaration) -> None`
- Produces: `assert_preprocessing_visible(field: FieldDeclaration) -> None`

- [ ] **Step 1: Write RED tests for raw and derived visibility escape attempts**

Include attempts to hash/aggregate/rename `SPLIT_ONLY` donor ID and `ORACLE_ONLY z_reg_private` into a model-visible feature. Include a lawful derivation from only `MODEL_VISIBLE` parents and a lawful operator-context path that remains operator-context rather than becoming unrestricted model input.

- [ ] **Step 2: Run RED**

Run: `python -m pytest -q tests/qualification/test_visibility_v1.py`
Expected: FAIL.

- [ ] **Step 3: Implement strictest-parent inheritance with no implicit declassification**

Declassification is not implemented in V1. If requested visibility is less restrictive than any parent, raise `VisibilityViolation`.

- [ ] **Step 4: Run GREEN**

Run: `python -m pytest -q tests/qualification/test_visibility_v1.py`
Expected: PASS.

- [ ] **Step 5: Commit**

`git commit -m "feat: enforce transitive qualification visibility firewall"`

---

### Task 3: Feature identity and immutable scientific batch identity

**Files:**
- Create: `src/sea_ad_jepa/qualification/identity.py`
- Test: `tests/qualification/test_identity_v1.py`

**Interfaces:**
- Produces: frozen `FeatureIdentityReceiptV1(registry_digest, ordering_digest, reader_mapping_digest, tokenizer_mapping_digest, tensor_feature_axis_digest, synthetic: bool)` with `validate()` and `digest()`
- Produces: frozen `QualificationBatchIdentityV1(observation_ids, feature_receipt_digest, query_spec_digest, evidence_mask_digest, measurement_mask_digest, operator_context_digest, evaluation_weight_digest, grouping_digest, split_digest, target_spec_digest)` with `digest()`
- Produces: `PackingReceiptV1(scientific_identity_digest, packing_digest)`

- [ ] **Step 1: Write RED tests for feature-chain mismatches and packing invariance**

Require mismatch between tokenizer mapping and tensor feature axis to fail. Build two packing receipts with different microbatch/device/sparse-dense packing but identical scientific identity and assert the scientific digest is unchanged. Change observation membership, query mask, grouping, or scientific weights and assert the scientific digest changes.

- [ ] **Step 2: Run RED**

Run: `python -m pytest -q tests/qualification/test_identity_v1.py`
Expected: FAIL.

- [ ] **Step 3: Implement identity records and explicit chain validation**

Do not infer semantic equality from shape or byte count. `FeatureIdentityReceiptV1.validate()` requires all component digests and a declared check that the tensor feature-axis digest corresponds to the tokenizer/registry mapping supplied by the adapter.

- [ ] **Step 4: Run GREEN**

Run: `python -m pytest -q tests/qualification/test_identity_v1.py`
Expected: PASS.

- [ ] **Step 5: Commit**

`git commit -m "feat: add feature and scientific batch identity receipts"`

---

### Task 4: Three independent authorities and execution-mode firewall

**Files:**
- Create: `src/sea_ad_jepa/qualification/authorities.py`
- Test: `tests/qualification/test_authorities_v1.py`

**Interfaces:**
- Produces: frozen `ScientificExperimentAuthorityV1`
- Produces: frozen `MutationAuthorityV1` with status including `MUTATION_NOT_AUTHORIZED` and narrow authorized status for future use
- Produces: frozen `ClaimAuthorityV1` with maximum claim level
- Produces: `AuthorityBundleV1.validate_against(protocol: QualificationProtocolV1) -> None`

- [ ] **Step 1: Write RED tests for authority escalation**

Valid experiment authority + mutation OFF must reject any mutation-enabled event. Successful mechanics/mutation authority must not increase `ClaimAuthorityV1`. Synthetic claim authority cannot exceed the protocol claim ceiling or auto-promote to real biological state.

- [ ] **Step 2: Run RED**

Run: `python -m pytest -q tests/qualification/test_authorities_v1.py`
Expected: FAIL.

- [ ] **Step 3: Implement independent digests/statuses and cross-validation**

No method may derive one authority from success of another. `ZERO_UPDATE_QUALIFICATION` requires mutation OFF.

- [ ] **Step 4: Run GREEN**

Run: `python -m pytest -q tests/qualification/test_authorities_v1.py`
Expected: PASS.

- [ ] **Step 5: Commit**

`git commit -m "feat: separate experiment mutation and claim authorities"`

---

### Task 5: Monotonic run identity and failure-contained lifecycle

**Files:**
- Create: `src/sea_ad_jepa/qualification/lifecycle.py`
- Test: `tests/qualification/test_lifecycle_v1.py`

**Interfaces:**
- Produces: `RunMode` derived from `ExecutionMode`
- Produces: lifecycle states supporting zero-update `NOT_STARTED -> PREPARED -> QUALIFICATION_OUTPUTS_FROZEN -> VERIFIED`
- Produces: mutation states `PREPARED -> MUTATED -> EMA_APPLIED -> CHECKPOINTED -> QUALIFICATION_OUTPUTS_FROZEN -> VERIFIED`
- Produces: `ExperimentRunV1(experiment_run_id, protocol_digest, mode, state, parent_run_id=None)` with explicit event methods
- Produces terminal failure record carrying last proven state and reason

- [ ] **Step 1: Write RED tests for illegal jumps, cross-run events, partial failure and retry ambiguity**

Include `PREPARED -> EMA_APPLIED` without mutation, mutation event under zero-update mode, optimizer success then checkpoint failure, restart verification failure, and attaching an event from a different `experiment_run_id`.

- [ ] **Step 2: Run RED**

Run: `python -m pytest -q tests/qualification/test_lifecycle_v1.py`
Expected: FAIL.

- [ ] **Step 3: Implement state transitions as explicit methods only**

No arbitrary `set_state`. Failure is terminal for that run; retry creates a child run with `parent_run_id` and explicit reason.

- [ ] **Step 4: Run GREEN**

Run: `python -m pytest -q tests/qualification/test_lifecycle_v1.py`
Expected: PASS.

- [ ] **Step 5: Commit**

`git commit -m "feat: add fail-closed qualification run lifecycle"`

---

### Task 6: Q-safety policy and required synthetic negative-control contract

**Files:**
- Create: `src/sea_ad_jepa/qualification/qsafe.py`
- Test: `tests/qualification/test_qsafe_v1.py`

**Interfaces:**
- Produces: frozen `QSafetyPolicyV1` with required forbidden descendant channels: query value, normalization denominator, library-size summary, detected-feature summary, QC descendants, support/missingness, mask construction, query-dependent preprocessing, target/teacher pre-context
- Produces: `NegativeControlArm` vocabulary for clean negative, technical/operator shortcut, planted recoverable biological, planted inaccessible/private-state, query-leak
- Produces: `SyntheticControlRosterV1.validate(required_for_protocol: ...)`

- [ ] **Step 1: Write RED tests for weakened q-safety and missing controls**

Deleting any required descendant channel from the policy must fail. A serious synthetic protocol missing private-state or query-leak control when applicable must be incomplete, not PASS.

- [ ] **Step 2: Run RED**

Run: `python -m pytest -q tests/qualification/test_qsafe_v1.py`
Expected: FAIL.

- [ ] **Step 3: Implement exact policy roster and applicability-aware control validation**

Keep this task declarative: it defines what later preprocessing must prove; it does not implement RNA normalization itself.

- [ ] **Step 4: Run GREEN**

Run: `python -m pytest -q tests/qualification/test_qsafe_v1.py`
Expected: PASS.

- [ ] **Step 5: Commit**

`git commit -m "feat: bind transitive q-safety and synthetic controls"`

---

### Task 7: One-way synthetic oracle unblinding

**Files:**
- Create: `src/sea_ad_jepa/qualification/oracle.py`
- Test: `tests/qualification/test_oracle_v1.py`

**Interfaces:**
- Produces: opaque `SyntheticOracleTruthV1` data holder that is not accepted by protocol/batch/preprocessing interfaces
- Produces: frozen `FrozenQualificationOutputsV1(run_id, output_digest, provenance_receipt_digest)`
- Produces: `OracleUnblindingReceiptV1(run_id, output_digest, oracle_digest, challenge_status)`
- Produces: `unblind_oracle(run: ExperimentRunV1, frozen_outputs: FrozenQualificationOutputsV1, oracle: SyntheticOracleTruthV1) -> OracleUnblindingReceiptV1`
- Produces: challenge status transition to development/calibration if same-run deciding configuration changes after unblinding

- [ ] **Step 1: Write RED tests for early unblinding and feedback**

Oracle cannot unblind before `QUALIFICATION_OUTPUTS_FROZEN`. A receipt with a different run ID is rejected. Post-unblinding threshold/diagnostic configuration mutation cannot remain sealed prospective challenge evidence.

- [ ] **Step 2: Run RED**

Run: `python -m pytest -q tests/qualification/test_oracle_v1.py`
Expected: FAIL.

- [ ] **Step 3: Implement downstream-only unblinding receipt**

Oracle evaluation returns only evaluation artifacts/receipts; it exposes no callback into model/preprocessing/runtime code.

- [ ] **Step 4: Run GREEN**

Run: `python -m pytest -q tests/qualification/test_oracle_v1.py`
Expected: PASS.

- [ ] **Step 5: Commit**

`git commit -m "feat: enforce one-way synthetic oracle unblinding"`

---

### Task 8: End-to-end provenance receipt and zero-update qualification skeleton

**Files:**
- Create: `src/sea_ad_jepa/qualification/receipts.py`
- Create: `src/sea_ad_jepa/qualification/pipeline.py`
- Test: `tests/qualification/test_receipts_v1.py`
- Test: `tests/qualification/test_zero_update_pipeline_v1.py`

**Interfaces:**
- Produces: `QualificationProvenanceReceiptV1` binding governance, protocol, adapter, feature identity, preprocessing/q-safety, representation request, target/evidence, operator policy, split/unit/estimand, threshold status, runtime identity if any, checkpoint if any, environment/code identity, synthetic realization/challenge partition when applicable
- Produces: `QualificationBatchV1` that holds typed groups/field declarations and `QualificationBatchIdentityV1`
- Produces: `run_zero_update_qualification(protocol, authorities, batch, representation_fn, readout_fn) -> FrozenQualificationOutputsV1`

- [ ] **Step 1: Write RED tests for missing provenance, pseudoreplication, visibility escape and mutation attempt**

A deciding receipt missing feature identity or unit of inference must fail. Donor-level protocol with cell-only aggregation metadata must fail. The zero-update skeleton must reject a representation/readout callback that attempts to emit a mutation/EMA event or consume forbidden visibility.

- [ ] **Step 2: Run RED**

Run: `python -m pytest -q tests/qualification/test_receipts_v1.py tests/qualification/test_zero_update_pipeline_v1.py`
Expected: FAIL.

- [ ] **Step 3: Implement the smallest zero-update orchestration boundary**

Do not import `torch`, optimizer modules, PR #221 or PR #222 runtime code. The pipeline validates protocol/authorities/batch, executes caller-supplied frozen representation/readout functions over explicitly model-visible data, freezes outputs, and emits provenance.

- [ ] **Step 4: Run GREEN plus governance regression suite**

Run: `python -m pytest -q tests/qualification tests/governance/test_premise_qualification_v3_surface.py tests/governance/test_stage_a_v3_machine_contract.py`
Expected: all PASS.

- [ ] **Step 5: Commit**

`git commit -m "feat: add zero-update shared qualification boundary"`

---

### Task 9: Focused CI and independent spillover scan

**Files:**
- Create: `.github/workflows/shared-qualification-interface-v1.yml`
- Create: `docs/agent/JEPA_SHARED_QUALIFICATION_INTERFACE_V1_AUDIT_20261006.md`
- Test: all `tests/qualification/*` plus PR #220 governance tests

**Interfaces:**
- Produces no new runtime API; establishes exact-head evidence.

- [ ] **Step 1: Add CI triggers for qualification package/tests, binding design docs, PR #220 governance state/validator, and workflow itself**

Use Python 3.12 and install only pytest for this interface slice.

- [ ] **Step 2: Run focused suite locally/CI and record exact RED→GREEN history**

Run: `python -m pytest -q tests/qualification tests/governance/test_premise_qualification_v3_surface.py tests/governance/test_stage_a_v3_machine_contract.py`
Expected: PASS.

- [ ] **Step 3: Perform semantic historical-spillover audit**

Search the new package and tests for V64/E2 authority, target winner, width-160 biological semantics, old residual-target rescue, T_A/T_B biological promotion, calibration-closure operator loss, protected TEST/Morabito use, implicit estimand/threshold defaults, and runtime optimizer/EMA imports. Record findings even when negative.

- [ ] **Step 4: Audit design coverage and exact-head claims**

Confirm all interface safeguards are represented by tests and that no claim says the runtime, synthetic adapter, real adapter, Stage A, or training is qualified by this slice.

- [ ] **Step 5: Commit**

`git commit -m "test: qualify shared interface surface without execution authority"`

---

## Deferred to Separate Plans

The following are intentionally **not** part of this implementation plan and must receive their own RED-first plans after this interface is reviewed:

1. **PR #221/#222 runtime convergence plan:** one canonical inactive PyTorch consumer; actual AdamW; GradScaler skipped-step proof; optimizer provenance/ownership; checkpoint persistence/completeness; interrupt/resume equivalence; terminal reconciliation receipt and donor-PR supersession.
2. **V77/S127 synthetic adapter/challenge plan:** CSR -> `QualificationBatchV1`; authenticated synthetic feature registry; separate `SyntheticOracleTruthV1`; development vs sealed challenge partition; q-leak/B3/B6/operator controls; zero-update first; bounded mutation only under separate authority.
3. **Future real-RNA adapter/execution plan:** complete 41,238 registry -> ordering -> reader/index -> tokenizer -> model tensor authentication; actual Stage-A authority; representation/estimand/threshold decisions only when separately approved.

## Self-Review

- **Spec coverage:** protocol versioning, visibility, feature identity, scientific identity, q-safety, zero-update mode, three authorities, lifecycle, oracle unblinding, negative controls, provenance and unit-of-inference are each owned by a task. Runtime convergence and adapters are explicitly deferred rather than silently omitted.
- **Step scan:** each task follows RED -> observed failure -> minimum implementation -> GREEN -> commit; no task requires inventing unresolved scientific values.
- **Type consistency:** `QualificationProtocolV1`, `QualificationBatchIdentityV1`, `ExperimentRunV1`, `AuthorityBundleV1`, `FrozenQualificationOutputsV1`, and provenance/oracle receipts are introduced before downstream use.
- **Review Focus coverage:** derived visibility (Task 2/8), repacking identity (Task 3), authority collapse (Task 4), oracle feedback (Task 7), pseudoreplication/feature identity (Task 3/8).
- **Proportion:** this plan defines interfaces/tests and stops before writing model/runtime/adapter implementations; it does not duplicate the design spec or prescribe algorithm bodies beyond deterministic digesting and state-transition constraints.
