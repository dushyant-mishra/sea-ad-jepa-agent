# Target Tournament Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build synthetic-fixture-only, non-authorizing infrastructure that enforces the frozen target-tournament gates, constructs the matched wrong-cell null without breaking technical strata, and rejects direct or indirect query-value leakage.

**Architecture:** Three small Python modules under `scripts/v5/` implement independent pure functions with no H5AD/NPZ/matrix readers and no training code. A machine-readable scaffold contract freezes current candidate IDs, gate names, claim boundaries, and fixture-only authority. Tests under `tests/v5/` use synthetic dictionaries/rows only and must prove fail-closed behavior before production code is added.

**Tech Stack:** Python 3 standard library, pytest.

**Spec:** `docs/superpowers/specs/2026-10-11-td-multitarget-tournament-prefreeze.md`

## Global Constraints

- No corrected expression/count values may be opened by this scaffold.
- No G6/G7 execution or value-read authorization may be created.
- No target, representation, Stage4, TD60, or training authority may be emitted.
- Current contract is `fixture_only=true`; attempts to label real execution as qualified must fail closed.
- C5 regulatory/chromatin is optional-specialist only and cannot be promoted as the foundation target by this scaffold.
- Mandatory gate failure cannot be overridden by an aggregate score.
- Query address may condition a task; query scalar and q-derived descendants may not enter student evidence or target normalization.
- Matched wrong-cell reassignment must preserve donor, operator, support, depth-bin, and detection-bin and must change cell identity.

## Review Focus

1. A receipt with every high-level score positive but one mandatory gate false must still be rejected.
2. A receipt or contract claiming target/training/value authority must fail before adjudication.
3. Null construction must never cross donor/operator/support/depth/detection strata and must never retain the same cell.
4. Singleton strata must report non-estimability rather than silently cross strata.
5. Query leakage hidden two or more dependency edges upstream of a student feature or target normalization must still be detected.

---

### Task 1: Tournament contract and non-authorizing adjudicator

**Files:**
- Create: `custody/takeover_20261011/TD_TARGET_TOURNAMENT_SCAFFOLD_CONTRACT_V1.json`
- Create: `scripts/v5/td_target_tournament_scaffold.py`
- Test: `tests/v5/test_td_target_tournament_scaffold.py`

**Interfaces:**
- Consumes: JSON-like Python mappings for scaffold contract and candidate receipts.
- Produces: `validate_contract(contract) -> None`, `validate_candidate_receipt(receipt, contract) -> None`, `adjudicate(contract, receipts) -> dict`.

- [ ] **Step 1: Write failing tests** for exact schema/candidate IDs, forbidden authority booleans, mandatory-gate failure despite favorable score, C5 specialist-only behavior, and no-winner terminal.
- [ ] **Step 2: Run** `pytest -q tests/v5/test_td_target_tournament_scaffold.py` and require RED caused by missing module/functions.
- [ ] **Step 3: Implement minimal validator/adjudicator** with no file/matrix readers and no statistical computation.
- [ ] **Step 4: Re-run focused tests** and require GREEN.
- [ ] **Step 5: Commit** test, module, and contract together with preserved RED/GREEN log notes.

### Task 2: Deterministic matched wrong-cell null constructor

**Files:**
- Create: `scripts/v5/td_target_tournament_nulls.py`
- Test: `tests/v5/test_td_target_tournament_nulls.py`

**Interfaces:**
- Consumes: sequence of row mappings with `cell_id`, `donor_id`, `operator_id`, `support_key`, `depth_bin`, `detection_bin`.
- Produces: `build_matched_wrong_cell_map(rows, seed_material) -> dict[str, str]` and raises `NotEstimableStratum` for strata that cannot be deranged.

- [ ] **Step 1: Write failing tests** proving identity changes, all frozen strata are preserved, determinism under same seed/input, changed seed can change valid mappings, and singleton strata fail closed.
- [ ] **Step 2: Run** `pytest -q tests/v5/test_td_target_tournament_nulls.py` and require RED from missing module/functions.
- [ ] **Step 3: Implement deterministic per-stratum derangement** using SHA-256-derived ordering; never fall back across strata.
- [ ] **Step 4: Re-run focused tests** and require GREEN.
- [ ] **Step 5: Commit** test and module.

### Task 3: Query-information lineage/leakage guard

**Files:**
- Create: `scripts/v5/td_query_information_guard.py`
- Test: `tests/v5/test_td_query_information_guard.py`

**Interfaces:**
- Consumes: dependency graph mapping node -> direct parent nodes plus declared node roles.
- Produces: `assert_query_safe(graph, roles) -> None`; raises `QueryLeakageError` with offending path.

- [ ] **Step 1: Write failing tests** allowing `q_address`, rejecting direct `q_scalar`, rejecting q-bearing target normalization, rejecting indirect student leakage through normalization/QC descendants, and detecting dependency cycles.
- [ ] **Step 2: Run** `pytest -q tests/v5/test_td_query_information_guard.py` and require RED from missing module/functions.
- [ ] **Step 3: Implement ancestry traversal** with explicit allowed/forbidden source roles and cycle rejection.
- [ ] **Step 4: Re-run focused tests** and require GREEN.
- [ ] **Step 5: Commit** test and module.

### Task 4: Cross-module qualification and non-authority receipt

**Files:**
- Create: `docs/agent/TD_TARGET_TOURNAMENT_SCAFFOLD_QUALIFICATION_20261011.md`
- Create: `custody/takeover_20261011/TD_TARGET_TOURNAMENT_SCAFFOLD_STATE_20261011.json`

**Interfaces:**
- Consumes: Tasks 1-3 modules/tests.
- Produces: immutable qualification note stating synthetic-fixture qualification only.

- [ ] **Step 1: Run all three focused test files together** and preserve exact counts.
- [ ] **Step 2: Run static import/AST check** confirming scaffold modules import no `h5py`, `anndata`, `torch`, `scanpy`, or project value-read modules and contain no matrix-opening calls.
- [ ] **Step 3: Compare branch to base** and verify only plan/scaffold/tests/contracts/qualification artifacts changed.
- [ ] **Step 4: Record exact file SHA-256 values and explicit false authority flags** in state/qualification files.
- [ ] **Step 5: Open a draft evidence-only PR** and stop with terminal `SYNTHETIC_SCAFFOLD_QUALIFIED__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY`.
