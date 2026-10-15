# Unified Task 3 B5 History Custody Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close T3-B5 by making advanced Task 3 qualification depend on a harness-owned, append-only history custody object that can distinguish lawful history from caller-rebuilt registry tuples.

**Architecture:** Follow frozen Task 2's `HarnessAccessRegistry` trust pattern: a private-key-bearing custody object is initialized only from a history-free pre-advanced genesis, records exact promotion/revocation transitions as they occur, and later validates that a presented registry's history and current unit state match its externally held event chain. Existing registry receipts remain the durable in-registry evidence; custody supplies the missing external authority. Direct prerequisite additions may change the registry payload but do not become history events. Advanced consumption (`HUMAN_EXECUTABLE`) and advanced revocation must fail closed without matching custody.

**Tech Stack:** Python 3.11, dataclasses, HMAC/SHA-256, pytest 9.1.1.

**Spec:** `docs/agent/MACHA_UNIFIED_TASK3_INDEPENDENT_REVIEW_851544E8_20261015.md` on independent review head `869ca777a498181c519ccfc04b8bf5db0f2888c7`.

## Global Constraints

- Frozen Task 0–2 production authority remains untouched.
- Preserve Macha H5/H6 attack semantics: fabricated RRR history and deleted revocation must fail even when the attacker presents otherwise valid actors/dependencies.
- Custody authority must live outside `TDQualificationRegistry`; a digest or tuple supplied by the registry/caller cannot be the sole trust root.
- Genesis must be history-free and may not start with a unit beyond `KNOWN_TRUTH_QUALIFIED`.
- Existing one-stage promotion, Task 2 exact-row binding, actor-registry, B1/B2/B4 and B6 behavior must remain unchanged.
- No Task 4 work or protected biological values.

## Review Focus

- Fresh custody created from an already advanced/fabricated registry must be rejected.
- Deleting a previously recorded revocation must be detected even if the unit is manually reset ACTIVE.
- Fabricating an internally consistent promotion receipt must be detected if custody never recorded it.
- Adding HUMAN_EXECUTABLE prerequisites after a lawful RRR promotion must not invalidate history solely because prerequisites changed.
- A custody object must not accept a transition whose pre-state is not its currently recorded history state.

---

### Task 1: Preserve B5 attacks against the new trust boundary

**Files:**
- Modify: `tests/v5/td_unified/test_registry_v1_macha_rejection.py`
- Create: `tests/v5/td_unified/test_registry_v1_history_custody.py`

**Interfaces:**
- Produces: expected `RegistryHistoryCustody` behavior used by Task 2.

- [ ] Add a lawful synthetic custody object before the RRR transition in H5/H6 setup.
- [ ] Pass custody through the lawful RRR/revocation transitions, then present the same custody to the forged/deleted-history promotion attempt.
- [ ] Add focused tests for advanced-genesis rejection, unrecorded fabricated event rejection, recorded-revocation deletion rejection, and lawful RRR → prerequisite-addition → HUMAN_EXECUTABLE validation.
- [ ] Run focused tests and verify RED because `RegistryHistoryCustody`/history integration does not exist.

### Task 2: Implement harness-owned history custody

**Files:**
- Modify: `scripts/v5/td_unified/registry_v1.py`

**Interfaces:**
- Produces: `RegistryHistoryCustody(genesis_registry, *, attestation_key: bytes)`, `validate_current(registry)`, and internal transition recording used by registry mutation functions.

- [ ] Implement a private HMAC-attested event chain initialized from an exact, history-free, pre-advanced genesis.
- [ ] Validate event prefixes, exact promotion/revocation receipt identities, actor-registry binding and current unit-state identity against custody-held state.
- [ ] Permit non-history prerequisite changes without treating them as transition events.
- [ ] On a supplied custody object, have `promote_unit`/`revoke_or_supersede` validate the pre-state and record the exact post-transition state.
- [ ] Require matching custody for `HUMAN_EXECUTABLE` promotion and for revocation/supersession of an RRR-or-higher unit.
- [ ] Make `derive_real_reference_ready` fail closed on a registry that already carries promotion/revocation history unless matching custody is supplied.

### Task 3: Restore inherited fixtures without weakening custody

**Files:**
- Modify only tests/fixtures that lawfully exercise advanced history.

- [ ] Bind one synthetic custody object at the lawful genesis and thread the same object through lawful advanced transitions.
- [ ] Do not initialize custody from an already advanced registry merely to make a test pass.
- [ ] Run focused Task 3 suite; expected 0 failures if B5 closes without regressions.

### Task 4: Exact-head regression and independent-review package

**Files:**
- Update: `docs/agent/UNIFIED_TASK3_SUCCESSOR_REPAIR_LEDGER_20261015.md`
- Update PR #322/#323 custody/navigation surfaces.

- [ ] Run focused Task 3 suite, full `tests/v5/td_unified`, Task 2 workflow/regression, Task 1 workflow/regression, Task 0 workflow/regression, B6 policy and unified synthetic integration on one exact head.
- [ ] Remove dead `asserted_ready` and `prerequisite_evidence_verifier` parameters only after B1–B6 behavior is green, with dedicated API-regression tests.
- [ ] Audit diff proving frozen Task 0–2 production files are untouched.
- [ ] Request focused independent Macha B1–B6 recheck only; do not claim Task 3 accepted before that review.
