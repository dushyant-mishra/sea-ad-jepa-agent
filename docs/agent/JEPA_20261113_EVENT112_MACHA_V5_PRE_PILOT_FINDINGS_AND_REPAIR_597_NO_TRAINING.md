# Event112 (part 1 of 2) — Macha V5 pre-pilot findings and repair draft #597 (NO TRAINING)

**Date:** 2026-11-13.

**Author:** Macha.

**Branches:** append-only on #322, mirrored on #460. Events 1–111 are unchanged; the #595 verdict stays as recorded in Event111.

**Scope:**
- contract, static and mock checks only;
- PR224 V5 modules constructed only for the pairing check;
- guard tests use a hook-faithful fake optimizer and recording parameter stand-ins;
- no forward, backward, optimizer step, EMA update, GPU, real data or merge.

The pilot was not launched.

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Newer-entry check

Before work started, #322 was at Event111 (`dac5b1c2`), #595 at `37dc2469` and #596 at `bc9da054`. Nothing newer existed, so the #595 verdict (REPAIR_REQUIRED, scoped; repaired in #596) stands as recorded.

## Findings

1. **The teacher-input contract was wrong; the code was right.**
   - **What the code does:** the PR548 adapter parses only the q-excluded student member and only hashes `teacher_measured.npz`. The forward probe asserts that neither encoder's packed input contains 1672–1675. So both encoders receive the same 2,044 base values.
   - **What the contract said:** `teacher_address_ids` = all 2,048 addresses, mixing up the vocabulary with the values supplied. A request claiming the teacher receives q values was accepted.
   - **Repaired in #597:**
     - `vocabulary_address_ids` (2,048) is a separate field;
     - teacher and student address IDs are both the 2,044 base addresses;
     - `encoder_input_mode = SHARED_BASE_MASKED_BLOCK_JEPA`;
     - a V2 gene-axis binding covers all of these;
     - contract `4536ce82…`.
   - **The teacher-only query mode is an open owner decision.** The historical record (`L04_OWNER_DECISION_PENDING__NO_IMPLICIT_SHARED_Q_DESCENDANT_TO_C3`; "L04 EMERGENT/TRANSFER") settles that the decision is pending, not what it should be. It is recorded as not implemented.

2. **Target leakage gap in the pinned runtime.** `run_inactive_reference_update` checks only that hidden genes are measured. A characterization test shows a block member moved to a still-visible gene passes its checks and reaches the teacher forward (a fake that raises immediately). The #597 pre-flight refuses this before the route is called; the members must equal the hidden genes, each once, measured, with no q.

3. **EMA route and pairing.**
   - **Already correct in the pinned PR224 guard (mocks):** a failed or skipped optimizer step never permits EMA; a successful step permits exactly one; and the wrapper pairs each teacher tensor with the post-step student encoder, never the predictor.
   - **Added in #597:**
     - only `run_presentation_ema_bound_guarded_reference_update` is accepted (the scalar-momentum routes are refused);
     - a pairing and ownership validator: same names, order, shapes and dtypes; teacher frozen; AdamW owns exactly the student encoder and predictor;
     - a recorded update record: half-life, base cells, parent and child presentations, derived momentum, step 0 → 1, completion-proof SHA-256.

4. **Lineage and checkpoint boundaries.**
   - **The chain (AST):** pilot → EMA-bound route → guarded wrapper → reference update → `KeyedIPBEncoderV2Reference` + `BlockPredictor`.
   - **V4 components used:** `ipb_jepa`, `gene_tokenizer`, `contracts`, `masking`, and `teacher_student_runtime.sample_uniform_target_blocks` only.
   - **Not called:** the V4 trainer, legacy V4 EMA and toy actor (they are loaded by the V4 package `__init__`, not called).
   - **Checkpoints:** the u0-only journal is unchanged; a dev checkpoint path inside it is refused.
   - **Authorization:** the driver requires an owner M1 authorization record. None exists.

## Evidence for #597 (RED `0ab2b1d7` → GREEN `bfcba24e`)

**Hosted RED (Python 3.11.9 and 3.12.7):**

| Run | Result (per Python) |
|---|---|
| 43509850943 | 4 failed (3 contract tests + 1 new-API route test), 6 characterization tests passed |
| 43509850768 | 3 failed (contract), 480 passed, 37 skipped |

**Hosted GREEN:** 7/7 workflows, 14/14 jobs.

| Run | Result (per Python) |
|---|---|
| 43510149310 | 40 passed; inventory 43 files verified |
| 43510149246 | 513 passed, 37 skipped; contract `4536ce82…` verified |
| 43510149267 | 74 + 56 passed |

**Local GREEN:** full no-step inventory via the reviewed runner, 541 passed, 9 skipped.

**Limits:** the validator guards the pilot driver, not the pinned runtime itself; an indirectly called helper is not certified.
