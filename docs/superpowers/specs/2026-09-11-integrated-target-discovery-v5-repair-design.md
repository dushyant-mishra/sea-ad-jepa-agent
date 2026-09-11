# Integrated Target Discovery → V5 Repair Design

Status: REVIEW/IMPLEMENTATION DESIGN
Date: 2026-09-11

## Goal
Close the remaining external-review blockers across the production chain

`raw SEA-AD substrate → discovery population/masks → target discovery → target statistical qualification/freeze → teacher target → V5 student/teacher training → downstream evaluation`

without modifying frozen V20, opening protected `reader_validation`/`reader_oracle`, running S0–S4 before executable qualification, or granting training authority prematurely.

## Architecture

1. **Immutable V20 stays read-only.** All repairs are successor V21/V5 code and governance.
2. **Decision-capable target qualification consumes provenance-bound artifacts, never naked arrays.** A validated 28-fold cross-fit artifact carries donor identity, exact train/holdout membership, fold-specific inner-ridge trace, estimator identity, prediction, nuisance inputs, source digests, and code/contract identity.
3. **Structural invalidity and scientific non-estimability are distinct states.** Malformed/nonfinite/coding-invalid inputs raise fail-closed validation errors; legitimate rank/estimability failures return typed non-estimable results.
4. **Power is calibrated to the exact frozen confirmatory test.** No claim of ≥80% power may be made from a transportable `t/sqrt(n)` shortcut unless prospectively justified and empirically calibrated. The default successor gate therefore uses deterministic/simulation calibration of the same confirmatory statistic/test family and labels sensitivity quantities honestly.
5. **The jackknife minimum is an empirical influence-sensitivity statistic, not a confidence lower bound.** Any lower-confidence claim requires an explicit coverage construction.
6. **S0–S4 measurement is a separate, hash-bound layer.** Selection logic cannot accept unverifiable scalar dictionaries as production evidence; measurement artifacts bind raw discovery lineage, measured-core identity, thinning draws/retention, held-out-biology preservation, ridge-stability metrics, estimator code identity and complete tables.
7. **The final 46-development-donor target gets its own successor authority and serializer.** It cannot reuse a V20 28-donor package while implying 46-donor provenance.
8. **V5 accepts exactly one qualified teacher-target receipt.** The trainer/optimizer path must refuse to update unless the receipt binds the qualified target package root, V21 contract/executor identity, 46-donor development role ledger, V5 design authority and all required pre-execution gates.
9. **Adversarial qualification attacks the real path.** Tests cover held-out-outcome perturbation, donor/batch/library/depth/source/specimen nuisance recovery, identity/shared-view/same-cell/lookup/duplicate/technical-only shortcuts, corrupted biology, receipt tampering and optimizer bypass.
10. **Governance is updated only after executable evidence exists.** Status remains NO-GO until exact-head tests and mutation/adversarial evidence are reproducible from tracked code.

## Components

### A. V21 validated cross-fit artifact
A typed artifact constructor validates exactly 28 unique discovery donors, each donor held out exactly once, each training set equal to the other 27 donors, no holdout identity in any fold fit inputs, fold-local ridge trace and estimator identity present, finite OOF prediction per donor, and source/contract digests. Production `power_gate` consumes only this artifact.

### B. V21 input validation and inference semantics
Public functions validate shape, finiteness and categorical coding before nuisance design/inference. Only mathematically legitimate rank/design degeneracy is represented as `NOT_ESTIMABLE`; malformed inputs raise `InvalidV21Input`.

### C. V21 ridge refinement
Replace the non-moving Stage-C contract with deterministic recentering: at each declared step evaluate `{c-step,c,c+step}`, select with the prospectively frozen V20 tie rule, recenter to that winner, and continue. Boundary/non-bracketing states fail closed. The design document is updated before any biological execution.

### D. V21 power/sensitivity gate
Freeze the confirmatory test first. Power calibration reruns the same donor-level statistic/test under prospectively declared effect-generating assumptions or resampling mechanics. Until validated, the jackknife-minimum-based calculation is exposed only as `influence_sensitivity_projection`, never a statistical lower confidence bound or production power authority.

### E. S0–S4 measurement artifact
Implement the actual discovery-only measurement path: discovery-derived common measured core; retention/thinning ladder; standardized displacement; held-out-biology preservation; beta-direction, cell-score-geometry and donor-summary ridge stability; QC calibration inputs; complete candidate table; digests and provenance. Selection consumes only this artifact.

### F. V21 46-donor freeze
After S0–S4 selection and power/qualification pass (not during this repair if protected/data-dependent prerequisites remain closed), refit the already-frozen estimator on exactly the 46 development donors and serialize a new target package whose package root binds the 46-donor role ledger, raw expression/address/cell identities, estimator contract, ridge choice, learned parameters and qualification receipt.

### G. V5 teacher receipt and optimizer guard
Add one pre-execution receipt schema with the qualified V21 target package root and required V5 authorities. The production optimizer step requires a validated receipt object/token and fails before gradient/update state is touched when absent, stale, mismatched or tampered.

### H. Reproducible external-review evidence
Commit the mutation/adversarial harness, exact commands, expected fail-closed mutations and exact-head evidence. Update START_HERE/current authority/supersession only to describe demonstrated state.

## Error handling
- Structural/malformed input: raise and STOP.
- Missing/mismatched digest, donor membership or fold provenance: raise and STOP.
- Legitimate statistical non-estimability: typed `NOT_ESTIMABLE`, never silently converted from malformed input.
- Power-calibration assumptions not validated: `STOP_POWER_CALIBRATION_NOT_QUALIFIED`.
- Missing 46-donor target authority: `STOP_V21_46DONOR_TARGET_NOT_FROZEN`.
- Missing/mismatched V5 receipt: `STOP_V5_QUALIFIED_TARGET_RECEIPT_INVALID` before optimizer update.

## Testing strategy
TDD for every production change. Each repaired defect first gets a minimal failing test, then minimal implementation, then the focused suite and the broader affected suite. External review adds adversarial tests that are not mirrors of implementation details. No protected biological result is read to make a test pass.

## Acceptance criteria
- Frozen V20 bytes unchanged.
- All malformed-input tests fail closed; legitimate rank degeneracy remains distinguishable.
- Naked arrays cannot call any decision-capable production power gate.
- Cross-fit artifact proves 28/28 one-time holdout and 27-donor train membership with fold-local ridge provenance.
- Ridge refinement can move away from the coarse anchor and is deterministic under the frozen tie rule.
- No ≥80% production-power claim is emitted by an unqualified parametric shortcut.
- S0–S4 production selection cannot run from hand-entered scalar summaries.
- A distinct 46-donor successor target package/receipt schema exists and cannot be confused with V20 28-donor provenance.
- V5 optimizer cannot execute one update without a matching qualified-target receipt.
- Mutation/adversarial harness is tracked and reproducible.
- Governance reports exact demonstrated status; training remains OFF until all data-dependent and production-geometry gates close.
