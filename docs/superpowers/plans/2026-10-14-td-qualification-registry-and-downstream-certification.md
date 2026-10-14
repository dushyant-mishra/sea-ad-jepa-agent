# TD Qualification Registry and Downstream Certification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one executable chain of custody from known-truth qualification through real TD gate execution to an immutable downstream Target Qualification Bundle and downstream certification handoff.

**Architecture:** Add a machine-readable qualification registry as the only source of gate authority metadata, generate exact execution manifests from it, validate a common real-shaped CaseBundle with controller-only truth separation, build immutable target qualification bundles, and validate downstream teacher/student certification receipts. Existing gate logic remains untouched; this layer binds and routes exact identities rather than cloning scientific rules.

**Tech Stack:** Python 3.11, JSON, pytest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-14-td-qualification-registry-and-downstream-certification.md`

## Global Constraints

- Human candidate outcomes remain sealed.
- Synthetic outcomes never set human thresholds.
- Current authority remains `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
- Registry identities must use exact immutable commit/path/receipt identities; branch names are navigation only.
- `HUMAN_EXECUTABLE` cannot be inferred from green CI alone.
- Controller-only synthetic truth must never enter executor-visible inputs.

## Review Focus

- Registry lifecycle skipping must fail closed.
- Missing producer/reference identities must block `HUMAN_EXECUTABLE`.
- Synthetic truth leakage into executor-visible bundles must be rejected.
- `NO_WINNER` must remain a valid immutable target bundle outcome.
- Downstream certification completion must not itself flip real-training authority.

---

### Task 1: Qualification Registry and Validator

**Files:**
- Create: `results/target_discovery/qualification/TD_QUALIFICATION_REGISTRY_V1.json`
- Create: `scripts/v5/td_qualification_registry_v1.py`
- Test: `tests/v5/test_td_qualification_registry_v1.py`

**Interfaces:**
- Consumes: exact repaired gate commit/path/receipt identities.
- Produces: `load_registry() -> dict`, `validate_registry(registry: dict) -> dict`, `gate_state(registry, gate_id) -> str`.

- [ ] Write failing tests for lifecycle ordering, exact identity format, missing producer/reference fail-closed behavior, and authority closure.
- [ ] Run focused test and preserve RED.
- [ ] Implement minimal validator and current registry entries.
- [ ] Run focused test GREEN and authority guard.
- [ ] Commit.

### Task 2: TD Execution Manifest

**Files:**
- Create: `scripts/v5/td_execution_manifest_v1.py`
- Test: `tests/v5/test_td_execution_manifest_v1.py`

**Interfaces:**
- Consumes: validated registry.
- Produces: `build_execution_manifest(registry, *, mode: str, requested_gates: list[str]) -> dict`.

- [ ] RED tests: synthetic rehearsal accepts qualified mechanics; human mode rejects unresolved producer/reference dependencies; manifest binds exact registry identity and cannot use branch tips.
- [ ] Implement minimal generator.
- [ ] GREEN focused tests.
- [ ] Commit.

### Task 3: Common Gate-Facing CaseBundle

**Files:**
- Create: `scripts/v5/td_case_bundle_v1.py`
- Test: `tests/v5/test_td_case_bundle_v1.py`

**Interfaces:**
- Produces: `validate_executor_case(bundle: dict) -> dict`, `bind_controller_truth(executor_case: dict, truth: dict) -> dict`.

- [ ] RED tests: reject truth/synthetic labels in executor view; preserve donor/source/operator/support/evidence/count-library identities; controller truth remains separate.
- [ ] Implement minimal schema validator and controller wrapper.
- [ ] GREEN focused tests.
- [ ] Commit.

### Task 4: Immutable Target Qualification Bundle

**Files:**
- Create: `scripts/v5/td_target_qualification_bundle_v1.py`
- Test: `tests/v5/test_td_target_qualification_bundle_v1.py`

**Interfaces:**
- Consumes: authenticated tournament output, execution manifest, gate receipts, support/evidence/reference policy identities.
- Produces: `build_target_qualification_bundle(...) -> dict`.

- [ ] RED tests: selected candidate or `NONE`; exact receipt identity closure; no missing limitations; bundle hash changes on scientific-field mutation; all authority false.
- [ ] Implement canonical bundle and digest.
- [ ] GREEN focused tests.
- [ ] Commit.

### Task 5: Downstream JEPA Certification Handoff

**Files:**
- Create: `scripts/v5/td_downstream_certification_v1.py`
- Test: `tests/v5/test_td_downstream_certification_v1.py`

**Interfaces:**
- Consumes: immutable target bundle plus teacher/student certification receipts.
- Produces: `validate_downstream_certification(...) -> dict`.

- [ ] RED tests for hidden-target/query/totals/support/normalization leakage, source-boundary loss, wrong observation operator, and representation-semantic drift.
- [ ] Implement required receipt-family validation.
- [ ] Verify certification completeness never grants real-training authority.
- [ ] Commit.

### Task 6: Sealed Integration Rehearsal and CI

**Files:**
- Create: `tests/v5/test_td_qualification_integration_v1.py`
- Create: `.github/workflows/td-qualification-registry-integration-v1.yml`

**Interfaces:**
- Exercises Tasks 1-5 together with candidate-neutral synthetic fixtures and controller-only truth.

- [ ] RED integration rehearsal before final wiring.
- [ ] Wire exact registry -> manifest -> case -> synthetic truth adjudication -> target bundle -> downstream certification flow.
- [ ] Verify PASS/FAIL/NOT_ESTIMABLE/NUMERICAL_FAILURE and `NO_WINNER` propagation.
- [ ] Run full focused integration suite plus authority guard.
- [ ] Open draft PR and record exact RED/GREEN workflow identities.
