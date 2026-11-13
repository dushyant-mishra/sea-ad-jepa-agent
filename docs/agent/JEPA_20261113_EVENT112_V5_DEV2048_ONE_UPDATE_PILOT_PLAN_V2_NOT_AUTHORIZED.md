# Event112 (part 2 of 2) — DEV2048 one-update V5 pilot plan, version 2 (PLAN ONLY — NOT AUTHORIZED)

**Date:** 2026-11-13.

**Author:** Macha.

**Supersedes:** Event111 part 2, where they differ. The changes are listed in section 6.

**Status:** design only. No forward, backward, optimizer step or EMA was run. Executing M1 needs a separate owner authorization record. The pilot tests **training mechanics on synthetic data**, not Alzheimer's biology.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## 1. Decisions the owner must make before M1

1. **Encoder input mode.** `SHARED_BASE_MASKED_BLOCK_JEPA` is the only implemented mode: both encoders get the same 2,044 base values, and q 1672–1675 are hidden from both. A teacher-only query mode (historical L04 EMERGENT/TRANSFER) is pending and not built. Choosing it would need new inputs and masks and a new review.
2. **EMA half-life.** The proposed value is 22,136 presentations, derived from the V4 contract's 0.996 per 128 cells.
3. **M1 authorization record.** It is defined in `verify_pilot_authorization`: milestone M1, horizon 1, the mode, rows, half-life, contract, FIT, premise and commit pins, plus owner, dates and expiry.

## 2. Exact pins

- **Code commit:** must contain #597 (the pre-flight) on top of #596/#594/#590–#593, as one pinned commit after independent review.
- **Contract:** `4536ce82f4dae6eaef94db24a5dc8bbcdcc62664105100e821e4ff8455cdd613`.
- **Data:** PR547 FIT ZIP `87fe3ec2…` (artifact 13364085153).
- **Governance file:** premise state blob `d8d6be5f2f1d4f7f50dfc2cc38b688deff9ef1f9`.
- **Model:** the PR224 35-file closure, verified on disk and as loaded (#594); config 2048/160/4/6/320, dropout 0.1, identity dim 48; init seed 8113002.
- **Optimizer:** AdamW, lr 1e-4 constant, betas (0.9, 0.999), eps 1e-8, weight decay 0.01, one group (student encoder, then predictor).
- **Batch:** rows 1, 3, 8, 10, 28, 32, 34, 35, 49, 54, 65, 74, 79, 81, 83, 90 (the first 16 SYNTH_A TRAIN rows); stable keys row + 11,000,000; one operator; 1,988 measured base addresses per cell.
- **Target blocks:** `sample_uniform_target_blocks`, seed 8813003, `sample_pass` 0, one view, mask fraction 0.40, 16 blocks, so about 795 genes are hidden per cell.
- **Execution environment:** CPU only, 1 thread, deterministic algorithms; WSL ext4 run directory; at most 30 minutes and 8 GiB.

## 3. Execution path (M1, exactly one update)

1. `build_shared_base_inputs` → `sample_m1_target_blocks` → `validate_target_blocks`. Leakage is refused here.
2. Connector u0 capture (exact seed rebuild, loaded-module check). The u0 is recorded only in the existing **u0-only** journal, which stays closed to updates.
3. Genesis authority: `capture_prefreeze_bound_checkpoint` → `ema_bound_runtime_proof_v1.issue_presentation_ema_bound_authority_from_checkpoint` (premise path, half-life).
4. `run_authorized_one_update`: authorization check, pairing and ownership check, then **one** call of `run_presentation_ema_bound_guarded_reference_update`. The route derives the momentum; no scalar momentum is passed.
5. Persist through **existing** PR224 code only: `bind_completed_checkpoint_to_presentation_ema` → `ema_persisted_continuation_v2.persist_presentation_ema_continuation_checkpoint`, into a directory that passes `require_separate_dev_checkpoint_path`.
6. Strict re-read of the persisted checkpoint; write the report.

## 4. M1 acceptance test (all must hold, or M1 fails)

**Runtime.**
- Optimizer step goes 0 → 1, exactly once.
- `guarded_ema` is true.
- The EMA equation check (`torch.equal`) passes.
- The gradient gate passes (no missing, non-finite or all-zero gradient).
- The teacher has no gradients.

**Recorded EMA facts.**

| Field | Required value |
|---|---|
| `ema_half_life_presentations` | the authorized half-life |
| `ema_presentations_this_update` | 16 |
| `ema_child_presentations_seen` | 16 |
| `ema_momentum_used` | `ema_momentum_for_presentations(16, H)` (0.99949912 at H = 22,136) |
| `presentation_ema_completion_proof` | present; its SHA-256 recorded |

**Predicted parameter changes.**
- Every student and predictor element moves by at most lr·(1 + wd·|θ|), opposite to its gradient.
- Adam `step` is 1 everywhere, and `exp_avg_sq = 0.1·exp_avg²` (real moments).
- The teacher's change equals (1 − m)·(student after − student before), at most about 5.1e-8 per element.
- The predictor is never used in the EMA.

**Inputs.**
- No q address appears in either packed input.
- Block members equal the hidden genes.
- Mode and rows match the authorization.

**Custody.**
- The checkpoint is persisted outside the u0-only journal and verifies on a strict re-read.
- The u0-only journal is unchanged.

**Not used as a criterion:** the direction of the loss. It is recorded only; a lower loss is not biology.

**Stop conditions.** Any failure of the above, a sentinel `CollapseStop`, a journal refusal, or a time or memory overrun aborts before persistence and records the failed attempt.

## 5. Restart test (separate milestone M2, separate authorization)

**Precondition:** M1 has passed and been reviewed.

**Runs.** Three updates on the next SYNTH_A TRAIN rows (16 per update, `sample_pass` = update index):

| Run | Description |
|---|---|
| C1, C2 | uninterrupted, in the same environment |
| R | interrupted after u1; a new process uses `load_presentation_ema_continuation_checkpoint` + `restore_and_issue_presentation_ema_continuation_authority`, then continues |
| R′ (optional) | process killed between `ATTEMPT_BEGIN` and commit, then journal recovery |

**A bitwise restart claim needs C1 ≡ C2 first.** It then requires, for R versus C1 at u2 and u3:
- every online, teacher and predictor tensor `torch.equal`;
- named AdamW state (step, `exp_avg`, `exp_avg_sq`) bit-for-bit, and param groups equal;
- cursors, presentations and each EMA momentum equal as floats;
- per-update loss, gradient maximum, microbatch plan and hidden-mask SHA-256 equal;
- global RNG state bytes equal;
- one canonical tensor digest equal.

**Not compared:** file bytes, timestamps and session IDs.

**Negative controls**, which must each be detected: a one-ULP change, `presentations + 1`, and an off-by-one batch.

**What a pass supports:** this environment, these three updates, DEV2048 only.

## 6. Changes from Event111 part 2

- The teacher receives the **shared q-excluded base**, not 2,048 addresses. The contract is corrected, and the teacher-only query mode is an open owner decision.
- An explicit pre-route **target-leakage refusal** is added; the pinned runtime does not provide one.
- The pilot is bound to the presentation-EMA route, with pairing, ownership and recorded-field checks implemented in #597.
- Lineage is checked statically: no V4 trainer, legacy EMA or toy actor is called.
