# Integrated Target Discovery → V5 Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close executable external-review defects from target discovery through V5 authorization without modifying frozen V20 or opening protected data.

**Architecture:** Add successor V21 validation/provenance components around the immutable V20 learner; make production decisions consume typed hash-bound artifacts; add a distinct 46-donor target receipt schema; make V5 optimizer authorization depend on that receipt; commit adversarial evidence and governance only after verification.

**Tech Stack:** Python 3, NumPy/SciPy/statsmodels where already used, pytest, hashlib/json/dataclasses, existing JEPA repository utilities.

**Spec:** `docs/superpowers/specs/2026-09-11-integrated-target-discovery-v5-repair-design.md`

## Global Constraints
- Frozen V20 bytes MUST NOT change.
- Do not open `reader_validation` or `reader_oracle`.
- Do not execute S0–S4 on biological data until executable qualification closes.
- Do not grant production training authority.
- Structural invalidity must fail closed and remain distinct from statistical non-estimability.
- Production decision functions may not accept unprovenanced naked score arrays.

---

### Task 1: Complete external code/evidence inventory
**Files:** read-only audit of V21/V5 scripts, tests, governance, authority and trainer entry path.

- [ ] Re-fetch live heads and exact files.
- [ ] Trace raw discovery lineage → V20 target → V21 successor → V5 teacher/optimizer.
- [ ] Record every open defect with executable evidence and distinguish cleared concerns from real blockers.
- [ ] Verify no hidden wrapper already closes each reported gap.

### Task 2: V21 structural validation boundary
**Files:**
- Modify: `scripts/v4/t0_v21_selection_and_power_v1.py`
- Modify/Test: `scripts/v4/test_t0_v21_selection_and_power_v1.py`

**Produces:** `InvalidV21Input`; validation before nuisance design/inference.

- [ ] Add failing tests: nonfinite age, length mismatch, invalid sex coding and malformed score vectors must raise `InvalidV21Input`.
- [ ] Confirm existing code fails those tests for the intended reason.
- [ ] Implement minimal structural validator and call it before estimability handling.
- [ ] Add a valid rank-degenerate case proving it still yields `estimable=False` rather than structural invalidity.
- [ ] Run focused and full V21 tests.

### Task 3: Provenance-bound 28-fold cross-fit artifact
**Files:**
- Create: `scripts/v4/t0_v21_crossfit_artifact_v1.py`
- Create/Test: `scripts/v4/test_t0_v21_crossfit_artifact_v1.py`
- Modify: `scripts/v4/t0_v21_selection_and_power_v1.py`

**Produces:** `CrossFitFoldRecord`, `ValidatedCrossFitArtifact`, `validate_crossfit_artifact()`.

- [ ] Write failing tests for duplicate holdout, wrong 27-donor train set, holdout-in-training, missing ridge trace, missing estimator/source digest, nonfinite OOF score, donor-order tampering and naked score input to production power gate.
- [ ] Verify RED.
- [ ] Implement canonical JSON hashing and exact 28-fold validation.
- [ ] Change decision-capable power entry point to require validated artifact.
- [ ] Keep any array-based helper explicitly non-authoritative/private for unit math only.
- [ ] Test held-out outcome perturbation using actual frozen target learner adapter: donor i outcome change must not alter donor i OOF prediction or its fold hyperparameter trace.
- [ ] Run focused + V21 suite.

### Task 4: Repair Stage-C ridge refinement contract
**Files:**
- Modify: `docs/agent/T0_V21_PROSPECTIVE_DESIGN_DRAFT.md`
- Modify: `scripts/v4/t0_v21_selection_and_power_v1.py`
- Modify/Test: `scripts/v4/test_t0_v21_selection_and_power_v1.py`

- [ ] Add failing test where true local minimum lies at `c+step` and refinement must recenter/move.
- [ ] Verify current implementation cannot move.
- [ ] Update design prospectively: evaluate `{c-step,c,c+step}`, choose by frozen loss/tolerance/strongest-regularization tie rule, recenter to winner, proceed; fail on unbracketed terminal state.
- [ ] Implement minimal recentering algorithm.
- [ ] Add determinism/tie/boundary tests.
- [ ] Run V21 suite.

### Task 5: Correct power/sensitivity semantics
**Files:**
- Modify: `docs/agent/T0_V21_PROSPECTIVE_DESIGN_DRAFT.md`
- Modify: `scripts/v4/t0_v21_selection_and_power_v1.py`
- Modify/Test: `scripts/v4/test_t0_v21_selection_and_power_v1.py`

**Produces:** no production `PASS_POWER` from unqualified `t/sqrt(n)` projection; explicit influence-sensitivity result and `STOP_POWER_CALIBRATION_NOT_QUALIFIED` until exact confirmatory calibration is supplied.

- [ ] Add failing test proving legacy noncentral-t projection cannot emit production-pass authority.
- [ ] Rename jackknife-minimum semantics to empirical influence minimum/sensitivity projection.
- [ ] Add explicit calibration receipt interface binding exact confirmatory test family, alpha, nuisance design, n=12 and calibration method/digest.
- [ ] Production gate stops without validated calibration receipt.
- [ ] Add tamper/mismatch tests.
- [ ] Run V21 suite.

### Task 6: S0–S4 measurement/provenance layer
**Files:**
- Create: `scripts/v4/t0_v21_measurement_artifact_v1.py`
- Create/Test: `scripts/v4/test_t0_v21_measurement_artifact_v1.py`
- Modify: `scripts/v4/t0_v21_selection_and_power_v1.py`

**Produces:** `ValidatedEstimatorMeasurementArtifact`; production selection accepts this artifact only.

- [ ] Add failing tests for hand-entered summary dicts, missing common-core digest, missing thinning draw/retention provenance, incomplete candidate table, absent held-out-biology envelope, absent beta/cell-score/donor-summary ridge metrics and digest tampering.
- [ ] Implement artifact schema/validation and deterministic metric aggregation only; do not execute biology.
- [ ] Wire `select_estimator` production entry to validated artifact.
- [ ] Preserve pure math helper separately for unit tests.
- [ ] Run focused + V21 suite.

### Task 7: 46-donor successor target authority
**Files:**
- Create: `scripts/v4/t0_v21_target_freeze_v1.py`
- Create/Test: `scripts/v4/test_t0_v21_target_freeze_v1.py`

**Produces:** `V21TargetFreezeReceipt` schema and serializer/validator; no biological refit is executed in this repair.

- [ ] Add failing tests preventing 28-donor V20 provenance from masquerading as 46-donor target.
- [ ] Require exactly 46 unique development donors and role-ledger digest.
- [ ] Bind estimator identity, ridge exponent/trace identity, raw-expression/address/cell/donor digests, qualification receipts and learned-parameter digest into package root.
- [ ] Add tamper tests for every bound component.
- [ ] Verify schema can represent future refit without opening fresh 12/10 donors.

### Task 8: V5 qualified-target receipt and optimizer guard
**Files:** identify exact V5 pre-execution/trainer entry files during Task 1; modify only successor V5 branch copies.

**Produces:** `QualifiedTeacherTargetReceipt` validation and a pre-update fail-closed guard.

- [ ] Add failing integration test: actual optimizer/trainer update path called without receipt must fail before parameters/optimizer state/RNG-update counters change.
- [ ] Add receipt mismatch/tamper/stale-code tests.
- [ ] Implement minimal guard at the deepest common update boundary, not only CLI/report layer.
- [ ] Bind V21 46-donor target package root plus V5 authority roots.
- [ ] Verify valid synthetic/mechanics receipt allows the mechanics test path but confers no production authority.

### Task 9: V5 anti-shortcut and gate-execution hardening
**Files:** exact files from live V5 head after inventory.

- [ ] Reproduce asymmetric-zero cosine edge defect with failing test; fix and test zero/nonzero/subnormal/NaN cases.
- [ ] Replace report-level rejection-power assertion with execution of actual frozen gate over deterministic controls and hash-bound raw outputs.
- [ ] Add donor-held-out nuisance-recovery attacks for donor/batch/library/depth/source/specimen structure.
- [ ] Add deliberate identity/same-cell/shared-view/lookup/duplicate/technical-only/corrupted-biology attacks against actual qualification path.
- [ ] Require each attack to fail closed with explicit reason.

### Task 10: Reproducible mutation/adversarial audit and governance
**Files:**
- Create: `scripts/v4/mutation_audit_v21.py`
- Create/Modify: review artifact under `docs/agent/reviews/`
- Modify: governance pointers only after verification.

- [ ] Commit mutation harness covering all repaired defect classes.
- [ ] Run exact-head tests where executable in reviewer environment; distinguish reviewer-run from producer-run evidence.
- [ ] Verify frozen V20 tree hashes unchanged.
- [ ] Record unresolved data/runtime blockers separately (FULL104 expression binding, production dimensions/GPU/postqualification).
- [ ] Update startup/authority/supersession documents to exact demonstrated state, with training still OFF unless every production gate closes.

## Self-review
- Spec coverage: Tasks 2–10 map to all ten design principles and acceptance criteria.
- No task authorizes protected-data opening or biological selection.
- The 46-donor task creates authority/schema only; it intentionally does not perform the refit before qualification.
- V5 guard is required at the optimizer boundary so CLI/report bypass cannot update parameters.
- Array/dict math helpers may remain for unit testing, but production decision APIs require validated artifacts.
