# V5 Target and Remaining-RNA Execution Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bind the exact query-safe teacher-target computation graph and separate semantic authority from executed evidence that remaining RNA is necessary for query-local state recovery.

**Architecture:** `TeacherTargetSemanticsAuthorityV2` defines meaning; `TargetConstructionAuthorityV1` pins computation-graph semantics; `RemainingRnaNecessityAuthorityV1` defines the decision rule; a separate execution-evidence authority binds healthy-teacher results and precision authority. Historical T1 checkpoints remain adversarial fixtures only.

**Tech Stack:** Python 3.12, dataclasses, hashlib/json, pytest, current V5 query-provider and authority modules.

**Spec:** `docs/superpowers/specs/2026-09-17-v5-production-authority-closure-design.md`

## Global Constraints

- Biological/query-local latent state only; scalar hidden-gene reconstruction forbidden.
- Query identity remains supplied.
- Queried scalar evidence must be withheld before contextual mixing.
- Lawful global biological context may remain available.
- Remaining-RNA qualification is state-level and prospectively precision-bound.
- TRAINING_OFF and protected outcomes sealed.

---

### Task 1: Target-construction authority

**Files:**
- Create: `src/sea_ad_jepa/v5/target_construction_authority_v1.py`
- Create: `tests/test_v5_target_construction_authority_v1.py`

**Interfaces:**
- Produces `TargetConstructionAuthorityV1` with exact roots for representation, support, target-address provider and implementation artifact.
- Enumerates `QUERY_IDENTITY_SUPPLIED_V1`, `QUERY_SCALAR_WITHHELD_BEFORE_CONTEXT_MIXING_V1`, `NON_QUERY_LAWFUL_RNA_VISIBLE_V1`, `LAWFUL_GLOBAL_BIOLOGICAL_CONTEXT_ALLOWED_V1`, `TEACHER_STOPGRAD_V1`, `SCALAR_EXPRESSION_OBJECTIVE_ABSENT_V1`.

- [ ] **Step 1: Write failing tests** rejecting free-form semantics, missing implementation root, query-scalar-visible policy and scalar-expression objective.
- [ ] **Step 2: Run** `python -m pytest -q tests/test_v5_target_construction_authority_v1.py` and confirm RED.
- [ ] **Step 3: Implement** the authority and deterministic canonical digest.
- [ ] **Step 4: Run** tests and require PASS.
- [ ] **Step 5: Commit** `feat(v5): bind query-safe target construction`.

### Task 2: Bind target construction into teacher semantics

**Files:**
- Modify: `src/sea_ad_jepa/v5/teacher_target_semantics_authority_v2.py`
- Modify: `tests/test_v5_remaining_rna_necessity_v1.py`
- Modify: `tests/test_v5_current_semantic_successor_spillover_v1.py`

**Interfaces:**
- `TeacherTargetSemanticsAuthorityV2.target_construction_authority_sha256` must equal the live target-construction authority digest through an explicit binder.

- [ ] **Step 1: Add failing tests** proving a valid semantic object with a wrong target-construction root is rejected by the binder/closure.
- [ ] **Step 2: Run** focused tests and confirm RED.
- [ ] **Step 3: Add** `bind_teacher_semantics_to_target_construction_v1(teacher, target_construction)` and use it from current closure.
- [ ] **Step 4: Run** focused tests and require PASS.
- [ ] **Step 5: Commit** `fix(v5): bind teacher semantics to target construction`.

### Task 3: Remaining-RNA execution evidence authority

**Files:**
- Create: `src/sea_ad_jepa/v5/remaining_rna_execution_authority_v1.py`
- Create: `tests/test_v5_remaining_rna_execution_authority_v1.py`

**Interfaces:**
- Produces `RemainingRnaExecutionAuthorityV1` binding the rule authority, precision authority, target construction, target panel, outer split, exact result artifact SHA and terminal status.
- Terminal status enum is `EXECUTED_PASS` or `EXECUTED_FAIL`; nonexecution/skipped is never PASS.

- [ ] **Step 1: Write failing tests** for fabricated pass without result root, wrong rule/precision roots, skipped/nonexecuted status and historical-T1 evidence identifier.
- [ ] **Step 2: Run** tests and confirm RED.
- [ ] **Step 3: Implement** the execution authority with enumerated evidence source `HEALTHY_CURRENT_V5_TEACHER_V1` only.
- [ ] **Step 4: Run** tests and require PASS.
- [ ] **Step 5: Commit** `feat(v5): add remaining RNA execution evidence authority`.

### Task 4: Critical-test/anti-cheat integration

**Files:**
- Modify: `src/sea_ad_jepa/v5/anti_cheat_authority_bundle_v1.py` or create successor `anti_cheat_authority_bundle_v2.py` if adding fields would break frozen V1 provenance.
- Create/Modify: corresponding tests under `tests/test_v5_anti_cheat*`.

**Interfaces:**
- Current anti-cheat bundle must bind remaining-RNA execution evidence in addition to target identity, masking, measurement, observation-gradient firewall and critical-test execution.

- [ ] **Step 1: Write failing regression** showing a bundle/closure can currently pass without any healthy remaining-RNA execution evidence.
- [ ] **Step 2: Run** and confirm RED.
- [ ] **Step 3: Prefer a V2 successor** if V1 is already frozen historical provenance; require distinct role digests and `training_authorized=False`.
- [ ] **Step 4: Run** anti-cheat + closure + semantic spillover suites and require PASS with zero skips.
- [ ] **Step 5: Commit** `feat(v5): require healthy remaining RNA evidence in anti cheat closure`.

### Task 5: FULL104 healthy-teacher runner contract

**Files:**
- Create: `analysis/v5_remaining_rna_qualification_20260917/REMAINING_RNA_FULL104_RUN_CONTRACT.json`
- Create: `analysis/v5_remaining_rna_qualification_20260917/validate_remaining_rna_run_contract.py`
- Create: `tests/test_v5_remaining_rna_full104_contract_v1.py`

**Interfaces:**
- Contract binds exact source commit/root and requires three aligned conditions: full lawful remaining RNA, identity-only, identity+lawful-global-context/no-RNA.

- [ ] **Step 1: Write failing tests** requiring all upstream roots, healthy current-V5 teacher source, state metric, target/fold aligned outputs, no protected metadata and no training.
- [ ] **Step 2: Run** and confirm RED.
- [ ] **Step 3: Implement** the contract validator; leave data-dependent numerical thresholds supplied only through frozen precision authority.
- [ ] **Step 4: Run** tests and require PASS.
- [ ] **Step 5: Commit** `feat(v5): freeze remaining RNA full104 runner contract`.

### Task 6: Spillover firewall update

**Files:**
- Modify: `tests/test_v5_current_stage_a_spillover_firewall_v1.py`
- Modify: `tests/test_v5_current_stage_a_spillover_firewall_v2.py`

- [ ] **Step 1: Add failing test** that all current target construction/execution modules are tracked while historical teacher semantics V1 remains quarantined.
- [ ] **Step 2: Run** and confirm RED.
- [ ] **Step 3: Update** current path/quarantine sets.
- [ ] **Step 4: Run** Stage-A + target suites and require PASS/no skips.
- [ ] **Step 5: Commit** `test(v5): extend spillover firewall through target execution`.
