# Unified Task 3 Rejection Preservation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve Macha's exact Unified Task 3 rejection as executable evidence on the active repair branch before any B1-B5 production repair.

**Architecture:** Treat the independent review head `869ca777a498181c519ccfc04b8bf5db0f2888c7` as immutable evidence, not as code authority. First remove the two write-capable self-rewriting workflows from PR #392, then port H1-H6 plus actor-alias attacks into a read-only pytest regression file and demonstrate that the rejected implementation fails those tests. No Task 4 code, protected values, or biological data are touched.

**Tech Stack:** Python 3.11, pytest 9.1.1, GitHub Actions, existing `scripts.v5.td_unified` registry/authority code.

**Spec:** `docs/agent/MACHA_UNIFIED_TASK3_INDEPENDENT_REVIEW_851544E8_20261015.md` at review head `869ca777a498181c519ccfc04b8bf5db0f2888c7` plus `results/target_discovery/unified_qualification_v1/JEPA_LANE_TAKEOVER_STATE_V1_20261015.json` at PR #322 head `31e33f57f1e456e28f93250493d45da5ee4ffa7a`.

## Global Constraints

- Task 0/1/2 authority remains frozen at `e37a22b...`, `799d2e23...`, and `c7dfff1c...` respectively.
- Task 3 remains `REJECTED_OPEN_REPAIR_REQUIRED` until an independent exact-head recheck accepts it.
- Task 4 implementation remains blocked until exact-head Task 3 acceptance/freeze.
- Global authority remains `TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
- Do not open protected biological/candidate/validation/oracle values.
- Do not modify frozen Task 0-2 files.
- Preserve Macha H1-H6 and actor-alias probes as RED evidence before production repair.
- No CI workflow may rewrite production code or tests on push.

## Review Focus

- A human push must not cause CI-authored source/test mutation.
- H1 must expose UNIT scope climbing beyond `HUMAN_EXECUTED`.
- H2 must expose evidence-free `KNOWN_TRUTH_QUALIFIED` promotion.
- Actor aliases and self-minted controller identities must remain explicit failing attacks.
- H3/H4 cache poisoning plus H5/H6 fabricated/rewritten history must remain independently visible failures.

---

### Task 1: Contain T3-B6 before any other repair

**Files:**
- Delete: `.github/workflows/task3-red6-actor-repair.yml`
- Delete: `.github/workflows/apply-task3-cycle4-hardening.yml`

**Interfaces:**
- Consumes: rejected PR #392 head `851544e8dc2a3881193a4d5bbcf07933e1d61149`.
- Produces: a branch where Task 3 CI is verification-only.

- [x] **Step 1: Delete the RED6 self-rewriting workflow**

Commit: `229317559f69929a72678ceebc1bdd43a0b62f65`.

- [x] **Step 2: Delete the cycle4 self-rewriting workflow**

Commit: `6d6a0a315575ba61320b3fb7cac767d467219a49`.

- [x] **Step 3: Verify both paths are absent and PR #392 points at `6d6a0a31...`**

Expected: both file fetches return 404; PR #392 head equals `6d6a0a315575ba61320b3fb7cac767d467219a49`.

### Task 2: Import the independent hostile attacks as pytest RED

**Files:**
- Create: `tests/v5/td_unified/test_registry_v1_macha_rejection.py`

**Interfaces:**
- Consumes: exact hostile logic from `docs/agent/macha_task3_review_evidence_851544e8/task3_probe1.py` at review head `869ca777...` and existing `registry_v1_dependency_fixtures`.
- Produces: separate pytest tests for H1, H2, actor aliases/self-minting, H3, H4, H5, H6.

- [ ] **Step 1: Write H1/H2 tests**

Assert that a UNIT-scoped record cannot promote beyond `HUMAN_EXECUTED`, and that `SAME_CODE_PATH -> KNOWN_TRUTH_QUALIFIED` without independent reviewer/sealed evidence is refused.

- [ ] **Step 2: Write actor-alias/self-minted identity tests**

Use the exact alias classes from Macha: trailing whitespace, leading whitespace, case alias, fullwidth-colon alias, plus a newly minted controller id. Each attack must be refused.

- [ ] **Step 3: Write H3/H4 cache tests**

Reuse Macha's caller-poisoned and warmed-cache attacks; each must fail to authenticate an empty resolver.

- [ ] **Step 4: Write H5/H6 history tests**

Reuse Macha's fabricated REAL_REFERENCE_READY receipt and delete-revocation/rebuild attacks; each must be refused.

- [ ] **Step 5: Run the focused file through read-only CI and verify RED**

Run: `python -m pytest -q tests/v5/td_unified/test_registry_v1_macha_rejection.py`

Expected: failures correspond to the already-reviewed B1-B5 defects, not import/collection errors.

### Task 3: Record the takeover RED baseline without changing authority

**Files:**
- Create: `docs/agent/UNIFIED_TASK3_SUCCESSOR_REPAIR_LEDGER_20261015.md`
- Modify: PR #392 body only if needed to add exact successor heads/results.

**Interfaces:**
- Consumes: Task 1 containment commits and Task 2 CI run/test failure identities.
- Produces: durable restart point for B1-B5 repair plans and later independent recheck.

- [ ] **Step 1: Record exact branch head, B6 containment commits, imported test path, CI run IDs, and failing test names**

- [ ] **Step 2: State explicitly that RED evidence grants no authority and Task 4 remains blocked**

- [ ] **Step 3: Verify PR #392 remains draft/rejected and no protected values were touched**
