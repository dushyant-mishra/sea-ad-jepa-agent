# TD V79 Synthetic Crosswalk Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement and qualify a fail-closed target-discovery adapter that maps V79 Q00-Q11 truth to C1-C5 target claims without allowing synthetic evidence to create biological authority.

**Architecture:** A frozen JSON registry defines the candidate×world claim matrix. A small standard-library validator/combiner authenticates the registry, combines real and synthetic statuses asymmetrically, and emits foundation contingency terminals. Existing target-tournament CI exercises the implementation; no V79 world generation or biological execution is performed.

**Tech Stack:** Python 3.11 standard library, JSON, pytest, existing GitHub Actions target-tournament qualification workflow.

**Spec:** `docs/superpowers/specs/2026-10-12-td-v79-synthetic-crosswalk-design.md`

## Global Constraints

- Keep V79 synthetic and target-discovery execution authorities separate.
- Do not open or generate synthetic qualification outcomes.
- Do not authorize corrected replay, target selection, TD60, Stage4, representation selection or training.
- Synthetic PASS never overrides real FAIL or NOT_ESTIMABLE.
- Only truth-backed decisive synthetic failures may eliminate a real-PASS candidate.
- Current missing C1 shared-latent, C2 relational, C3 query-biological, C4 increment and C5 regulatory truths remain NOT_ESTIMABLE.
- C4 cannot rescue failed/unresolved C2 or C3.
- C5 never changes the foundation-target terminal.

## Review Focus

- A decisive entry with empty truth bindings must be rejected.
- An unknown or missing Q00-Q11 world/candidate must be rejected.
- Synthetic PASS presented against real FAIL/NOT_ESTIMABLE must not rescue the candidate.
- C4 must not become eligible when C2 or C3 is ineligible/unresolved.
- Q10/Q11 operator evidence must require the canonical paired rule rather than independent single-world evidence.

---

### Task 1: Frozen registry and structural validator

**Files:**
- Create: `results/target_discovery/synthetic_crosswalk/TD_V79_SYNTHETIC_CROSSWALK_V1.json`
- Create: `scripts/v5/td_v79_synthetic_crosswalk_v1.py`
- Create/Test: `tests/v5/test_td_v79_synthetic_crosswalk_v1.py`
- Modify: `.github/workflows/td-target-tournament-qualification.yml`

**Interfaces:**
- Produces: `load_crosswalk(path) -> dict`, `validate_crosswalk(crosswalk) -> None`, constants for exact candidates/worlds/evidence classes.

- [ ] Write tests first for exact registries, authority-off flags, decisive truth binding, mandatory NOT_ESTIMABLE claims, Q10/Q11 pairing and malformed-registry rejection.
- [ ] Run CI and observe RED because the module/registry do not yet exist.
- [ ] Implement the frozen JSON registry and minimal validator.
- [ ] Run focused CI and require all tests green.

### Task 2: Real + synthetic candidate combiner

**Files:**
- Modify: `scripts/v5/td_v79_synthetic_crosswalk_v1.py`
- Modify/Test: `tests/v5/test_td_v79_synthetic_crosswalk_v1.py`

**Interfaces:**
- Produces: `combine_candidate_evidence(candidate_id, real_status, synthetic_results, crosswalk) -> str`.

- [ ] Add failing tests proving real FAIL and NOT_ESTIMABLE cannot be rescued, real PASS with decisive synthetic FAIL is eliminated, and diagnostic/NOT_ESTIMABLE synthetic cells cannot eliminate/promote by themselves.
- [ ] Observe RED.
- [ ] Implement minimal asymmetric combiner.
- [ ] Run focused CI green.

### Task 3: Foundation contingency adjudicator

**Files:**
- Modify: `scripts/v5/td_v79_synthetic_crosswalk_v1.py`
- Modify/Test: `tests/v5/test_td_v79_synthetic_crosswalk_v1.py`
- Create: `docs/agent/TD_V79_SYNTHETIC_CROSSWALK_QUALIFICATION_20261012.md`

**Interfaces:**
- Consumes candidate statuses from Task 2.
- Produces: `adjudicate_foundation(candidate_statuses, specialist_status=None) -> dict`.

- [ ] Add failing tests for zero, one and multiple eligible foundation candidates; C4 dependency on C2+C3; C5 specialist separation.
- [ ] Observe RED.
- [ ] Implement minimal contingency adjudicator.
- [ ] Run the full target-tournament focused qualification harness.
- [ ] Record exact head/run/test count in qualification note; retain hard terminal and no-authority flags.

## Completion contract

The work is complete only when the exact implementation head has a green target-tournament qualification run including `test_td_v79_synthetic_crosswalk_v1.py`, the registry validates fail-closed, and no synthetic/real biological execution has occurred.
