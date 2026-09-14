# V5 Data-Aware Measurement Qualification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the T0-derived course correction executable: FULL104 reconnaissance is explicitly outcome-blind, derived feature lineage is independently sealed, V5 measurement-procedure qualification is required before real D_shared, and local/heavy execution fails closed when the environment cannot prove its tests actually ran.

**Architecture:** Add four small authority modules with narrow responsibilities. Reconnaissance authority defines what may be inspected before D_shared; feature-lineage authority seals a heavy-machine receipt proving the 512-dimensional matrices derive lawfully from authenticated FULL104; measurement-qualification authority freezes and later validates real-geometry positive/negative/difficulty-control evidence; environment preflight validates execution context. A final successor pre-outcome binder may authorize real D_shared only when all upstream artifacts are present and passed; current V2 alone must no longer authorize real D_shared.

**Tech Stack:** Python 3.12, stdlib `hashlib/json/platform/subprocess`, existing `artifact_binding_v1`, pytest, GitHub Actions.

**Spec:** `docs/agent/V5_T0_LESSONS_DATA_AWARE_MEASUREMENT_QUALIFICATION_COURSE_CORRECTION_20260914.md`

## Global Constraints

- T0 remains closed; do not modify the frozen T0 contract.
- No current-V5 D_shared, D_private, D_obs, protected, pathology, checkpoint-outcome, TD60, or relational-target result may be accessed by these changes.
- Governing rule: `UNDERSTAND_FULL104_DEEPLY__KEEP_FINAL_D_SHARED_HYPOTHESIS_TEST_SEALED`.
- Historical feature roots are provenance only until derivation is certified.
- Real D_shared outcome access remains false until feature-lineage, FULL104 reconnaissance, measurement-procedure qualification, matching-state discreteness, exact pre-outcome binding, and independent executor review are all closed.
- Tests are RED first, then minimal GREEN implementation.
- Any missing/unknown authority field fails closed.

---

### Task 1: Outcome-blind FULL104 reconnaissance authority

**Files:**
- Create: `docs/agent/V5_FULL104_RECONNAISSANCE_AUTHORITY_V1.json`
- Create: `src/sea_ad_jepa/v5/full104_reconnaissance_authority_v1.py`
- Create: `tests/test_full104_reconnaissance_authority_v1.py`
- Modify: `.github/workflows/v5_dataset_first_production_closure.yml`
- Modify: `tests/v5_critical_test_manifest_v1.json`

**Interfaces:**
- Produces: `validate_full104_reconnaissance_authority_v1(authority) -> dict`, `seal_full104_reconnaissance_receipt_v1(authority, receipt) -> dict`, `validate_full104_reconnaissance_receipt_v1(envelope) -> dict`.
- The authority allowlists structural diagnostics and explicitly forbids decision-bearing D_shared quantities/rank information.

- [ ] **Step 1: Write failing tests** proving the module/artifact exist; all required structural diagnostics are allowlisted; D_shared outcome fields are forbidden; receipts require authenticated FULL104 geometry and `d_shared_outcomes_inspected=false`; sealing/validation round-trips.
- [ ] **Step 2: Push tests and verify RED** in GitHub Actions because module/artifact are absent.
- [ ] **Step 3: Implement minimal authority/module/artifact** using existing `seal_artifact`/`validate_artifact` patterns.
- [ ] **Step 4: Add suite to workflow and critical manifest, then verify GREEN** with no skipped critical tests.
- [ ] **Step 5: Commit** with an isolated task commit.

### Task 2: Derived FULL104 feature-lineage authority

**Files:**
- Create: `src/sea_ad_jepa/v5/full104_feature_lineage_v1.py`
- Create: `tests/test_full104_feature_lineage_v1.py`
- Modify: `.github/workflows/v5_dataset_first_production_closure.yml`
- Modify: `tests/v5_critical_test_manifest_v1.json`

**Interfaces:**
- Produces: `seal_full104_feature_lineage_v1(receipt) -> dict`, `validate_full104_feature_lineage_v1(envelope) -> dict`.
- Receipt must bind exact sealed FULL104 artifact SHA, historical feature and multiview package roots, producer/transform contract hashes, exact `A_full/B_full/A_views/B_views` shapes, 4,553,407 row identity closure, 41,238 address identity closure, 104 donors, 42 operators, deterministic reproduction, and explicit no filtering/capping/sampling/pathology/protected/checkpoint/adaptive-outcome flags.
- Certification terminal must be one of `CERTIFIABLE_EXACT_DERIVATION` or `CERTIFIABLE_WITH_MECHANICS_REPAIR_ONLY`; `NOT_CERTIFIABLE_REBUILD_FROM_AUTHENTICATED_FULL104_REQUIRED` must never seal as execution authority.

- [ ] **Step 1: Write failing tests** for valid sealing plus rejection of wrong row/address identity, wrong roots, outcome adaptation, capping/sampling, nondeterminism, and non-certifiable classification.
- [ ] **Step 2: Push and verify RED** because module is absent.
- [ ] **Step 3: Implement minimal validator/sealer** using `artifact_binding_v1`.
- [ ] **Step 4: Add suite to workflow/critical manifest and verify GREEN**.
- [ ] **Step 5: Commit**.

### Task 3: V5 measurement-procedure qualification authority and scientific stopping rule

**Files:**
- Create: `docs/agent/V5_D_SHARED_MEASUREMENT_QUALIFICATION_AUTHORITY_V1.json`
- Create: `src/sea_ad_jepa/v5/d_shared_measurement_qualification_v1.py`
- Create: `tests/test_d_shared_measurement_qualification_v1.py`
- Modify: `src/sea_ad_jepa/v5/d_shared_rank_adjudication_v2.py`
- Modify: `tests/test_d_shared_rank_adjudication_v2.py`
- Modify: `.github/workflows/v5_dataset_first_production_closure.yml`
- Modify: `tests/v5_critical_test_manifest_v1.json`

**Interfaces:**
- Produces: `validate_measurement_qualification_authority_v1(authority) -> dict`, `seal_measurement_qualification_receipt_v1(authority, receipt) -> dict`, `validate_measurement_qualification_receipt_v1(envelope) -> dict`.
- Freeze three control families before decision evidence: real-geometry negative controls, real-geometry positive controls, and a prospective difficulty curve. Require unconditional failures, donor/top-k/LODO influence diagnostics, nuisance/simple comparator, exact FULL104/feature/reconnaissance parent bindings, and no protected/pathology/checkpoint outcomes.
- Scientific terminal: if no rank 1..512 qualifies, current shared-state hypothesis ends at `D_shared=0`; no threshold relaxation, alternate null, new bins, rank expansion, or same-run redesign.

- [ ] **Step 1: Write failing tests** for authority completeness, rejection of toy-only controls, survivor-only metrics, post-outcome tuning, missing influence/nuisance controls, and scientific stopping-rule mutation.
- [ ] **Step 2: Push and verify RED**.
- [ ] **Step 3: Implement minimal authority/receipt validation and stopping-rule enforcement**.
- [ ] **Step 4: Add critical tests/workflow and verify GREEN**.
- [ ] **Step 5: Commit**.

### Task 4: Executable environment preflight and successor real-D_shared gate

**Files:**
- Create: `src/sea_ad_jepa/v5/environment_preflight_v1.py`
- Create: `scripts/v5_anticheat/run_environment_preflight_v1.py`
- Create: `tests/test_environment_preflight_v1.py`
- Create: `src/sea_ad_jepa/v5/d_shared_real_execution_gate_v1.py`
- Create: `tests/test_d_shared_real_execution_gate_v1.py`
- Modify: `.github/workflows/v5_dataset_first_production_closure.yml`
- Modify: `tests/v5_critical_test_manifest_v1.json`

**Interfaces:**
- `validate_environment_preflight_v1(receipt) -> dict` fails on collection errors, skipped critical tests, missing torch/import, wrong HEAD, dirty authority files, or EOL translation.
- `authorize_real_d_shared_v1(...) -> dict` consumes passed sealed FULL104, feature-lineage, reconnaissance, measurement-qualification, matching-state, environment, and independently reviewed executor receipts. It returns `d_shared_real_outcome_access_authorized=true` only when every exact parent passes; all downstream authorities remain false.

- [ ] **Step 1: Write failing tests** for every fail-closed environment condition and for the successor gate rejecting V2-only authorization.
- [ ] **Step 2: Push and verify RED**.
- [ ] **Step 3: Implement minimal validator/CLI/gate**.
- [ ] **Step 4: Add workflow compile/test coverage and verify GREEN**.
- [ ] **Step 5: Run full exact-head workflow, critical-test guard, compile authority modules, and compare branch against the pre-plan head for unintended files**.
