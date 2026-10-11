# Foundation Representation Residual Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. Steps use TDD and fail closed.

**Goal:** Close every representation gate that can be lawfully resolved from authenticated TRAIN/project evidence while preserving explicit blockers for missing production/FULL104 evidence.

**Architecture:** Add one pure adjudication module for matrix label-identifiability, learned held-out-donor evidence, conditional technology-imprint diagnostics, and resource-benchmark classification. Add an audit CLI that consumes authenticated compact CSV/JSON inputs and emits bounded non-authorizing receipts. Existing V4 qualification remains unchanged; this is a successor diagnostic layer.

**Tech Stack:** Python 3.11, stdlib csv/json/hashlib, NumPy, pytest.

**Spec:** `docs/superpowers/specs/2026-10-11-foundation-representation-qualification-v4-design.md`

## Global Constraints

- TRAIN/project evidence only; no TEST/Morabito/pathology.
- No target-discovery corrected value reads.
- No representation winner, Stage4, training or checkpoint authority.
- Do not call a fit-population technology diagnostic held-out transfer.
- Do not call a CPU benchmark the final production-GPU benchmark.
- Preserve current `SUBSPACE_ONLY`, separate evidence/depth uncertainty, and sampling authority.

## Review Focus

- Source/operator predictability must not be relabeled purely technical when biology is aliased.
- Missing broad labels must be reported as non-identifiable, not imputed.
- Matrix label coverage must be computed leave-one-matrix-out.
- Held-out donor evidence must remain descriptive unless a prospective pass threshold existed.
- Resource receipts must distinguish bounded CPU evidence from final production hardware evidence.

---

### Task 1: Residual-gate adjudication primitives

**Files:**
- Create: `src/sea_ad_jepa/v4/foundation_residual_gates.py`
- Test: `tests/v4/test_foundation_representation_residual_gates.py`

**Interfaces:**
- Produces `matrix_label_identifiability(rows)`, `adjudicate_heldout_donor_evidence(rows)`, `adjudicate_conditional_technology_imprint(record)`, `adjudicate_resource_benchmark(record)`.

- [ ] Write tests for leave-one-matrix label coverage, missing broad labels, mixed donor evidence, fit-pop technology imprint, and CPU-vs-production resource status.
- [ ] Verify RED because module does not exist.
- [ ] Implement minimal pure functions.
- [ ] Verify focused tests GREEN.

### Task 2: Authenticated audit CLI

**Files:**
- Create: `scripts/v4/audit_foundation_representation_residual_gates_v1.py`
- Extend: `tests/v4/test_foundation_representation_residual_gates.py`

**Interfaces:**
- Consumes sample-freeze CSV, shortcut-atlas CSV, conditional-imprint JSON, resource JSON.
- Produces compact JSON state plus matrix-identifiability CSV with SHA-256 bindings and all authority flags false.

- [ ] Write failing CLI test.
- [ ] Implement hash-bound, exclusive-output CLI.
- [ ] Verify focused suite GREEN.

### Task 3: Current evidence receipts

**Files:**
- Create: `results/v4/FOUNDATION_MATRIX_LABEL_IDENTIFIABILITY_V1.csv`
- Create: `results/v4/FOUNDATION_T1_CONDITIONAL_TECHNOLOGY_DIAGNOSTIC_V1.json`
- Create: `results/v4/FOUNDATION_T1_CPU_RESOURCE_BENCHMARK_V1.json`
- Create: `results/v4/FOUNDATION_REPRESENTATION_RESIDUAL_GATES_V1.json`

- [ ] Bind calibration bundle SHA `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444` and u205 checkpoint identity.
- [ ] Record 84-cell fit-pop technology diagnostic without promoting it to held-out authority.
- [ ] Record measured 1/4/12-cell CPU memory and wall-time evidence without calling it production-GPU evidence.
- [ ] Record matrix vocabulary identifiability from 50K metadata.

### Task 4: Independent audit + cross-lane handoff

**Files:**
- Audit PR #271 addendum.
- Handoff PR #272 addendum/state.
- Target-discovery audit PR #251 cross-lane addendum.
- Target-discovery handoff PR #247 cross-lane addendum.

- [ ] Self-audit code, receipts, hashes and authority flags.
- [ ] Update canonical audit/handoff branches without merging.
- [ ] Preserve representation/target winner NONE and training off.

### Task 5: FULL104 residual work audit

- [ ] Recheck current GitHub FULL104/dimension implementation before writing anything.
- [ ] Implement only missing code that does not require absent >30GB physical bytes.
- [ ] Leave physical FULL104 numeric authority blocked if bytes are unavailable.
