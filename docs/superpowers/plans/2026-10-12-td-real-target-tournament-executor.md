# Real Target-Tournament Executor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the already-qualified C1/C2/C3/C6/C4/C5 target definitions and falsifier rules into a physical donor-primary real-data evaluator that produces raw sufficient statistics and exact gate statuses consumable by the existing routing/convergence machinery, without selecting a target.

**Architecture:** Candidate science remains in prospectively frozen candidate definitions. A shared case ledger fixes donor/source/operator/support partitions and falsifier identities before outcomes; small candidate adapters expose only candidate-specific target construction/evaluation; a gate evaluator emits raw evidence plus PASS/FAIL/NOT_ESTIMABLE; a bundle validator then hands statuses to `td_target_tournament_routing_v4.py` and `td_target_convergence_v1.py`. No aggregate score or winner is created here.

**Tech Stack:** Python 3.11, NumPy/Pandas/SciPy/scikit-learn as already pinned by the target-discovery qualification workflow, pytest, JSON/NPZ receipts.

**Spec:** `docs/superpowers/specs/2026-10-12-td-downstream-turnkey-gates-design.md`

## Global Constraints

- Foundation candidates are exactly `C1_SHARED_EMERGENT`, `C2_RELATIONAL_SHARED`, `C3_QUERY_MEASURED`, `C6_SHARED_QUERY_COMPOSITE`, `C4_STRUCTURED_COMPOSITE`; `C5_REGULATORY_SPECIALIST` is specialist-only.
- Candidate dependencies remain C6←C1+C3 and C4←C2+C3.
- Relational replay only directly gates C2/C4. C1/C3/C6 remain independently adjudicable according to routing V4.
- Donor is the primary biological replication unit; source/acquisition is an observation operator.
- Measured zero is valid; structurally unsupported is abstention. No modality imputation is introduced.
- Mandatory falsifiers include constant/train-mean, technical/operator-only, address/support/operator shortcut, matched wrong-cell, fine-neighborhood wrong-cell, q-count-only, q-address-only, query-agnostic, wrong-q, technical+q, q-excluded teacher, and identity+support-only.
- Synthetic evidence is not consumed by this executor.
- No average score, rank sum, post-hoc weighting, best-loser rescue, threshold relaxation, or target authority.
- `target_selected=false`, `representation_selected=false`, `td60_authorized=false`, `stage4_authorized=false`, `training_authorized=false` in every output.

## Review Focus

1. Donor leakage across train/evaluation partitions.
2. Source/operator weighting accidentally treated as biological replication.
3. Unsupported entries silently becoming zero/imputed values.
4. Candidate adapter seeing fields forbidden by its frozen target definition.
5. Falsifier incompleteness/cherry-picking.

---

### Task 1: Freeze real-tournament execution contract and candidate registry

**Files:**
- Create: `results/target_discovery/real_tournament/TD_REAL_TOURNAMENT_CONTRACT_V1.json`
- Create: `scripts/v5/td_real_tournament_contract_v1.py`
- Test: `tests/v5/test_td_real_tournament_contract_v1.py`

**Interfaces:**
- Produces `load_real_tournament_contract() -> dict`, `validate_candidate_registry(contract: dict) -> dict` and exact candidate→required-component→required-gate→mandatory-falsifier mappings.

- [ ] Write RED tests asserting exact candidate set, dependencies, falsifier completeness, donor-primary/source-operator law, support semantics, and all no-authority flags.
- [ ] Run `pytest -q tests/v5/test_td_real_tournament_contract_v1.py` and preserve RED.
- [ ] Implement minimal contract validator and frozen JSON.
- [ ] Run focused tests GREEN.
- [ ] Commit `td: freeze real target tournament execution contract`.

### Task 2: Build immutable donor-primary case ledger

**Files:**
- Create: `scripts/v5/td_real_tournament_case_ledger_v1.py`
- Test: `tests/v5/test_td_real_tournament_case_ledger_v1.py`

**Interfaces:**
- Consumes authenticated real-data metadata/support only.
- Produces `build_case_ledger(metadata, support, contract) -> CaseLedger` with immutable case IDs, donor blocks, source/operator labels, support states, q identities, and predeclared falsifier pairing IDs.

- [ ] Write RED tests for donor-disjoint partitions, deterministic ledger identity, measured-zero/support distinction, source/operator retention, matched-wrong-cell and fine-neighborhood pair construction, and refusal when no legal falsifier partner exists.
- [ ] Run RED.
- [ ] Implement metadata/support-only ledger builder; no target outcome calculation.
- [ ] Run GREEN.
- [ ] Commit.

### Task 3: Implement candidate adapters with field firewalls

**Files:**
- Create: `scripts/v5/td_real_candidate_adapters_v1.py`
- Test: `tests/v5/test_td_real_candidate_adapters_v1.py`

**Interfaces:**
- Produces one adapter for C1/C2/C3/C6/C4/C5 under `build_candidate_payload(candidate_id, case_ledger, observations, replay_context) -> CandidatePayload`.

- [ ] Write RED tests that each candidate receives exactly its frozen components and that C1/C3/C6 cannot accidentally consume relational evidence; C5 cannot be routed as a foundation rescue.
- [ ] Run RED.
- [ ] Implement the adapters as thin composition layers over frozen target constructors; do not invent new target statistics.
- [ ] Run GREEN.
- [ ] Commit.

### Task 4: Implement mandatory falsifier engine

**Files:**
- Create: `scripts/v5/td_real_tournament_falsifiers_v1.py`
- Test: `tests/v5/test_td_real_tournament_falsifiers_v1.py`

**Interfaces:**
- Consumes CandidatePayload + CaseLedger.
- Produces `run_falsifiers(...) -> dict[str, RawFalsifierEvidence]` covering the complete mandatory set prospectively attached to that candidate.

- [ ] Write RED tests for all named falsifiers, deterministic matching, support-safe shuffles, donor/source boundaries, and refusal of incomplete evidence sets.
- [ ] Run RED.
- [ ] Implement falsifiers without altering candidate target construction.
- [ ] Run GREEN.
- [ ] Commit.

### Task 5: Implement candidate gate evaluator

**Files:**
- Create: `scripts/v5/td_real_tournament_gates_v1.py`
- Test: `tests/v5/test_td_real_tournament_gates_v1.py`

**Interfaces:**
- Produces `evaluate_candidate(candidate_id, payload, falsifier_evidence, contract) -> CandidateGateReceipt` containing raw sufficient statistics plus exact per-gate `PASS|FAIL|NOT_ESTIMABLE`.

- [ ] Write RED tests pinning gate grammar, donor-primary aggregation, source disagreement behavior, shortcut failure, uncertainty/support reporting, and NOT_ESTIMABLE propagation.
- [ ] Run RED.
- [ ] Implement only prospectively frozen thresholds/rules; thresholds live in contract, never computed from observed outcomes.
- [ ] Run GREEN.
- [ ] Commit.

### Task 6: Build QUALIFY / EXECUTE_ONCE real-tournament stage controller

**Files:**
- Create: `scripts/v5/run_td_real_target_tournament_once.py`
- Create: `scripts/v5/run_td_real_target_tournament_once.sh`
- Test: `tests/v5/test_run_td_real_target_tournament_once.py`

**Interfaces:**
- QUALIFY authenticates corrected-replay prerequisites, candidate registry, metadata/support, case ledger and executor hashes without computing biological target results.
- EXECUTE_ONCE requires fresh tournament-only authority and writes start marker before candidate outcome-bearing evaluation.

- [ ] Write RED tests for stale/missing replay context, relational-dependent candidate blocks, fresh namespace, one-shot authority, QUALIFY no-outcome behavior, and forbidden downstream flags.
- [ ] Run RED.
- [ ] Implement fail-closed controller.
- [ ] Run GREEN.
- [ ] Commit.

### Task 7: Validate bundle and connect to existing routing/convergence

**Files:**
- Create: `scripts/v5/td_real_tournament_bundle_v1.py`
- Test: `tests/v5/test_td_real_tournament_bundle_v1.py`

**Interfaces:**
- Produces `validate_bundle(namespace: Path) -> dict` and exact `candidate_statuses` object accepted by `td_target_tournament_routing_v4.py`; later convergence consumes those statuses without re-reading raw biology.

- [ ] Write RED tests for zero/one/multiple/unresolved candidate patterns, C6/C4 parent dependency, C5 specialist isolation, tamper detection, and no-authority outputs.
- [ ] Run RED.
- [ ] Implement validator/projection.
- [ ] Run `pytest -q tests/v5/test_td_real_tournament_bundle_v1.py tests/v5/test_td_target_tournament_routing_v4_c6.py tests/v5/test_td_target_convergence_v1.py` GREEN.
- [ ] Commit.

### Task 8: Add focused CI and outcome-blind real-file qualification

**Files:**
- Create/modify: `.github/workflows/td-target-tournament-qualification.yml`
- Create: `docs/agent/TD_REAL_TOURNAMENT_EXECUTOR_QUALIFICATION_20261012.md`

- [ ] Add Tasks 1–7 tests and clean-worktree assertions to focused CI.
- [ ] Run real-file QUALIFY against exact authenticated metadata/support/replay inputs without producing candidate outcomes.
- [ ] Freeze implementation/contract/launcher hashes, run/job/artifact IDs and negative-case results.
- [ ] Require terminal `PASS_TD_REAL_TOURNAMENT_EXECUTOR_QUALIFICATION__NO_REAL_CANDIDATE_RESULTS__EXECUTION_AUTHORITY_REQUIRED`.
- [ ] STOP before real tournament execution.

## Self-Review Outcome

All candidate/falsifier/gate science is inherited from frozen target-discovery designs; this plan closes only the physical execution and evidence interfaces. Every high-risk leakage/support/replication failure has an owning negative test. No task creates a target winner.