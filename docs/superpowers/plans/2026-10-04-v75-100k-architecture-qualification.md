# V75 100K Architecture Qualification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Qualify the FULL104-like synthetic measurement architecture for a 100K stress run without overclaiming a learned 160-D JEPA state.

**Architecture:** Start from V74 calibration closure, restore only the V73 stress-twin protections that V74 regressed, then require a real 2K promotion smoke with complete feasible operator occupancy, independent fragment-byte linkage, empirical-QC causal consumption, control twins, protected-boundary checks, and fail-closed readiness. 100K execution remains measurement/population architecture qualification only.

**Tech Stack:** Python 3.11, NumPy, pytest, GitHub Actions, JSON authority receipts.

**Spec:** `results/v75/V75_PHASE0_LINEAGE_DECISION_V1.json`

## Global Constraints

- Training OFF.
- Stage 4 NOT AUTHORIZED.
- Real correspondence UNOPENED.
- Morabito PROTECTED.
- Recoverability TEST SEALED.
- No pathology variable as observation-operator input.
- 2K smoke may authorize only 100K stress.
- 100K measurement qualification must not be called learned 160-D JEPA-state qualification.
- No threshold may be selected from observed 100K outcomes.

## Review Focus

- 2K source quota can support all source-nested operators but largest remainder still gives zero: rescue must preserve source totals.
- Fragment gzip bytes can change while decompressed rows remain identical: digest must be recomputed from bytes.
- QC authority can be present/bound but behaviorally unused: mutation must move generated targets.
- Smoke can execute successfully while omitting operators: readiness must inspect realized occupancy, not a status string.
- Resource pressure must not silently alter cell/operator/source population.

---

### Task 1: Restore feasible operator occupancy

**Files:**
- Modify: `scripts/v64/v73_full104_population_geometry.py`
- Test: `tests/test_v73_population_geometry_authority.py`

**Interfaces:**
- Consumes: authenticated FULL104 source/operator counts.
- Produces: source-preserving operator quotas with nonzero occupancy when each source quota is large enough to cover its operators.

- [ ] RED: run `test_2k_smoke_preserves_all_feasible_operator_support` on V74 semantics and observe failure.
- [ ] GREEN: restore within-source zero-quota rescue from audited V73 stress-twin semantics.
- [ ] Verify 2K = 42/42, 10K = 42/42, 100K/full counts unchanged.
- [ ] Commit.

### Task 2: Restore independent fragment byte linkage

**Files:**
- Create: `scripts/v64/validate_v73_fragment_byte_linkage.py`
- Test: `tests/test_v75_fragment_byte_linkage.py`

**Interfaces:**
- Consumes: fragment manifest + compressed fragment shards + paired-multiome source shards.
- Produces: fail-closed byte/linkage receipt.

- [ ] RED: test import/validation fails because validator is absent on V74.
- [ ] GREEN: restore audited V73 validator semantics.
- [ ] Verify byte mutation and multiplicity mutation fail for named reasons.
- [ ] Wire into 2K smoke before readiness authorization.
- [ ] Commit.

### Task 3: Causally prove QC authority consumption

**Files:**
- Test: `tests/test_v75_rna_qc_authority_mutation.py`
- Preserve unless defect found: `scripts/v64/build_v73_full104_sharded_observer.py`

**Interfaces:**
- Consumes: operator-level QC quantiles.
- Produces: evidence that changing consumed empirical library distributions changes generated panel targets while unused data does not.

- [ ] Run mutation test.
- [ ] If failure reveals decorative calibration, repair minimally under TDD; otherwise record existing behavior as qualified.
- [ ] Commit result/receipt.

### Task 4: Audit existing V75 control/readiness implementation

**Files:**
- Audit: `scripts/v75/build_v75_control_twins.py`
- Audit: `scripts/v75/validate_v75_run_boundaries.py`
- Audit: `scripts/v75/validate_v75_100k_readiness.py`
- Audit: `tests/test_v75_*.py`

**Interfaces:**
- Consumes: repaired legacy smoke + V75 controls.
- Produces: narrow permission for 100K measurement-architecture stress only.

- [ ] Verify controls use same biological truth for measurement-null and prospectively distinct biology for positive twin.
- [ ] Verify no threshold is outcome-tuned.
- [ ] Verify actual manifests prove protected boundaries.
- [ ] Verify readiness refuses missing operator occupancy/fragment linkage/QC mutation evidence.
- [ ] Commit any minimal fixes.

### Task 5: Exact 2K promotion smoke

**Files:**
- Modify: `.github/workflows/v75-100k-architecture-qualification.yml`
- Results: uploaded machine receipts.

**Interfaces:**
- Consumes: Tasks 1–4.
- Produces: `READY_FOR_100K_MEASUREMENT_ARCHITECTURE_STRESS_ONLY` or fail-closed blocker list.

- [ ] Execute exact-head workflow.
- [ ] Require 42/42 realized operators at 2K.
- [ ] Require fragment-byte validator PASS.
- [ ] Require QC causal-consumption proof.
- [ ] Require boundaries PASS.
- [ ] Explicitly keep 500K/full/training unauthorized.
- [ ] Commit closeout receipt only after evidence exists.

### Task 6: 100K measurement architecture stress

**Files:**
- Execute existing V75 100K workflow only after Task 5 authorization.
- Result validator: `scripts/v75/validate_v75_100k_result.py`

**Interfaces:**
- Consumes: exact authorized 2K preflight.
- Produces: PASS/FAIL/INDETERMINATE for progression to 500K measurement stress.

- [ ] Freeze execution SHA, seed, shard size, authorities, controls, resource ceilings.
- [ ] Run 100K.
- [ ] Validate population/QC/resource/shard/control metrics prospectively.
- [ ] Do not claim learned 160-D state qualification.
- [ ] Emit narrow decision and next action.
