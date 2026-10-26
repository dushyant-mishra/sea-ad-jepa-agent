# Macha independent review — production-synthetic Task 3 (calibration) at `1f2b7f1f` (PR #432)

Date: 2026-10-26.

Role: independent reviewer. ChatGPT authored this code; Macha did not.

Scope: PR #356 Task 3, under PR #344 V3.1/V3.1.1. Every input is a dummy fixture. No protected or real bytes were read.

## Verdict

`REJECT_TASK3_IMPLEMENTATION` for `1f2b7f1fab7a952ffd4aee11d5ef7af827cf6b47`.

**What holds.**
- The precision mathematics (E) is correct.
- Scope containment (F) is clean: no I/O, no hidden biology, no protected outcomes, no controller secrets, no production world, no STOP crossed.
- Within the author's own tests, `NumericProvenance` rejects NaN, infinity, `bool` and `np.float64`.

**What fails.** Four authority surfaces accept caller assertions as authority:
- **A.** The calibration firewall: authentication and split isolation.
- **B.** The numeric-provenance labels.
- **C.** The address-universe check.
- **D.** The realism stopping law.

The module's docstrings disclose that the inputs are not attestations. The code nonetheless returns results that look authenticated, and does not fail closed.

## Evidence

| item | value |
|---|---|
| hostile tests | `tests/production_synthetic/test_calibration_v1_macha_hostile.py` (branch `review/macha-ps-task3-hostile-red-20261026`, draft PR #434) |
| RED, CI | run `40342119953`, job `121639313193`: **11 failed** (all hostile tests), 19 passed (the author's) |
| RED, local | 11 failed (Windows, Python 3.9) |
| author suite, local | `test_calibration_v1.py` 19 passed. The full `tests/production_synthetic` suite shows 4 failures in the Task 1–2 tests, caused only by local Python 3.9: `co_qualname` and the int-string limit both need ≥3.11. CI runs 3.11. |

## Blocking defects

**PS3-B1 (A). The firewall authenticates nothing beyond internal consistency.**
- **A1.** `split_role` and `provenance` are not type-checked. A `str` subclass that compares equal to anything lets a `READER_ORACLE` artifact through.
- **A2.** The protected partitions (`excluded_donors`) come from the caller and may be empty, so any donor can be listed as fit-eligible.
- **A3.** A digest the caller pins for itself (`sha256(raw)`) comes back with provenance `AUTHENTICATED_EMPIRICAL_CALIBRATION`.

*Minimal repair:*
- Check the exact type of every artifact field.
- Require each protected role (validation, oracle, reserved, development) to be present and non-empty, in a typed partition object.
- Never return `AUTHENTICATED_EMPIRICAL_CALIBRATION` for a caller-pinned digest. Return an explicit non-authoritative status until a code-pinned registry of authenticated artifacts exists. Choosing that registry, and which split authority binds the partitions, belongs to the deciding lane.

**PS3-B2 (B). A provenance label alone confers the category.**
- `NumericProvenance(..., "AUTHENTICATED_EMPIRICAL_CALIBRATION", "0"*64)` constructs successfully.

*Minimal repair:*
- `AUTHENTICATED_EMPIRICAL_CALIBRATION` must reference an artifact that the pinned authority authenticated. Until one exists, it fails closed.
- The other two categories must name what they are bound to: a pinned executor code identity, or a frozen-convention digest.
- `PrecisionTarget` ε and α are decision-bearing numbers and should carry provenance.

**PS3-B3 (C). The address-universe check returns eligibility from caller values.**
- Identical caller dictionaries plus two self-matched caller digests return bare `True`.

*Minimal repair:*
- Return a typed, non-authoritative fixture status.
- Real eligibility requires pinned 96-pilot and 41,238-registry digests held as code constants, plus authenticated per-address inputs from which the module computes the statistic itself. Otherwise the result is `CALIBRATION_INELIGIBLE`, as §22.13 requires.

**PS3-B4 (D). The realism stopping law holds only for an honest caller.**
- **D1.** The search can be re-initialised after `REALISM_NOT_QUALIFIED`.
- **D2.** A failed version can be replayed in a fresh search.
- **D3.** A state built by the caller reopens an exhausted search. A `FIRST_JOINT_PASS_FROZEN` state naming any version can be built the same way.
- **D4.** A relaxed contract can restart the same generator family.
- **D5.** `contract_sha256` is an arbitrary claim, not the contract's content digest.

*Minimal repair:*
- `RealismState` is issued only by the module: a private token plus a process-local registry, with a lease per (version family, contract digest).
- One contract and one search per generator family.
- Terminal states are irreversible.
- `contract_sha256` must equal the content digest.
- Bind the version family to the Task 2 frozen generator version.
- Persistent cross-process custody remains a STOP_B prerequisite, and its absence must fail closed for any non-fixture use.

## Non-blocking

- **E.** The two-sided Hoeffding bound `n ≥ ln(2/α)/(2ε²)` is correct for independent [0,1] units (ε=0.1, α=0.01 gives 265). The docstring correctly says it is not power.
  - There is no multiplicity adjustment across statistics; that has to be a recorded prospective convention.
  - Within one synthetic world, donors share the world's parameters. The bound is conditional on the world unless worlds are the unit of analysis.
- A huge integer (`10**400`) raises `OverflowError` rather than `CalibrationError`. That still fails closed, just with the wrong exception type.
- The returned frozen dataclasses can be mutated with `object.__setattr__`. That is acceptable at fixture level, but the lesson from Unified Task 4 applies before any consumer relies on them.
- The Task 3 workflow runs only the Task 3 tests. It should also run the Task 1–2 regressions.

## Prerequisite check: Tasks 1–2

No independent per-task acceptance decision exists for production-synthetic Tasks 1–2 (`ff597faf` / `f53c13e6`):
- The controller audit `MACHA_OLD_SYNTH_TASK1_2_CONTROLLER_AUDIT_V1_20261014` classifies them `REUSE_CANDIDATE__NOT_YET_ACCEPTED`, with "fresh reviewer verdict" listed as open evidence.
- The no-repeat audit dated 2026-10-26 states that acceptance is not established by branch presence or by the #382 rerun.
- PR #382 has no review.

Macha authored Tasks 1–2, so Macha cannot supply that verdict; another reviewer must.

## Consequence

PR #356 lets Task 4 (candidate-neutral hidden biology) begin only after Tasks 1–3 each clear their per-task review. Both conditions are unmet: Task 3 is rejected here, and Tasks 1–2 have no independent acceptance. **Production-synthetic Task 4 is not started.**

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
