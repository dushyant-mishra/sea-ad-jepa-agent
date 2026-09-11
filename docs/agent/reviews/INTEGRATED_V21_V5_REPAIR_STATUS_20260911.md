# Integrated V21/V5 repair status — 2026-09-11

Status: `IMPLEMENTATION_REPAIRS_PUSHED__AWAITING_EXTERNAL_REVIEW`

This file records the work completed after review of Claude's `3b5933f6` V21 repair candidate and the V5 qualified-target guard work completed in this chat.

## Immutable review candidate

`3b5933f6be45c2ec5589ddd4f200e9ff5eb49f46` remains immutable and should not be amended. It is still useful as the candidate that repaired the original six external-review blockers, but it exposed additional production-authority issues that were repaired on successor branches.

## V21 authority successor branch

Branch: `repair/t0-v21-authority-hardening-20260911`

Base: `3b5933f6be45c2ec5589ddd4f200e9ff5eb49f46`

Current status from remote compare at completion: 7 commits ahead of base.

Key files:

- `scripts/v4/t0_v21_authority_v1.py`
- `scripts/v4/t0_v21_measurement_artifact_v1.py`
- `scripts/v4/t0_v21_target_freeze_v1.py`
- `scripts/v4/test_t0_v21_authority_v1.py`
- `scripts/v4/test_t0_v21_measurement_and_freeze_v1.py`

Implemented repairs:

1. Canonical cross-fit structural revalidation now occurs during both sealing and verification. It rejects self-consistent forged artifacts, not only post-seal tampering. It checks exactly 28 donors, unique donor IDs, y/age/sex geometry, complete binary sex coding, exactly 28 fold records, held-out indexes 0..27 exactly once, `n_train = 27`, exact complement train sets, finite predictions, and score/fold agreement.
2. Confirmation-design authority is no longer a free caller argument. Receipts must come from an approved pre-unblinding source role and must match an externally expected receipt digest. Protected reader partitions remain forbidden design sources.
3. Predictor-geometry transport is explicit and hash-bound. `iid_normal_surrogate`, `random_normal_surrogate`, and `representative_synthetic_design` transport modes are rejected as non-decision-capable.
4. Power calibration is now receipt-bound rather than delegated to the legacy surrogate-based `power_gate`. A decision-capable calibration receipt must bind the authoritative cross-fit, source authority, nested-permutation evidence, confirmation-design receipt, predictor-geometry transport receipt, calibration code SHA, contract SHA, `B=9999`, alpha, target power, Monte Carlo lower limit, and must declare that it consumes predictor geometry and does not use an iid-normal surrogate.
5. The decision-capable V21 entry point validates cross-fit authority, whole-pipeline nested-permutation evidence, externally expected confirmation design, predictor-geometry transport, and geometry-aware power calibration before returning a gate verdict. It does not call the legacy surrogate-based `power_gate`.
6. Measurement and 46-donor freeze modules remain schema/validator layers only. They do not execute S0-S4, AT8, partition access, reader validation, oracle, training, optimizer steps, or EMA.

Local verification before push:

```text
cd /mnt/data/v21_patch/scripts/v4
python -m py_compile t0_v21_authority_v1.py t0_v21_measurement_artifact_v1.py t0_v21_target_freeze_v1.py
python -m pytest -q
18 passed in 0.11s
```

Remaining V21 non-executed work:

- Build the actual geometry-aware calibration executor behind the receipt schema.
- Define/freeze the lawful confirmation-design authority source or conservative design envelope.
- Define/freeze the predictor-geometry transport rule or conservative geometry class.
- Run expanded mutation audit on the successor branch.
- External review.

Forbidden until those close: real S0-S4 selection, real power gate, AT8/fresh validation/oracle/partition opening, V21 freeze, training, optimizer steps, EMA.

## V5 qualified-target guard branch

Branch: `repair/v5-qualified-target-guard-20260911`

Base: `planning/v5-full-population-cheat-proofing-20260909`

Current status from remote compare at completion: 6 commits ahead of base.

Key files:

- `src/sea_ad_jepa/v5/qualified_teacher_target_receipt_v1.py`
- `src/sea_ad_jepa/v5/qualified_optimizer_guard_v1.py`
- `src/sea_ad_jepa/v5/qualified_teacher_student_runtime_v1.py`
- `tests/test_v5_qualified_target_optimizer_guard_v1.py`

Implemented repairs:

1. V5 target receipt requires a V21 46-development-donor target freeze receipt and refuses a 28-donor discovery artifact as a target substitute.
2. V5 receipt binds expected V5 authority roots: trainer pre-execution authority, pre-execution bundle, FULL104 expression root, representation firewall, and V5 runtime source.
3. Optimizer guard is attached directly to the optimizer via step pre/post hooks. Unarmed `optimizer.step()` fails before parameter or optimizer-state mutation.
4. One authorization permits exactly one step and then fails closed again.
5. AMP `scaler.step(optimizer)` is covered because it calls the guarded optimizer's `step()`.
6. New `qualified_teacher_student_runtime_v1.qualified_production_update()` wraps the canonical v4 runtime update, installs/arms the guard for the requested schedule cursor, requires the guarded step to complete, then closes the hooks and returns a qualified authority receipt. It leaves `production_training_authorized = False`.

Local verification before push:

```text
cd /mnt/data/v5_patch
PYTHONPATH=src python -m pytest tests -q
8 passed in 2.15s
```

Remaining V5 non-executed work:

- Run against the full repository test suite in a clean checkout.
- External red-team review of whether any alternative production path bypasses `qualified_production_update`.
- Bind the eventual V21 46-donor target package root after it exists.
- Do not train or execute production optimizer updates.

## QID lineage

See `docs/agent/reviews/F1_QID_PAIRED_WRONG_AUTHORITY_LINEAGE_20260911.md` on this branch.

Status remains: `UNRESOLVED_HISTORICAL_AUTHORITY_GAP__NOT_PROVEN_ACTIVE_V5_TRAINER_BUG`.

The historical F1 QID implementation appears to alias `paired_wrong_similarity` to matched-null similarity. Current V5 trainer code reviewed so far did not consume QID directly, but all V5 qualification/evidence consumers still need full lineage audit.

## Claude's corrected role

Claude should review/red-team the branches above rather than rebuild them. Do not ask Claude to start the V5 pipeline or target-discovery framework from scratch.

Claude review targets:

1. `repair/t0-v21-authority-hardening-20260911`
2. `repair/v5-qualified-target-guard-20260911`
3. `review/integrated-target-v5-repairs-20260911`

Required verdict format: `PASS`, `PASS_WITH_MINOR_NOTES`, `MAJOR_REVISION`, or `NO_GO`, with exact file/function, failing invariant, minimal reproduction, and smallest safe repair for any blocker.
