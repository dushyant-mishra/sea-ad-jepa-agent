# V80 Sparse-Positive Successor Qualification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an estimator-independent, sealed synthetic benchmark that prospectively qualifies sparse-positive estimation and lawful abstention without modifying or rescuing V79.

**Architecture:** A deterministic producer creates eight independently seeded sparse-positive challenge families from anonymous latent parameters, then writes disjoint fit-side and controller-side transports. A separate parser/adjudicator later consumes successor-estimator outputs and controller truth, while a frozen non-regression manifest binds the immutable V79 Q00-Q11 package. This PR qualifies only the benchmark package and adjudication mechanics.

**Tech Stack:** Python 3.11, NumPy, JSON/NPZ, pytest, GitHub Actions, existing repository custody conventions.

**Spec:** `docs/superpowers/specs/2026-10-13-v80-sparse-positive-successor-qualification-design.md`

## Global Constraints

- Base is PR #328 exact head `25bbdbe18aa5ed3c8a39a7e4295bc36de1e328ec`.
- V79 scorer/orchestrator head `ac1e73d79489438634aaeeca035d229875f3186a` and final receipt `ef10852e...e8abfd` are immutable historical evidence.
- Do not use the three V79 failed-fit IDs in seed derivation, parameter construction, challenge selection, or thresholds.
- New benchmark challenge identity and estimability truth are controller-only.
- `COMPLETE`, `NOT_ESTIMABLE`, and `NUMERICAL_FAILURE` are distinct statuses.
- `NUMERICAL_FAILURE` can never satisfy a deliberately non-estimable challenge.
- No V79 world regeneration, V79 threshold retuning, real-data inference, target/representation selection, TD60, Stage4, or training.
- Synthetic recovery thresholds are benchmark-only and carry no human biological authority.

## Review Focus

- **Accidental Q08 overfitting:** prove no failed-fit IDs or V79 realized seeds enter generator source/config.
- **False abstention:** estimable worlds must be full-rank and have prospectively adequate positive support.
- **False certainty:** SP05/SP06 must be non-estimable by construction, not merely difficult.
- **Controller leakage:** fit transport must remain challenge/estimability/truth blind.
- **Poison/support bug:** unsupported stored values must never change fit-visible sufficient statistics.

---

### Task 1: Contract, challenge definitions, and RED tests

**Files:**
- Create: `results/v80/sparse_positive/V80_SPARSE_POSITIVE_QUALIFICATION_CONTRACT_V1.json`
- Create: `tests/v80/test_v80_sparse_positive_benchmark.py`
- Create: `.github/workflows/v80-sparse-positive-benchmark.yml`

**Interfaces:**
- Consumes: frozen identities from the design spec.
- Produces: test expectations for `scripts/v80/v80_sparse_positive_benchmark.py` and `scripts/v80/v80_sparse_positive_adjudicator.py`.

- [ ] **Step 1: Write failing tests** for exact eight family IDs, no V79 failed-fit IDs in source/config, deterministic generation, controller-free fit serialization, SP05 zero-positive non-estimability, SP06 rank-deficient non-estimability, estimable-world full rank/support, donor-disjoint splits, poison invariance, and status adjudication.
- [ ] **Step 2: Run tests and verify RED** because `scripts.v80` modules do not exist.
- [ ] **Step 3: Commit RED tests/contract/workflow**.

### Task 2: Deterministic sparse-positive producer

**Files:**
- Create: `scripts/v80/__init__.py`
- Create: `scripts/v80/v80_sparse_positive_benchmark.py`
- Modify: `tests/v80/test_v80_sparse_positive_benchmark.py`

**Interfaces:**
- Produces:
  - `SparsePositiveConfig`
  - `SparsePositiveWorld`
  - `build_sparse_positive_worlds(seed_root: int) -> tuple[SparsePositiveWorld, ...]`
  - `serialize_fit_transport(worlds) -> dict`
  - `serialize_controller_transport(worlds) -> dict`
  - `validate_fit_transport(payload) -> None`
  - `benchmark_identity(worlds) -> str`

- [ ] **Step 1: Implement only after Task 1 RED evidence.**
- [ ] **Step 2: Make family/estimability/full-rank/support tests GREEN.**
- [ ] **Step 3: Run existing PR #328 unified-synthetic tests to ensure no regression.**
- [ ] **Step 4: Commit producer implementation.**

### Task 3: Successor-output schema and hard adjudicator

**Files:**
- Create: `scripts/v80/v80_sparse_positive_adjudicator.py`
- Modify: `tests/v80/test_v80_sparse_positive_benchmark.py`

**Interfaces:**
- Produces:
  - `FitOutcome`
  - `parse_fit_outcome(record: Mapping[str, object]) -> FitOutcome`
  - `adjudicate_sparse_positive(controller_payload, estimator_results) -> dict`

- [ ] **Step 1: Add RED tests** proving status exclusivity, estimable→COMPLETE, non-estimable→NOT_ESTIMABLE, numerical failure always hard-fails, false-abstention hard-fails, false-certainty hard-fails, and no aggregate rescue.
- [ ] **Step 2: Implement minimal parser/adjudicator.**
- [ ] **Step 3: Verify GREEN and commit.**

### Task 4: Sealed package finalizer and non-regression binding

**Files:**
- Create: `scripts/v80/finalize_v80_sparse_positive_package.py`
- Create: `results/v80/sparse_positive/V80_V79_NONREGRESSION_BINDING_V1.json`
- Modify: `tests/v80/test_v80_sparse_positive_benchmark.py`

**Interfaces:**
- Produces:
  - `build_package_receipt(...) -> dict`
  - `write_transport_once(...)`
  - exact fit/controller/package hashes and V79 immutable bindings.

- [ ] **Step 1: Add RED tests** for exact V79 contract/world-set/final-receipt binding, fit/controller separate hashes, write-once behavior, authority-off fields, and refusal of historical-identity drift.
- [ ] **Step 2: Implement finalizer and binding.**
- [ ] **Step 3: Verify deterministic receipt and commit.**

### Task 5: CI physical separation, hostile audit, and freeze

**Files:**
- Modify: `.github/workflows/v80-sparse-positive-benchmark.yml`
- Create after green CI: `results/v80/sparse_positive/V80_SPARSE_POSITIVE_PACKAGE_RECEIPT_V1.json`
- Create: `docs/agent/V80_SPARSE_POSITIVE_BENCHMARK_EXECUTION_LEDGER_20261013.md`

**Interfaces:**
- Producer job uploads separate fit and controller artifacts.
- Fit-validation job downloads only fit artifact.
- Controller-validation job downloads only controller artifact.
- No estimator run occurs.

- [ ] **Step 1: Run RED workflow and preserve failure.**
- [ ] **Step 2: Run GREEN workflow after implementation.**
- [ ] **Step 3: Hostile self-audit** source/config for V79 failed-fit IDs, challenge leakage, rank/support mistakes, support poison dependence, authority escalation, and hidden estimator assumptions.
- [ ] **Step 4: Any found defect gets a RED regression before repair.**
- [ ] **Step 5: Freeze exact CI-produced receipt and update ledger.**
- [ ] **Step 6: Final verification:** focused V80 tests + inherited PR #328 tests + exact source/receipt hashes.

## Final completion contract

The work is complete only when a future estimator owner can receive an opaque fit package plus the prospective contract, run one frozen successor estimator, and later have controller adjudication distinguish correct estimation, correct abstention, false abstention, false certainty, and numerical failure without reopening or modifying V79.
