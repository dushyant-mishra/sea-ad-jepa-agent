# V5 Runtime, Geometry, EMA and Training-Lock Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace remaining permissive/free-form production-runtime seams with current-V5 successors and create one final fail-closed authority closure that is incapable of authorizing training until all scientific/runtime evidence exists.

**Architecture:** Preserve audited optimizer/checkpoint/EMA mechanics, but introduce current successor schemas for geometry, EMA timescale, measurement robustness and runtime source. A new authority-root vocabulary/closure version binds all newly separated masking/target evidence roots. A distinct final training authority is the only object permitted to set training authorization true.

**Tech Stack:** Python 3.12, dataclasses, hashlib/json, pytest, existing V5 guards.

**Spec:** `docs/superpowers/specs/2026-09-17-v5-production-authority-closure-design.md`

## Global Constraints

- Historical geometry and `.996` EMA values are not production authority.
- EMA advances only after proved optimizer step.
- Dynamic protected registry is geometry-derived.
- No current runtime may call historical V4 `production_update`.
- Training authorization belongs to one final authority only.
- Zero skipped critical tests.

---

### Task 1: Current runtime-source authority

**Files:**
- Create: `src/sea_ad_jepa/v5/current_runtime_source_authority_v1.py`
- Create: `tests/test_v5_current_runtime_source_authority_v1.py`

**Interfaces:**
- `CurrentRuntimeSourceAuthorityV1` binds exact source manifest SHA, source root SHA, Python/runtime ABI identifier and forbidden historical entrypoint policy.

- [ ] **Step 1: Write failing tests** rejecting raw single-file placeholders, historical V4 `production_update` entrypoint, noncanonical source roots and `training_authorized=True`.
- [ ] **Step 2: Run** focused tests and confirm RED.
- [ ] **Step 3: Implement** enumerated runtime-entrypoint semantics and deterministic digest.
- [ ] **Step 4: Run** tests and require PASS.
- [ ] **Step 5: Commit** `feat(v5): add current runtime source authority`.

### Task 2: Model geometry successor

**Files:**
- Create: `src/sea_ad_jepa/v5/model_geometry_authority_v2.py`
- Create: `tests/test_v5_model_geometry_authority_v2.py`

**Interfaces:**
- `ModelGeometryAuthorityV2` binds dimension authority, deterministic rank-to-geometry rule, exact geometry artifact, dynamic protected registry and geometry-dependent memorization qualification root.

- [ ] **Step 1: Write failing tests** showing V1 accepts free-form `geometry_schema_id` and lacks memorization-rerun evidence.
- [ ] **Step 2: Run** and confirm RED.
- [ ] **Step 3: Implement** V2 with enumerated geometry schema/rule IDs and mandatory geometry-specific memorization qualification root.
- [ ] **Step 4: Run** V1 provenance tests plus V2 tests and require PASS.
- [ ] **Step 5: Commit** `feat(v5): add geometry authority successor`.

### Task 3: EMA timescale successor

**Files:**
- Create: `src/sea_ad_jepa/v5/ema_timescale_authority_v2.py`
- Create: `tests/test_v5_ema_timescale_authority_v2.py`

**Interfaces:**
- `EmaTimescaleAuthorityV2` permits only presentation-normalized half-life momentum `exp(log(0.5)*p/H)` and enumerated presentation units.

- [ ] **Step 1: Write failing tests** demonstrating V1 accepts arbitrary momentum/presentation strings.
- [ ] **Step 2: Run** and confirm RED.
- [ ] **Step 3: Implement** enumerated function/presentation semantics, positive half-life, base-estimand/schedule roots and deterministic digest.
- [ ] **Step 4: Run** EMA presentation + V1 provenance + V2 tests.
- [ ] **Step 5: Commit** `feat(v5): add presentation normalized EMA authority`.

### Task 4: Measurement-robustness successor

**Files:**
- Create: `src/sea_ad_jepa/v5/measurement_robustness_authority_v2.py`
- Create: `tests/test_v5_measurement_robustness_authority_v2.py`

**Interfaces:**
- `MeasurementRobustnessAuthorityV2` binds perturbation protocol, state-level metric, stratification guardrail, precision authority and executed result artifact/status.

- [ ] **Step 1: Write failing tests** demonstrating V1 accepts arbitrary metric/failure labels and no execution evidence.
- [ ] **Step 2: Run** and confirm RED.
- [ ] **Step 3: Implement** enumerated state metric/perturbation/failure semantics plus result root/status.
- [ ] **Step 4: Run** tests and require PASS.
- [ ] **Step 5: Commit** `feat(v5): add executed measurement robustness authority`.

### Task 5: Current V5 root vocabulary and closure V2

**Files:**
- Create: `src/sea_ad_jepa/v5/current_authority_roots_v2.py`
- Create: `src/sea_ad_jepa/v5/current_authority_closure_v2.py`
- Create: `tests/test_v5_current_authority_closure_v2.py`

**Interfaces:**
- V2 root vocabulary explicitly includes target evidence budget, precision, split, target panel, address universe, masking qualification design, target construction, remaining-RNA execution, geometry V2, EMA V2, measurement V2 and runtime-source authority in addition to established substrate/representation/support/estimand/address/masking/anti-cheat roots.

- [ ] **Step 1: Write failing tests** for every single-root splice, missing role, duplicate role digest, legacy schema substitution and training-authorized upstream object.
- [ ] **Step 2: Run** and confirm RED.
- [ ] **Step 3: Implement** exact root vocabulary and live-object binders; no generic 64-character placeholder may substitute for an object where a live authority is supplied.
- [ ] **Step 4: Run** V1 closure provenance tests plus V2 closure tests.
- [ ] **Step 5: Commit** `feat(v5): add complete current authority closure v2`.

### Task 6: Preexecution/receipt/optimizer successors

**Files:**
- Create: `src/sea_ad_jepa/v5/current_trainer_preexecution_contract_v2.py`
- Create: `src/sea_ad_jepa/v5/current_teacher_target_receipt_v2.py`
- Create: `src/sea_ad_jepa/v5/qualified_optimizer_guard_v3.py`
- Create: `tests/test_v5_current_preexecution_receipt_optimizer_v2.py`

**Interfaces:**
- Preexecution V2 consumes exactly the V2 root vocabulary and critical-test/protected-registry roots.
- Receipt V2 seals target package + exact V2 roots + preexecution root.
- Optimizer guard V3 accepts only Receipt V2 and refuses any legacy receipt.

- [ ] **Step 1: Write failing tests** proving current V1/V2 path can still be substituted with older root vocabulary/receipt where not explicitly gated.
- [ ] **Step 2: Run** and confirm RED.
- [ ] **Step 3: Implement** the three successors and exact-root validation.
- [ ] **Step 4: Run** optimizer/checkpoint/current closure suites with zero skips.
- [ ] **Step 5: Commit** `feat(v5): advance preexecution receipt and optimizer guards`.

### Task 7: Explicit final training authority

**Files:**
- Create: `src/sea_ad_jepa/v5/current_training_authority_v1.py`
- Create: `tests/test_v5_current_training_authority_v1.py`

**Interfaces:**
- `CurrentTrainingAuthorityV1` is the only schema allowed to carry `training_authorized=True` and only when exact closure V2, preexecution V2, critical tests, receipt V2 and runtime-source roots are supplied with terminal executed-pass statuses.

- [ ] **Step 1: Write failing tests** for missing FULL104 masking qualification, remaining-RNA evidence, geometry-memory rerun, EMA, measurement, runtime source and skipped critical tests.
- [ ] **Step 2: Run** and confirm RED.
- [ ] **Step 3: Implement** a fail-closed authority that defaults false and requires an explicit `issue_training_authority_v1(...)` constructor to produce true after all validated prerequisites.
- [ ] **Step 4: Ensure** every other V5 authority rejects `training_authorized=True`.
- [ ] **Step 5: Run** full current-V5 authority suite/no-skip guard.
- [ ] **Step 6: Commit** `feat(v5): add explicit final training authority gate`.

### Task 8: Stage-A spillover and full regression

**Files:**
- Modify: `tests/test_v5_current_stage_a_spillover_firewall_v1.py`
- Modify: `tests/test_v5_current_stage_a_spillover_firewall_v2.py`
- Add/update workflow under `.github/workflows/` for current V5 closure.

- [ ] **Step 1: Add failing tests** requiring every V2/current successor module and quarantining V1 schemas that are no longer current.
- [ ] **Step 2: Run** and confirm RED.
- [ ] **Step 3: Update** firewall and workflow.
- [ ] **Step 4: Run** broad current-V5 tests twice, second pass with explicit skip detector.
- [ ] **Step 5: Commit** `test(v5): close current framework spillover surface`.
