# V5 Governance and FULL104 Handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reconcile the current V5 implementation/science line into one auditable branch, update governance so stale September 15 state cannot restart closed work, and prepare a code-audited FULL104 execution package for Claude.

**Architecture:** Integrate only reviewed successor commits into the live analysis line, preserve historical branches for provenance, update pointers/state docs to exact commits, and use immutable run manifests for every FULL104 canary/long execution.

**Tech Stack:** Git/GitHub, JSON/Markdown governance files, pytest/GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-17-v5-production-authority-closure-design.md`

## Global Constraints

- Do not delete historical branches before supersession mapping.
- Do not rewrite frozen historical artifacts in place.
- Full-data runs execute from immutable reviewed SHAs only.
- No long run before code audit and deterministic canary.

---

### Task 1: Integrate semantic successor PR

**Files:** Existing PR #18 and current analysis branch.

- [ ] **Step 1:** Verify PR #18 mergeability, changed files and latest CI.
- [ ] **Step 2:** Verify source/test bytes after the last green CI changed only by documentation/plans or rerun CI if source changed.
- [ ] **Step 3:** Mark ready and merge into `analysis/v5-ridge8-expanded-validation-20260917` using expected head SHA.
- [ ] **Step 4:** Re-fetch live analysis head and compare to both PR head and `handoff/v5-masking-successor-ridge8-20260917`.
- [ ] **Step 5:** Record any hardening still absent from the integrated branch before closing the handoff lane.

### Task 2: Current work checkpoint and authority ledger

**Files:**
- Update: `START_HERE.md`
- Update: `docs/agent/JEPA_LATEST_HANDOFF_POINTER.json`
- Create/update current state/handoff files dated 20260917.
- Update current authority/supersession ledgers if they remain stale.

- [ ] **Step 1:** Generate or require canonical-worktree `CURRENT_WORK_CHECKPOINT.json` according to repository governance; do not fabricate machine/worktree-bound values from the connector.
- [ ] **Step 2:** Classify every residual blocker as CLOSED, OPEN_AUTHORITY, GPU_EXECUTION_REQUIRED, DEFERRED_GEOMETRY or TRAINING_LOCKED.
- [ ] **Step 3:** Update governance so it states VALUE_ONLY_256/support/base estimand/Stage-A/current address provider and semantic successor accurately.
- [ ] **Step 4:** Keep masking scientific authority and remaining-RNA healthy execution explicitly open until FULL104 qualification.
- [ ] **Step 5:** Commit docs-only governance update after code branch is stable.

### Task 3: FULL104 read-only census contract

**Files:**
- Create: `docs/agent/V5_FULL104_SUPPORT_PRECISION_CENSUS_CONTRACT_20260917.json`
- Create: `analysis/v5_full104_census_20260917/validate_census_contract.py`

- [ ] **Step 1:** Bind FULL104 manifest `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`, VALUE_ONLY_256, support/estimability and canonical registry roots.
- [ ] **Step 2:** Require output counts for donor/source/address support, measured-zero versus missing, target×fold support, feasible burdens and precision inputs.
- [ ] **Step 3:** Explicitly forbid masking qualification outcomes, protected labels and training.
- [ ] **Step 4:** Unit-test validator and commit before Claude execution.

### Task 4: Immutable Claude run manifest

**Files:**
- Create: `docs/agent/V5_FULL104_EXECUTION_MANIFEST_SCHEMA_20260917.json`
- Create: `analysis/v5_full104_execution/validate_execution_manifest.py`

- [ ] **Step 1:** Require branch, commit SHA, source-root SHA, immutable input paths/sizes/SHA256, Python/environment, command line, output directory and protected-outcome declaration.
- [ ] **Step 2:** Require canary status before long-run status can become executable.
- [ ] **Step 3:** Require output artifact SHA256s and exact row/count reconciliation.
- [ ] **Step 4:** Test malformed/missing fields and commit.

### Task 5: Branch/supersession cleanup after integration

- [ ] **Step 1:** Compare current integrated branch against handoff/schema-hardening branches.
- [ ] **Step 2:** Mark branches fully subsumed as superseded in the register; do not delete if they contain unique historical evidence.
- [ ] **Step 3:** Keep one named current implementation/science branch and one docs-only handoff pointer.
- [ ] **Step 4:** Update the next-chat handoff to forbid replay of closed audits and point to exact remaining data-dependent executions.
