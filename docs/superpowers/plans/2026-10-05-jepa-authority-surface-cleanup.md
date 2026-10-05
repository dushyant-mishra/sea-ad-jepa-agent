# JEPA Authority Surface Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make GitHub’s canonical navigation and authority surface accurately reflect the October 5 target-authority reset without deleting historical evidence.

**Architecture:** Preserve historical files and results, but replace files whose names explicitly claim current authority with concise October 5 routing. Add a repository audit ledger that separates current authority, superseded navigation, historical evidence, custody-only artifacts, and unresolved research lanes. Rewrite README claims that currently present an unqualified target architecture as current fact.

**Tech Stack:** Markdown, JSON, GitHub repository governance.

**Spec:** `docs/agent/JEPA_NEW_CHAT_HANDOFF_20261005_TARGET_AUTHORITY_RESET.md`

## Global Constraints

- V75 100K measurement architecture remains qualified only within its declared scope.
- `TRAINING=OFF`, multimodal training OFF, Stage 4 NOT AUTHORIZED, 500K NOT AUTHORIZED.
- No qualified production target winner exists.
- `width=160` is network/token capacity, not biological dimension authority.
- Preserve historical evidence; do not rewrite old result artifacts.
- Do not rerun August donor-centering; V6R5B already returned `RESIDUAL_TARGET_DOES_NOT_RESCUE`.

## Review Focus

- A new agent must not be routed to V21/V25/V66/V67 as current authority.
- Historical claims must remain available but visibly superseded.
- README must distinguish implemented runtime from scientifically qualified target/state.
- Custody artifacts must not be promoted to scientific authority.
- Current files must agree on target/training/500K/state boundaries.

---

### Task 1: Canonical startup routing

**Files:** Modify `START_HERE.md`, `docs/agent/CURRENT_AUTHORITY_INDEX.md`, `docs/agent/CURRENT_SUPERSESSION_MAP.md`, `docs/agent/memory-os/ACTIVE_STATE.md`.

- [ ] Replace obsolete current-state routing with the Oct 5 handoff/pointer/state/audit.
- [ ] Preserve compact links to historical authority rather than deleting it.
- [ ] Verify all four files agree on training, 500K, target, and V75 status.

### Task 2: README scientific correction

**Files:** Modify `README.md`.

- [ ] Remove claims that a query-self-masked contextual target or diagnostic-only BlockPredictor is the currently qualified production target architecture.
- [ ] State implemented runtime versus qualified scientific authority separately.
- [ ] Point status readers to the Oct 5 authority reset.

### Task 3: Repository audit ledger

**Files:** Create `docs/agent/JEPA_REPOSITORY_AUTHORITY_CLEANUP_AUDIT_20261005.md` and `.json`.

- [ ] Record high-risk stale files and corrected replacements.
- [ ] Record known retractions/supersessions (including PR #147 S9 -> PR #178 retraction).
- [ ] Record target-lineage terminal finding: PR #163 candidate space open; PR #178 synthetic comparison not informative; no target winner.
- [ ] Define PR/branch classification policy: CURRENT, SUPERSEDED, HISTORICAL_EVIDENCE, CUSTODY_ONLY, INCOMPLETE_STOPPED, DEFERRED.

### Task 4: Verification

- [ ] Re-fetch each modified file from the cleanup branch.
- [ ] Search modified current files for stale V21/V25/V66/V67 current-status language.
- [ ] Compare branch against its custody base and confirm only docs/governance files changed.
