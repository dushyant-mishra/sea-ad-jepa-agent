# V5 Prospective Precision Authority Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze and enforce a prospective, hash-bound Monte Carlo / donor-resampling precision authority before any current-V5 dimension outcome can become decision-bearing.

**Architecture:** Add one small V5 precision-authority module that deterministically derives required replicate counts from predeclared bounded ranges, tolerances, and Bonferroni family-risk allocation using a Hoeffding fixed-N formula. Freeze one JSON authority artifact for the ten decision-bearing dimension quantities, and make the dimension execution firewall require the authority terminal/hash and exact derived replicate counts. This does not define biological effect thresholds and does not inspect FULL104 outcomes.

**Tech Stack:** Python 3.12 stdlib, JSON canonicalization, SHA-256, pytest.

**Spec:** `docs/superpowers/specs/2026-09-12-v5-dataset-first-production-closure-design.md`

## Global Constraints

- Production data authority remains FULL104: 4,553,407 cells, 104 donors, 42 operators/matrices, 41,238 addresses.
- No pathology, protected validation/oracle data, checkpoint outcomes, numeric dimension outcomes, or training are permitted while this authority is frozen.
- Replicate counts may not inherit historical 256/999/1000 values and may not be tuned after observing outcomes.
- Decision-bearing precision is unconditional over the declared evaluation population; estimator failures are non-qualifying and reported separately.
- Precision criteria are not biological effect criteria.
- Survivor-only intervals are forbidden when estimator failure is possible.
- Gate-ablation and redundancy/identity diagnostics remain required by downstream qualification.

---

### Task 1: Precision authority math and validator

**Files:**
- Create: `src/sea_ad_jepa/v5/prospective_precision_authority_v1.py`
- Test: `tests/test_prospective_precision_authority_v1.py`

**Interfaces:**
- Produces: `derive_hoeffding_fixed_n(range_width: float, tolerance: float, alpha: float) -> int`
- Produces: `canonical_precision_authority_bytes(authority: Mapping[str, object]) -> bytes`
- Produces: `validate_precision_authority_v1(authority: Mapping[str, object]) -> dict[str, object]`

- [ ] Write tests proving 0.05 family risk split across ten quantities yields alpha=0.005 each, fixed-N derivation is exact, historical hand-entered counts fail if they do not match the formula, outcome-inspection flags fail closed, risk allocation must sum exactly to the family budget, and duplicate quantity IDs fail.
- [ ] Run the tests and verify RED because the module does not yet exist.
- [ ] Implement the minimal validator and canonical serializer.
- [ ] Run tests and verify GREEN.

### Task 2: Freeze the prospective V5 dimension precision artifact

**Files:**
- Create: `docs/agent/V5_PROSPECTIVE_DIMENSION_PRECISION_AUTHORITY_V1.json`

**Interfaces:**
- Consumes: the Task-1 validator.
- Produces: one immutable authority artifact covering exactly ten decision-bearing quantities across D_shared, D_private, and D_obs.

- [ ] Freeze total familywise precision risk = 0.05 with equal Bonferroni allocation = 0.005 per quantity.
- [ ] Freeze matched-null exceedance tolerance 0.025 on [0,1] -> 4,794 full-refit null replicates.
- [ ] Freeze range-[0,1] resampling tolerance 0.05 -> 1,199 replicates.
- [ ] Freeze range-[-1,1] resampling tolerance 0.05 -> 4,794 replicates.
- [ ] Freeze deterministic RNG/replay, unconditional failure handling, no survivor-only intervals, no post-outcome tuning, precision-not-effect semantics, and no pathology/protected/checkpoint/dimension outcomes before freeze.
- [ ] Validate and hash the exact canonical artifact bytes.

### Task 3: Make precision authority a mandatory parent of dimension execution

**Files:**
- Modify: `src/sea_ad_jepa/v5/dimension_execution_firewall_v1.py`
- Modify: `tests/test_dimension_execution_firewall_v1.py`

**Interfaces:**
- Consumes: frozen precision authority SHA-256 and its declared derived counts.
- Produces: dimension execution PASS only when the receipt binds the exact authority and uses the exact prospectively derived counts.

- [ ] Write failing tests proving a receipt that merely says `*_derived_from_error_budget=True` without a precision authority hash/terminal is rejected.
- [ ] Add tests proving null/donor/operator replicate count mismatch versus the frozen authority is rejected.
- [ ] Add fail-closed checks for `precision_authority_frozen_before_dimension_outcomes=True` and `precision_authority_terminal=PASS_V5_PROSPECTIVE_PRECISION_AUTHORITY_V1`.
- [ ] Implement minimal firewall checks.
- [ ] Run the V5 dimension/firewall suite and verify GREEN.

### Task 4: Wire CI and verify exact-head behavior

**Files:**
- Modify: `.github/workflows/v5_dataset_first_production_closure.yml`

**Interfaces:**
- Consumes: new precision-authority tests.
- Produces: exact-head CI evidence that precision authority cannot silently disappear or be skipped.

- [ ] Add `tests/test_prospective_precision_authority_v1.py` to the V5 dataset-first closure workflow.
- [ ] Run exact-head GitHub Actions.
- [ ] Require full suite PASS, frozen critical-test guard PASS, authority-source compilation PASS.
- [ ] Red-team the final diff for historical-count leakage, outcome-adaptive tuning, conditional-on-success metrics, or training/protected-data authority creep.
