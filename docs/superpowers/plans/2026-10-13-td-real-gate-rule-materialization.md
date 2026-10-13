# TD Real Gate Rule Materialization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce the real-TD `RULE_NOT_MATERIALIZED` blocker by implementing only outcome-blind structural/provenance gates whose decision semantics are already fixed by the frozen tournament specification, while leaving unresolved quantitative gates explicitly blocked.

**Architecture:** Add a unique gate-rule registry keyed by the frozen gate universe, with one canonical rule reused across every candidate role. Only gates whose PASS/FAIL/NOT_ESTIMABLE semantics can be determined from frozen structural/provenance assertions without biological outcome values become callable; quantitative gates remain `BLOCKED_PROSPECTIVE_RULE_REQUIRED`. Regenerate the candidate×gate readiness projection from that registry without opening biological outcomes.

**Tech Stack:** Python 3.11, pytest, JSON/CSV contracts, existing TD V5 tournament modules.

**Spec:** `docs/superpowers/specs/2026-10-11-td-multitarget-tournament-prefreeze-v2.md` and the C6 extension bound by `scripts/v5/td_c6_candidate_extension_v1.py`.

## Global Constraints

- Donor remains the biological replication unit.
- Source/operator effects remain distinct from donor biology.
- Measured zero remains a valid measurement; structural unsupportedness abstains; imputation is forbidden.
- `NOT_ESTIMABLE` is never promoted to PASS or collapsed into FAIL.
- Historical descriptive cutoffs cannot become prospective thresholds.
- No current candidate outcomes may be opened to complete engineering.
- No candidate redesign, target selection, representation selection, TD60, Stage4, EMA or training authority is created.
- Composite gates cannot rescue failed constituents.

## Review Focus

- Missing structural evidence fails closed rather than being inferred.
- Any rule requiring an outcome-dependent numeric threshold remains blocked.
- One unique gate implementation is reused consistently across every candidate that requires it.
- Candidate-specific mandatory falsifiers and support semantics remain unchanged.
- The readiness projection cannot accidentally make real-tournament QUALIFY eligible.

---

### Task 1: Unique gate-rule registry

**Files:**
- Create: `scripts/v5/td_real_gate_rule_registry_v1.py`
- Test: `tests/v5/test_td_real_gate_rule_registry_v1.py`

**Interfaces:**
- Consumes: gate catalogs from `td_real_tournament_contract_v1.py`.
- Produces: `RULES`, `validate_rule_registry()`, `evaluate_structural_gate()` and deterministic rule hashes.

- [ ] Write RED tests proving exact 33-gate coverage, exact callable structural subset, no numeric thresholds on blocked gates, fail-closed missing evidence and PASS/FAIL behavior for every callable structural gate.
- [ ] Implement the minimal registry and validators.
- [ ] Run focused tests and self-audit the production diff against the frozen spec.
- [ ] Fix any drift and rerun.

### Task 2: Readiness projection V2

**Files:**
- Create: `scripts/v5/audit_td_real_gate_executor_readiness_v2.py`
- Create: `results/target_discovery/real_tournament/TD_REAL_GATE_EXECUTOR_READINESS_MATRIX_V2.csv`
- Create: `results/target_discovery/real_tournament/TD_REAL_GATE_EXECUTOR_READINESS_MATRIX_V2_SUMMARY.json`
- Test: `tests/v5/test_td_real_gate_executor_readiness_v2.py`

**Interfaces:**
- Consumes: Task 1 registry plus frozen candidate gate sets.
- Produces: outcome-blind 198-row candidate×gate readiness projection.

- [ ] Write RED projection tests for exact Cartesian coverage, role counts, donor/source/support invariants and authority false.
- [ ] Project callable structural roles as `CALLABLE_NEEDS_QUALIFICATION`; keep quantitative roles `RULE_NOT_MATERIALIZED`; non-required rows remain `NOT_APPLICABLE`.
- [ ] Assert real-tournament QUALIFY remains false whenever any required role is not `CALLABLE_AND_QUALIFIED`.
- [ ] Run focused tests and self-audit matrix-to-contract consistency.
- [ ] Fix any mismatch and rerun.

### Task 3: Historical-equivalence recovery ledger

**Files:**
- Create: `results/target_discovery/real_tournament/TD_REAL_GATE_HISTORICAL_EQUIVALENCE_V1.json`
- Create: `docs/agent/TD_REAL_GATE_HISTORICAL_EQUIVALENCE_AUDIT_20261013.md`
- Test: `tests/v5/test_td_real_gate_historical_equivalence_v1.py`

**Interfaces:**
- Consumes: repository code/history only, not candidate outcomes.
- Produces: per-gate evidence of whether an existing callable computation implements the same frozen estimand.

- [ ] Record exact path/hash and equivalence rationale where recoverable.
- [ ] Mark non-equivalent or incomplete historical computations without promoting them.
- [ ] Never copy historical descriptive cutoffs into decision rules.
- [ ] Run schema/invariant tests and self-audit all claimed equivalences.

### Task 4: Qualification packet for callable structural rules

**Files:**
- Create: `docs/agent/TD_REAL_STRUCTURAL_GATE_QUALIFICATION_PACKET_20261013.md`
- Create: `.github/workflows/td-real-structural-gates-qualification.yml`

**Interfaces:**
- Consumes: Tasks 1–3.
- Produces: outcome-blind qualification harness only; no biological execution.

- [ ] Run structural rule unit tests plus existing PR #313 tournament framework suites.
- [ ] Bind exact head and artifact hashes.
- [ ] Confirm no biological outcome namespace is accessed.
- [ ] STOP with `CALLABLE_NEEDS_QUALIFICATION` or, after independent qualification evidence, `CALLABLE_AND_QUALIFIED`; do not authorize real TD.
