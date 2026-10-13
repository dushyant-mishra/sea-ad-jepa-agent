# TD Real Directional + Structural Gates V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Materialize and mechanically qualify only the 15 PR #338 Scientific Amendment V2-cleared directional/structural real-TD gate rules while keeping the 13 substantive magnitude/stability/increment/transfer/coverage rules hard-blocked.

**Architecture:** Add one authenticated V2 gate-executor module that composes existing donor-primary statistical helpers and frozen falsifier evidence without redefining blocked biology. Add a V2 readiness/audit projection that promotes only the 15 cleared rule IDs to callable/qualified after outcome-blind qualification and leaves all 13 blocked rules unchanged. No real candidate values are consumed.

**Tech Stack:** Python 3.11, pytest, existing `td_real_quantitative_components_v1.py`, existing tournament/falsifier contracts, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-13-td-real-gate-prospective-contracts-scientific-amendment-v2.md`

## Global Constraints

- Donor is the biological replication unit.
- Source/operator is an observation process, not a biological replicate.
- `MEASURED_ZERO` remains a valid measurement; `STRUCTURALLY_UNSUPPORTED` remains abstention; imputation is forbidden.
- `NOT_ESTIMABLE` is never promoted to PASS.
- Non-compensation is mandatory across required subtests/strata.
- Class-A implementation scope is exactly: G3, G4, G5, G10, S3, R3, Q4-Q8, M1-M4.
- G2, G6, G7, G8, G9, G11, G12, S1, S2, R1, R4, C6 increment, C4 increment remain `BLOCKED_PROSPECTIVE_RULE_REQUIRED`.
- No blocked gate may fall back to direction-only significance.
- No biological candidate outcomes may be opened.
- No real TD, target selection, representation selection, TD60, production EMA, Stage4, or training authority may be created.

## Review Focus

- Relational G3 must require B3 plus B4 where B4 is lawfully applicable; unavailable lawful B4 must propagate NE rather than disappear.
- G5 must enforce the exact HVS/NPH52/SEA_AD required-source set without pooled rescue.
- G10 must require every candidate-mandatory falsifier and refuse extra/missing runtime sets that drift from the frozen candidate contract.
- M1-M4 must remain structural/provenance decisions only; they must not infer regulatory truth or causal biology.
- V2 readiness projection must never promote any of the 13 blocked gates, even if generic directional helper inputs are supplied.

---

### Task 1: V2 directional executor core

**Files:**
- Create: `scripts/v5/td_real_directional_gate_executors_v2.py`
- Create: `tests/v5/test_td_real_directional_gate_executors_v2.py`

**Interfaces:**
- Consumes: `td_real_quantitative_components_v1.directional_donor_contrast`, `noncompensating_status`, frozen candidate/falsifier registry.
- Produces: `evaluate_directional_gate(gate_id: str, evidence: Mapping, *, alpha_family: float = 0.01) -> dict` and canonical rule metadata for G3/G4/G10/S3/R3/Q4-Q8.

- [ ] Write RED tests for exact allowed gate IDs, donor-primary directional PASS/FAIL/NE, non-compensation, and refusal of blocked gates.
- [ ] Run focused tests; expected failure is missing V2 executor module/symbols.
- [ ] Implement minimal gate-specific evidence schemas and exact subtest aggregation.
- [ ] Re-run focused tests; all Task-1 tests PASS.
- [ ] Self-audit against V2 amendment; confirm no magnitude language or blocked gate fallback exists.
- [ ] Commit Task 1.

### Task 2: Source replication and exact falsifier applicability

**Files:**
- Modify: `scripts/v5/td_real_directional_gate_executors_v2.py`
- Modify: `tests/v5/test_td_real_directional_gate_executors_v2.py`

**Interfaces:**
- Consumes: frozen current source set HVS/NPH52/SEA_AD, candidate `mandatory_falsifiers` from tournament contract.
- Produces: exact G5 source-stratified adjudication and G10 frozen-falsifier-set adjudication.

- [ ] Add RED tests proving no source pooling/rescue, exact source set, missing source -> NE/fail-closed per evidence contract, and exact candidate-mandatory falsifier set enforcement.
- [ ] Run focused tests and confirm expected RED failures.
- [ ] Implement minimal G5/G10 logic using donor-primary helper + non-compensation.
- [ ] Run focused tests; PASS.
- [ ] Self-audit source/operator semantics and candidate-specific falsifier drift.
- [ ] Commit Task 2.

### Task 3: M1-M4 structural/provenance specialist rules

**Files:**
- Modify: `scripts/v5/td_real_directional_gate_executors_v2.py`
- Modify: `tests/v5/test_td_real_directional_gate_executors_v2.py`

**Interfaces:**
- Produces exact evidence predicates for:
  - `M1_CIRCULARITY_CONTROL`
  - `M2_INDEPENDENT_PROVENANCE`
  - `M3_CAUSAL_CLAIM_FALSE`
  - `M4_SUPPORT_ABSTENTION`

- [ ] Derive the narrow predicates from frozen specialist/provenance contracts only; no new biological thresholds.
- [ ] Add RED tests for PASS/FAIL/NE and explicit causal-claim refusal.
- [ ] Run focused tests and confirm RED.
- [ ] Implement minimal predicates.
- [ ] Run focused tests; PASS.
- [ ] Self-audit that C5 cannot become a foundation target and no structural predicate asserts biological efficacy.
- [ ] Commit Task 3.

### Task 4: Authenticated output + readiness projection

**Files:**
- Create: `scripts/v5/audit_td_real_gate_executor_readiness_v4.py`
- Create: `tests/v5/test_td_real_gate_executor_readiness_v4.py`
- Create: `results/target_discovery/real_tournament/TD_REAL_GATE_DESIGN_READINESS_V3.json`

**Interfaces:**
- Consumes: V2 design-readiness JSON, existing 198-row matrix, executor source hash.
- Produces: V4 readiness projection over all 198 candidate×gate rows and authenticated executor artifacts containing gate ID, status, executor/estimand/decision-rule/evidence hashes, raw sufficient statistics, claim boundary, and all-false authority.

- [ ] Add RED tests requiring exactly 15 unique newly callable rules, exactly 13 blocked rules, zero blocked-rule promotion, and all-false authority.
- [ ] Run tests and confirm RED.
- [ ] Implement projection/auditor; preserve existing five qualified structural rules from PR #334 separately.
- [ ] Run focused + existing readiness suites; PASS.
- [ ] Self-audit counts and blocked-gate identities against PR #338 V2 JSON.
- [ ] Commit Task 4.

### Task 5: Outcome-blind qualification workflow

**Files:**
- Create: `.github/workflows/td-real-directional-gates-v2-qualification.yml`
- Create: `docs/agent/TD_REAL_DIRECTIONAL_GATES_V2_QUALIFICATION_PACKET_20261013.md`
- Create after successful CI: `results/target_discovery/real_tournament/TD_REAL_DIRECTIONAL_GATES_V2_QUALIFICATION_RECEIPT.json`

**Interfaces:**
- Workflow runs only synthetic/unit/contract fixtures; it must not download biological outcome/controller inputs.
- Receipt binds exact executor/test/auditor hashes, environment versions, test counts, readiness counts, `candidate_outcomes_opened=false`, and all authority false.

- [ ] Add workflow that runs new tests plus relevant existing PR #333-#335 readiness/quantitative/structural suites.
- [ ] Emit explicit guards: `BIOLOGICAL_OUTCOME_INPUTS_DOWNLOADED=false`, `REAL_TOURNAMENT_EXECUTED=false`, `AUTHORITY_ALL_FALSE=true`.
- [ ] Run exact-head CI and inspect logs for test count/skips/failures.
- [ ] If GREEN, freeze receipt from exact tested head; if RED, diagnose/fix prospectively and rerun without changing scientific rules.
- [ ] Whole-branch self-audit: diff must contain no real outcome files, no blocked-gate decision rules, no target/representation/training authority.
- [ ] Open draft PR stacked on PR #338 and STOP for controller/external review.
