# Unified Task 3 B2 Stage-Evidence Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close Macha T3-B2 by making stage advancement fail closed unless the destination stage is explicitly mapped to its evidence law and that evidence law is implemented.

**Architecture:** Add a closed destination-stage policy table in `registry_v1.py`. Mechanical stages may be explicitly marked as requiring no additional stage-specific evidence; `REAL_REFERENCE_READY` and `HUMAN_EXECUTABLE` retain their existing implemented gates; `KNOWN_TRUTH_QUALIFIED` and `HUMAN_EXECUTED` are bound to specific evidence classes that are not yet implemented and therefore fail closed. Any destination stage absent from the table also fails closed. Do not invent sealed-challenge or human-execution receipts merely to turn tests green.

**Tech Stack:** Python 3.11, pytest 9.1.1, existing Unified Task 3 registry.

**Spec:** Independent Macha review at `869ca777a498181c519ccfc04b8bf5db0f2888c7`, blocker T3-B2.

## Global Constraints

- Task 3 remains rejected until independent exact-head recheck accepts it.
- Task 4 remains blocked; therefore Task 4 evidence is not available to satisfy B2.
- Do not create fake/semi-semantic sealed challenge or execution receipts inside Task 3.
- Preserve B1/B4 partial-GREEN behavior.
- B3 and B5 remain intentionally RED after this batch.
- Unknown evidence classes and unmapped stages fail closed.

## Closed stage policy

Destination stages are classified as follows:

- `FIXTURE_SAME_INTERFACE`: explicitly mechanical; no additional stage-specific evidence beyond ordinary promotion identity/authority checks.
- `SAME_CODE_PATH`: explicitly mechanical; no additional stage-specific evidence beyond ordinary promotion identity/authority checks.
- `KNOWN_TRUTH_QUALIFIED`: requires `SEALED_CHALLENGE_REVIEW`; not implemented in Task 3, so promotion fails closed.
- `REAL_REFERENCE_READY`: implemented `REAL_REFERENCE_READY` prerequisite/dependency gate.
- `HUMAN_EXECUTABLE`: implemented reviewer + process-isolation + cross-process-custody + provenance gate.
- `HUMAN_EXECUTED`: requires `HUMAN_EXECUTION_RECEIPT`; not implemented in Task 3, so promotion fails closed.
- later downstream/training stages: not implemented in Task 3 and/or separately forbidden by frozen Task 1 UNIT authority law; stage-policy check remains fail closed.

This table is a custody rule, not evidence that the unavailable evidence classes exist.

---

### Task 1: Preserve both B2 attacks as RED

**Files:**
- Modify: `tests/v5/td_unified/test_registry_v1_macha_rejection.py`

- [ ] **Step 1: Keep H2 known-truth attack**

`SAME_CODE_PATH -> KNOWN_TRUTH_QUALIFIED` without sealed challenge/reviewer evidence must raise `RegistryError`.

- [ ] **Step 2: Add H2 human-executed attack**

`HUMAN_EXECUTABLE -> HUMAN_EXECUTED` without an authenticated human-execution receipt must raise `RegistryError`.

- [ ] **Step 3: Run focused B2 tests before production repair**

Expected: both fail because the current registry advances both stages based only on requested destination plus generic actor checks.

### Task 2: Implement closed stage-evidence policy

**Files:**
- Modify: `scripts/v5/td_unified/registry_v1.py`

- [ ] **Step 1: Add a closed stage-policy table**

Every legal destination stage must map to an explicit policy token. Missing/unknown policy tokens raise `RegistryError`.

- [ ] **Step 2: Enforce evidence-bearing unavailable stages fail closed**

For `KNOWN_TRUTH_QUALIFIED`, raise a refusal identifying required `SEALED_CHALLENGE_REVIEW` evidence as unavailable/unimplemented.

For `HUMAN_EXECUTED`, raise a refusal identifying required `HUMAN_EXECUTION_RECEIPT` evidence as unavailable/unimplemented.

- [ ] **Step 3: Preserve existing implemented gates**

`REAL_REFERENCE_READY` and `HUMAN_EXECUTABLE` continue through their current exact gates; do not weaken or duplicate them.

### Task 3: Verify partial GREEN without accidental authority expansion

- [ ] **Step 1: Run both B2 tests**

Expected: PASS.

- [ ] **Step 2: Run full focused Task 3 family**

Expected after B2 repair: only five B3 identity attacks plus H5/H6 B5 history attacks remain RED.

- [ ] **Step 3: Run dedicated frozen Task 2 suite and broader unified folder**

Expected dedicated Task 2 suite: green. Broader folder may remain red only on the seven intentionally unresolved Task 3 attacks.

- [ ] **Step 4: Record exact head/run/results in successor ledger**

Do not freeze Task 3 or advance Task 4.
