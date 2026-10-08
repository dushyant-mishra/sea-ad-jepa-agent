# Remaining-RNA Necessity and Target-Semantics Successor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make current V5 fail closed unless query-local biological-state semantics are explicit and remaining RNA is prospectively required beyond query identity and lawful global biological context.

**Architecture:** Add a geometry-neutral remaining-RNA necessity decision rule that compares lawful full-evidence state scores against identity-only and query+lawful-global-context/no-remaining-RNA controls using paired robust summaries. Add `TeacherTargetSemanticsAuthorityV2` with enumerated biological/query-local semantics, explicit prohibition of scalar hidden-gene reconstruction, and a bound remaining-RNA-necessity authority root. Integrate the successor into current authority closure without opening training or protected outcomes.

**Tech Stack:** Python 3.12, dataclasses, stdlib hashlib/json/statistics, pytest, GitHub Actions.

**Spec:** `docs/agent/JEPA_NEW_CHAT_HANDOFF_20260917_RIDGE8_T1_SPILLOVER_CURRENT.md`

## Global Constraints

- `TRAINING_OFF`.
- Protected/pathology/DEV/SEALED/D_shared outcomes remain sealed.
- Target is biological/cellular latent state including query-local state, never hidden-gene scalar expression.
- Remaining-RNA necessity must allow lawful global biological context while proving that query identity/global context alone are insufficient.
- Historical T1 is an adversarial fixture, not healthy-teacher authority.
- No production geometry, mask burden, EMA timescale, or new numerical scientific threshold is silently frozen by this change.
- Numeric necessity thresholds are explicit authority inputs, not defaults.

---

### Task 1: Remaining-RNA necessity regression

**Files:**
- Create: `tests/test_v5_remaining_rna_necessity_v1.py`
- Create: `.github/workflows/v5-remaining-rna-target-semantics.yml`
- Create: `src/sea_ad_jepa/v5/remaining_rna_necessity_v1.py`

**Interfaces:**
- Produces `RemainingRnaNecessityAuthorityV1` and `evaluate_remaining_rna_necessity_v1(...)`.
- Evaluation consumes paired full-RNA, identity-only, and query+lawful-global-context/no-remaining-RNA query-local state scores.
- Positive paired advantage always means remaining RNA helps, regardless of whether the chosen latent-state metric is similarity or error.

- [ ] **Step 1: Write failing tests** proving missing implementation, explicit protocol vocabulary, robust paired decision behavior, identity/global-only insufficiency, no hidden-expression metric, no defaults for scientific thresholds, and training-off behavior.
- [ ] **Step 2: Run focused CI and verify RED** because the module does not yet exist.
- [ ] **Step 3: Implement minimal authority/evaluator** using enumerated state-only metric/protocol vocabulary, median paired advantage plus win fraction, exact input-length/finite-value checks, and no production threshold defaults.
- [ ] **Step 4: Run focused tests and verify GREEN** with zero skips.

### Task 2: Teacher-target semantics successor

**Files:**
- Create: `src/sea_ad_jepa/v5/teacher_target_semantics_authority_v2.py`
- Extend: `tests/test_v5_remaining_rna_necessity_v1.py`

**Interfaces:**
- Produces `TeacherTargetSemanticsAuthorityV2`.
- Binds representation, support, target-address provider, student-visible support, scientific estimand, masking, EMA boundary, target-construction root, gradient-boundary root, and remaining-RNA-necessity root.
- Enumerates state semantics and forbids scalar hidden-gene reconstruction.

- [ ] **Step 1: Add failing tests** for biological latent-state enum, query-local enum, scalar-expression prohibition, identity/global-only insufficiency policy, bound necessity root, and `training_authorized=False`.
- [ ] **Step 2: Verify RED** against absent V2 implementation.
- [ ] **Step 3: Implement minimal V2 authority** without modifying historical V1.
- [ ] **Step 4: Verify GREEN**.

### Task 3: Current closure and spillover integration

**Files:**
- Modify: `src/sea_ad_jepa/v5/current_authority_closure_v1.py`
- Modify: `tests/test_v5_current_authority_closure_v1.py`
- Modify as needed: `tests/test_v5_current_stage_a_spillover_firewall_v1.py`

**Interfaces:**
- Current closure must reject `TeacherTargetSemanticsAuthorityV1` even if internally self-consistent.
- Current closure must accept only `TeacherTargetSemanticsAuthorityV2` for the teacher-target role.
- Existing current target-address and masking successor schemas must remain current; historical schemas remain quarantined.

- [ ] **Step 1: Add failing closure/spillover tests** for legacy teacher-target substitution.
- [ ] **Step 2: Verify RED**.
- [ ] **Step 3: Add minimal type gate/imports** to current closure/firewall.
- [ ] **Step 4: Run focused and existing V5 closure/Stage-A suites**.

### Task 4: Verification and documentation

**Files:**
- Add a concise authority note under `docs/agent/` only after code/tests are green.

- [ ] **Step 1: Run focused CI with zero skips.**
- [ ] **Step 2: Run existing current-authority and Stage-A regression suites.**
- [ ] **Step 3: Inspect diff for forbidden semantic drift, accidental training authority, protected-outcome access, or hidden numerical defaults.**
- [ ] **Step 4: Record what is structurally closed versus what still requires prospective FULL104/GPU evidence.**
