# Audit-B N1 independent end-to-end execution review — 2026-09-22

Status: `STOP_N1_EXECUTION__END_TO_END_EXECUTOR_NOT_YET_FROZEN`

Parent reviewed: PR #50 head `e4b7e9f46842d66cd7db71b1df9de60fc037f971`.

## Scope

Independent static review of the N1 implementation before any Audit-B masking computation. No N1 target was executed; no masks, burden, terminal masking, protected outcomes, TD60, D_shared/G5, pathology/DEV/SEALED or training outcomes were opened.

Historical mechanics were not re-audited unless needed to determine current N1 executable completeness.

## What is genuinely closed at PR #50

The following pre-outcome components are implemented and CI-green:

- `audit_b_n1_execution_authority_v1.py`: binds N1=256 to the B4 contract and verified B4 runtime-preflight source; cannot directly authorize N2, terminal masking or training.
- `audit_b_n1_runtime_rng_bridge_v1.py`: prospectively freezes the runtime RNG composition and target identity rule.
- `audit_b_n1_cached_planner_v1.py`: caches fold-specific partner discovery and reuses it across burden rungs.
- `audit_b_n1_crossfold_planner_v1.py`: two-pass all-fold partner discovery; all partner fitting uses donors with `fold_by_donor != heldout_fold`.
- `audit_b_n1_result_contract_v1.py`: requires exact 256-target x 3-policy x 6-rung x 104-donor tensors and preserves source-balanced, donor-uniform and source-specific recomputability.
- N1 primary precision decision is limited to the frozen RIDGE8_CONDITIONAL at 5% burden cell.
- N2 can be authorized only by an explicit receipt after N1 precision failure; the receipt cannot jump to N3 or authorize terminal masking/training.

Hosted PR #50 workflows were green, including the fail-on-skips masking workflow.

## Blocking finding

There is **no end-to-end N1 execution CLI/executor in PR #50** that:

1. loads and verifies the frozen N1 execution authority and all physical input receipts;
2. iterates the exact frozen 256-target panel;
3. uses the reviewed cross-fold/cached planner for all four folds;
4. streams authenticated FULL104 data without held-out leakage;
5. computes the frozen production burden for all 3 nonuniform policies x 6 rungs x 104 donors;
6. writes the exact `AuditBN1ResultReceiptV1` artifact atomically;
7. supports deterministic crash-safe resume without duplicate/partial target consumption;
8. freezes the result before the precision decision is opened.

The existing builder script builds the N1 **authority**, not the N1 result. The current workflow verifies component contracts and parity tests; it does not test a real or synthetic end-to-end N1 execution command.

Therefore:

`N1_COMPONENTS_GREEN != N1_EXECUTOR_QUALIFIED`

and the B4 preflight state `READY_FOR_AUDIT_B_N1_EXECUTION` must not be interpreted as permission to execute until the missing end-to-end executor is implemented, tested and source-bound prospectively.

## Additional review observations

- Cross-fold partner discovery excludes the held-out outer fold in both the cached foldwise path and the two-pass all-fold path.
- The two-pass path computes donor-local sufficient statistics for all donors, then forms training-fold aggregates only from training donors. This is computational reuse, not by itself held-out fitting leakage.
- The result contract fails closed on target order drift, non-finite burden values, donor/source geometry drift and scope expansion.
- The precision receipt and N2 escalation logic are appropriately downstream of the frozen N1 result hash.
- No direct authority exists here for N3, terminal policy selection or training.

## Required repair before N1

Build a distinct N1 execution successor that is prospectively bound to:

- PR #50 N1 authority digest;
- B4 contract and B4 runtime-preflight receipt;
- RNG-V3/runtime bridge;
- exact frozen N1 target list and order;
- authenticated Level-4 manifest and source hashes;
- exact outer split;
- current production burden implementation;
- crossfold/cached planner source hashes;
- atomic result schema + exactly-once target/fold/rung bookkeeping.

Minimum tests should include:

- synthetic end-to-end equality against the frozen foldwise reference;
- deliberate held-out-donor perturbation that cannot change fitted partners for that fold;
- exact restart/resume replay with byte-identical final result;
- duplicate target and partial target rejection;
- source/donor/fold coverage completeness;
- result-receipt tamper rejection;
- no N2 decision before immutable N1 result receipt exists;
- fail-on-skipped tests.

## Outcome firewall

`AUDIT_B_N1=UNOPENED; MASKS_EXECUTED=NONE; BURDEN_CALCULATION=NOT_RUN; TERMINAL_MASKING=UNOPENED; RARE_TAIL_MOLECULAR=UNOPENED; TD60=UNEXECUTED; PATHOLOGY_DEV_SEALED=UNOPENED; D_SHARED_G5=UNOPENED; TRAINING=OFF`.
