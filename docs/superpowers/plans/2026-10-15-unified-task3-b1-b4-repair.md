# Unified Task 3 B1+B4 Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close Macha T3-B1 and T3-B4 without changing any Task 0-2 frozen authority, stage-evidence law, actor-registry law, or history-custody design.

**Architecture:** Make `promote_unit` validate its proposed post-promotion authority through frozen Task 1 `validate_authority_record`, preserving `NO_TRAINING_AUTHORITY` as a hard ceiling. Make readiness/dependency memoization call-owned only: keep the legacy public cache parameter temporarily for API compatibility, but never read or write caller cache as authority; recursive checks share a fresh internal cache created by the top-level call.

**Tech Stack:** Python 3.11, pytest 9.1.1, existing `scripts.v5.td_unified.authority_v1` and `registry_v1`.

**Spec:** `docs/agent/MACHA_UNIFIED_TASK3_INDEPENDENT_REVIEW_851544E8_20261015.md` at review head `869ca777a498181c519ccfc04b8bf5db0f2888c7`.

## Global Constraints

- Task 3 remains rejected until independent exact-head recheck accepts it.
- Task 4 remains blocked.
- Do not touch Task 0-2 frozen files.
- Do not weaken `test_registry_v1_macha_rejection.py` to obtain GREEN.
- Preserve prerequisite-graph and exact Task 2 binding behavior already accepted by Macha.
- B2, B3, and B5 must remain visibly RED after this batch; partial GREEN is the expected result.

## Review Focus

- `UNIT:*` may not cross the frozen Task 1 UNIT stage ceiling.
- `NO_TRAINING_AUTHORITY` may not be bypassed by direct stage advancement.
- A caller-prepopulated cache must not authenticate anything.
- Cache entries from resolver A must not authenticate resolver B.
- Recursive dependency verification must still deduplicate safely within one top-level call.

---

### Task 1: Enforce frozen Task 1 authority law on promotion (T3-B1)

**Files:**
- Modify: `scripts/v5/td_unified/registry_v1.py`
- Test: `tests/v5/td_unified/test_registry_v1_macha_rejection.py::test_h1_unit_scope_cannot_promote_beyond_human_executed`

**Interfaces:**
- Consumes: `AuthorityRecord`, `validate_authority_record`, and `AuthorityError` from frozen Task 1 authority module.
- Produces: `_validate_promoted_authority(unit, destination_stage)` fail-closed helper used by every promotion.

- [ ] **Step 1: Verify H1 is RED on the current successor head**

Run: `python -m pytest -q tests/v5/td_unified/test_registry_v1_macha_rejection.py::test_h1_unit_scope_cannot_promote_beyond_human_executed`
Expected: FAIL because `DOWNSTREAM_CERTIFIED` is currently accepted for a `UNIT:G8` record.

- [ ] **Step 2: Implement the smallest authority validation helper**

Construct the proposed post-promotion `AuthorityRecord` from the registry unit and destination stage; call frozen Task 1 `validate_authority_record`; translate `AuthorityError` to `RegistryError`. Explicitly refuse any `TRAINING_ELIGIBLE` or `TRAINING_AUTHORIZED` destination while `NO_TRAINING_AUTHORITY` is present.

- [ ] **Step 3: Run H1**

Expected: PASS with an authority/scope refusal.

- [ ] **Step 4: Run inherited Task 3 tests excluding the still-RED Macha rejection file**

Run: `python -m pytest -q tests/v5/td_unified/test_registry_v1.py tests/v5/td_unified/test_registry_v1_hostile_cycle*.py tests/v5/td_unified/test_registry_v1_self_audit*.py`
Expected: PASS.

### Task 2: Make dependency memoization internal per top-level call (T3-B4)

**Files:**
- Modify: `scripts/v5/td_unified/registry_v1.py`
- Test: `tests/v5/td_unified/test_registry_v1_macha_rejection.py::{test_h3_caller_poisoned_cache_cannot_authenticate_missing_dependencies,test_h4_warmed_positive_cache_cannot_survive_resolver_change}`

**Interfaces:**
- Consumes: existing recursive `_evaluate_unit(... verification_cache=...)` internal plumbing.
- Produces: top-level readiness/promotion calls allocate a fresh internal verification cache; supplied legacy `verification_cache` is non-authoritative and untouched.

- [ ] **Step 1: Verify H3/H4 are RED on the current successor head**

Run both named tests.
Expected: both FAIL with `ready=True` despite missing/changed resolver evidence.

- [ ] **Step 2: Allocate call-owned verification context**

At every public top-level entry that can authenticate dependencies, allocate a fresh dictionary and pass that dictionary through recursive verification. Do not seed from, read, or persist into caller-provided `verification_cache`.

- [ ] **Step 3: Run H3/H4**

Expected: PASS; empty resolver produces blockers even with caller cache contents.

- [ ] **Step 4: Run inherited Task 3 tests excluding still-RED Macha blockers**

Expected: PASS.

### Task 3: Partial-GREEN verification and custody update

**Files:**
- Modify: `docs/agent/UNIFIED_TASK3_SUCCESSOR_REPAIR_LEDGER_20261015.md`

**Interfaces:**
- Consumes: exact B1/B4 repair commits and CI results.
- Produces: auditable statement that B1/B4 are locally/CI mechanically closed while B2/B3/B5 remain open and Task 3 remains rejected.

- [ ] **Step 1: Run the full focused Task 3 test family**

Run: `python -m pytest -q tests/v5/td_unified/test_registry_v1*.py`
Expected: B1 and B4 tests pass; B2, five B3 aliases/self-mint, H5, and H6 remain failing. Existing controls/inherited tests remain green.

- [ ] **Step 2: Record exact head/run/results in the successor ledger**

- [ ] **Step 3: Do not freeze or advance Task 4**
