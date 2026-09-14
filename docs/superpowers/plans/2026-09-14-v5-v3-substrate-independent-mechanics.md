# V5 V3 Substrate-Independent Mechanics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and qualify V3-supporting mechanics that remain valid regardless of Claude's rebuilt FULL104 feature substrate: null mobility auditing, T0 sandbox authority/firewall, and hardened same-cell intervention receipts.

**Architecture:** Keep scientific choices unfrozen. The mobility auditor validates any predeclared discrete-block permutation without choosing blocks; the T0 sandbox validator can reject candidates or promote them only to FULL104 qualification, never to V5 execution authority; the same-cell probe remains a measurement-robustness diagnostic and cannot authorize D_shared. All artifacts are deterministic and fail closed.

**Tech Stack:** Python 3.12, NumPy, pytest, existing `sea_ad_jepa.v5.artifact_binding_v1` utilities, GitHub Actions protected V5 closure workflow.

**Spec:** `docs/superpowers/specs/2026-09-14-v5-v3-null-and-t0-stress-bench-design.md`

## Global Constraints

- No real D_shared decision-bearing outcome access.
- No D_private, D_obs, training, TD60, relational activation, pathology/protected confirmation, or fresh T0 reader-validation access.
- Do not freeze a final V3 null, rank envelope, block choice, depth/detection bins, or V5 numerical thresholds.
- T0 may reject a candidate; T0 passage may only permit FULL104 qualification.
- Historical `RARE_TAIL_UNDERDETERMINED_MEASUREMENT` remains immutable.
- Association/permutation significance must not be represented as effect-transport authority.
- All failure accounting is unconditional; survivor-only summaries are forbidden.

---

### Task 1: Generic blocked-permutation mobility auditor

**Files:**
- Create: `src/sea_ad_jepa/v5/null_mobility_audit_v1.py`
- Create: `tests/test_null_mobility_audit_v1.py`

**Interfaces:**
- Consumes: row-aligned `block_labels` and integer `permutation` plus explicit parent/seed identifiers.
- Produces: `audit_blocked_permutation_v1(...) -> dict[str, object]` with population, eligible/movable/changed/identity counts and fractions, block-level mobility, exact permutation validity, deterministic binding metadata, and `null_mobility_qualifying` based only on an explicit caller-supplied prospective minimum mobility.

- [ ] **Step 1: Write failing tests** for valid within-block permutation, duplicate/missing indices, cross-block movement, all-identity degeneracy, singleton handling, and forbidden outcome/authority escalation fields.
- [ ] **Step 2: Run CI and confirm RED** because the module does not exist.
- [ ] **Step 3: Implement the minimal auditor** with exact permutation checks, block preservation, mobility accounting, and fail-closed outcome flags.
- [ ] **Step 4: Run CI and require GREEN** for the new test plus existing closure suite.
- [ ] **Step 5: Commit** as an independently reviewable mechanics change.

### Task 2: T0-V3 sandbox authority/firewall

**Files:**
- Create: `src/sea_ad_jepa/v5/t0_v3_sandbox_firewall_v1.py`
- Create: `tests/test_t0_v3_sandbox_firewall_v1.py`

**Interfaces:**
- Consumes: a sandbox receipt with candidate ID, declared stress tests, historical-input classification, outcome-access flags, and terminal.
- Produces: `validate_t0_v3_sandbox_receipt_v1(receipt) -> dict[str, object]` permitting only `REJECT_CANDIDATE` or `ELIGIBLE_FOR_FULL104_QUALIFICATION` and always emitting all V5 execution authorities false.

- [ ] **Step 1: Write failing tests** proving a clean synthetic/historical receipt is accepted, while V5 qualification claims, D_shared authorization, fresh reader-validation/AT8/oracle/protected access, rare-tail override, broad-state-as-acceptance-criterion, survivor-only accounting, and effect-transport claims are rejected.
- [ ] **Step 2: Run CI and confirm RED** because the module does not exist.
- [ ] **Step 3: Implement minimal validator** with exact allowed terminals and explicit historical boundaries.
- [ ] **Step 4: Run CI and require GREEN** for new tests and closure suite.
- [ ] **Step 5: Commit** independently.

### Task 3: Harden same-cell intervention provenance and authority limits

**Files:**
- Modify: `src/sea_ad_jepa/v5/same_cell_technical_intervention_probe_v1.py`
- Modify: `tests/test_same_cell_technical_intervention_probe_v1.py`

**Interfaces:**
- Preserve existing summary/threshold interfaces.
- Add a deterministic receipt/binding layer requiring parent SHA-256, intervention-plan SHA-256, declared intervention strength, stable row identity, donor/operator/source preservation declarations, forbidden-outcome flags, and authority terminal restricted to measurement robustness only.

- [ ] **Step 1: Add failing tests** for mutated parent, undeclared/adaptive intervention strength, changed identity/nuisance-parent metadata, pathology/D_shared feedback, and attempted V5 qualification escalation.
- [ ] **Step 2: Run CI and confirm targeted RED.**
- [ ] **Step 3: Implement receipt seal/validate helpers** using `artifact_binding_v1` without changing the existing numerical metric semantics.
- [ ] **Step 4: Run CI and require GREEN.**
- [ ] **Step 5: Commit** independently.

### Task 4: Protected-CI integration and red-team closure

**Files:**
- Modify: `.github/workflows/v5_dataset_first_production_closure.yml`
- Modify: `tests/v5_critical_test_manifest_v1.json` only for a small set of new fail-closed critical tests.

**Interfaces:**
- CI must execute both new suites and compile both new modules.

- [ ] **Step 1: Add new test files to protected workflow and key tests to critical manifest.**
- [ ] **Step 2: Trigger exact-head GitHub Actions.**
- [ ] **Step 3: Inspect job steps/logs and require closure tests, critical-test guard, and compile step all GREEN.**
- [ ] **Step 4: Re-fetch branch head and verify no unrelated substrate/rank/null authority was changed.**
- [ ] **Step 5: Report exact evidence and remaining Claude-dependent blockers.**
